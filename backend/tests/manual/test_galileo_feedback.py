"""
Test script for Galileo integration and price feedback loop.

WHAT: End-to-end test of Galileo observability and price optimization feedback
WHY: Verify the feedback loop works correctly after negotiations complete
HOW: Create session → run negotiations → generate summaries → verify feedback loop
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import init_db, Base, engine, get_db
from app.core.session_manager import SessionManager
from app.core.models import (
    Session, Buyer, BuyerItem, Seller, SellerInventory,
    NegotiationRun, NegotiationParticipant, Message, Offer, NegotiationOutcome
)
from app.services.galileo_service import galileo_feedback_service
from app.services.price_feedback_service import price_feedback_service
from app.services.ai_summary_service import ai_summary_service
from app.models.api_schemas import (
    InitializeSessionRequest, BuyerConfig, ShoppingItem,
    SellerConfig, InventoryItem, SellerProfile, LLMConfig
)
from app.core.config import settings


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_step(step_num, description):
    """Print a step header."""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 80)


def check_galileo_setup():
    """Check if Galileo is properly configured."""
    print_section("Galileo Configuration Check")
    
    print(f"GALILEO_ENABLED: {settings.GALILEO_ENABLED}")
    print(f"GALILEO_API_KEY: {'***' + settings.GALILEO_API_KEY[-4:] if settings.GALILEO_API_KEY else 'NOT SET'}")
    print(f"GALILEO_PROJECT: {settings.GALILEO_PROJECT}")
    print(f"GALILEO_LOG_STREAM: {settings.GALILEO_LOG_STREAM}")
    
    if not settings.GALILEO_ENABLED:
        print("\n⚠️  WARNING: Galileo is disabled. Set GALILEO_ENABLED=true in .env")
        return False
    
    if not settings.GALILEO_API_KEY:
        print("\n⚠️  WARNING: GALILEO_API_KEY not set. Get your key from:")
        print("   https://app.galileo.ai/settings/api-keys")
        return False
    
    # Check if service initialized
    if galileo_feedback_service.is_enabled():
        print("\n✅ Galileo service is initialized and ready!")
        return True
    else:
        print("\n⚠️  WARNING: Galileo service failed to initialize")
        print("   Check your API key and network connection")
        return False


async def create_test_session():
    """Create a test session with negotiations."""
    print_section("Creating Test Session")
    
    manager = SessionManager()
    
    # Create session with 1 buyer, 3 sellers, 1 item
    request = InitializeSessionRequest(
        buyer=BuyerConfig(
            name="Test Buyer",
            shopping_list=[
                ShoppingItem(
                    item_id="laptop",
                    item_name="Gaming Laptop",
                    quantity_needed=1,
                    min_price_per_unit=800.0,
                    max_price_per_unit=1200.0
                )
            ]
        ),
        sellers=[
            SellerConfig(
                name="TechStore A",
                inventory=[
                    InventoryItem(
                        item_id="laptop",
                        item_name="Gaming Laptop",
                        cost_price=700.0,
                        selling_price=1300.0,
                        least_price=1150.0,  # High least price - will likely lose
                        quantity_available=5
                    )
                ],
                profile=SellerProfile(
                    priority="maximize_profit",
                    speaking_style="very_sweet"
                )
            ),
            SellerConfig(
                name="TechStore B",
                inventory=[
                    InventoryItem(
                        item_id="laptop",
                        item_name="Gaming Laptop",
                        cost_price=750.0,
                        selling_price=1250.0,
                        least_price=950.0,  # Lower least price - will likely win
                        quantity_available=5
                    )
                ],
                profile=SellerProfile(
                    priority="customer_retention",
                    speaking_style="very_sweet"
                )
            ),
            SellerConfig(
                name="TechStore C",
                inventory=[
                    InventoryItem(
                        item_id="laptop",
                        item_name="Gaming Laptop",
                        cost_price=800.0,
                        selling_price=1350.0,
                        least_price=1000.0,  # Medium least price
                        quantity_available=5
                    )
                ],
                profile=SellerProfile(
                    priority="maximize_profit",
                    speaking_style="very_sweet"
                )
            )
        ],
        llm_config=LLMConfig(
            provider="openrouter",
            model="google/gemini-2.5-flash-lite"
        )
    )
    
    response = manager.create_session(request)
    session_id = response.session_id
    
    print(f"✅ Session created: {session_id}")
    print(f"   Buyer: {response.buyer_id}")
    print(f"   Sellers: {len(response.seller_ids)}")
    print(f"   Rooms: {len(response.negotiation_rooms)}")
    
    return session_id, response, manager


async def simulate_negotiation(session_id, response, manager):
    """Simulate a negotiation with messages and offers."""
    print_section("Simulating Negotiation")
    
    room = response.negotiation_rooms[0]
    run_id = room.room_id
    
    # Start negotiation
    run_info = manager.start_negotiation(run_id)
    print(f"✅ Started negotiation: {run_id}")
    
    # Record messages
    messages = []
    for turn in range(1, 6):
        if turn % 2 == 1:
            # Buyer message
            msg = manager.record_message(
                run_id=run_id,
                turn_number=turn,
                sender_type="buyer",
                sender_id=response.buyer_id,
                sender_name="Test Buyer",
                message_text=f"Round {turn}: I'm looking for a good deal on a gaming laptop.",
                mentioned_agents=None
            )
        else:
            # Seller messages (all sellers respond)
            for seller_id in response.seller_ids:
                msg = manager.record_message(
                    run_id=run_id,
                    turn_number=turn,
                    sender_type="seller",
                    sender_id=seller_id,
                    sender_name=next(s.seller_name for s in response.negotiation_rooms[0].participating_sellers if s.seller_id == seller_id),
                    message_text=f"Round {turn}: I can offer you a great price!",
                    mentioned_agents=None
                )
                messages.append(msg)
        messages.append(msg)
    
    print(f"✅ Recorded {len(messages)} messages")
    
    # Record offers with decreasing prices
    offers = []
    with get_db() as db:
        from app.core.models import SellerInventory
        seller_inventories = {}
        for seller_id in response.seller_ids:
            inventory = db.query(SellerInventory).filter(
                SellerInventory.seller_id == seller_id,
                SellerInventory.item_name == "Gaming Laptop"
            ).first()
            if inventory:
                seller_inventories[seller_id] = inventory
        
        # Seller B offers lowest price (will win)
        for i, seller_id in enumerate(response.seller_ids):
            seller_name = next(s.seller_name for s in response.negotiation_rooms[0].participating_sellers if s.seller_id == seller_id)
            inventory = seller_inventories.get(seller_id)
            
            if inventory:
                # Seller B offers below their least_price to win
                if "B" in seller_name:
                    offer_price = 980.0  # Below least_price of 950, but close
                elif "A" in seller_name:
                    offer_price = 1180.0  # Close to least_price of 1150
                else:
                    offer_price = 1050.0  # Close to least_price of 1000
                
                # Find a seller message
                seller_msg = next((m for m in messages if m.sender_id == seller_id), None)
                if seller_msg:
                    offer = manager.record_offer(
                        message_id=seller_msg.id,
                        seller_id=seller_id,
                        price_per_unit=offer_price,
                        quantity=1
                    )
                    offers.append(offer)
                    print(f"   {seller_name}: ${offer_price:.2f} (least_price: ${inventory.least_price:.2f})")
    
    print(f"✅ Recorded {len(offers)} offers")
    
    # Finalize with Seller B winning
    seller_b_id = next(s.seller_id for s in response.negotiation_rooms[0].participating_sellers if "B" in s.seller_name)
    outcome = manager.finalize_run(
        run_id=run_id,
        decision_type="deal",
        selected_seller_id=seller_b_id,
        final_price_per_unit=980.0,
        quantity=1,
        decision_reason="Best price offered"
    )
    
    print(f"✅ Negotiation finalized: Seller B won at $980.00")
    
    return session_id, run_id


async def test_galileo_logging(session_id, run_id):
    """Test Galileo trace logging."""
    print_section("Testing Galileo Trace Logging")
    
    if not galileo_feedback_service.is_enabled():
        print("⚠️  Skipping: Galileo not enabled")
        return
    
    try:
        with get_db() as db:
            await galileo_feedback_service.log_negotiation_trace(
                db=db,
                run_id=run_id,
                session_id=session_id
            )
        print("✅ Successfully logged negotiation trace to Galileo")
        print("   Check your Galileo dashboard to see the trace")
    except Exception as e:
        print(f"❌ Failed to log trace: {e}")
        import traceback
        traceback.print_exc()


async def test_feedback_loop(session_id):
    """Test the price feedback loop."""
    print_section("Testing Price Feedback Loop")
    
    if not galileo_feedback_service.is_enabled():
        print("⚠️  Skipping: Galileo not enabled")
        return
    
    # Generate AI summaries first (simplified for testing)
    print("\n[1/3] Generating AI summaries...")
    ai_summaries = {
        "overall": {
            "performance_insights": "Buyer successfully negotiated a good deal",
            "cross_item_comparison": "Seller B was most competitive",
            "recommendations": ["Sellers should lower prices to be more competitive"]
        }
    }
    
    # Get run summaries
    with get_db() as db:
        runs = db.query(NegotiationRun).filter(
            NegotiationRun.session_id == session_id
        ).all()
        
        for run in runs:
            try:
                summary_data = await ai_summary_service.generate_item_summary(db, run.id)
                if summary_data:
                    ai_summaries[run.id] = summary_data
            except Exception as e:
                print(f"   Warning: Could not generate summary for {run.id}: {e}")
    
    print(f"✅ Generated {len(ai_summaries)} summaries")
    
    # Test price optimization analysis
    print("\n[2/3] Analyzing price optimization opportunities...")
    with get_db() as db:
        price_adjustments = await galileo_feedback_service.analyze_price_optimization(
            db=db,
            session_id=session_id,
            ai_summary=ai_summaries.get("overall", {})
        )
    
    print(f"✅ Found {len(price_adjustments)} price adjustment opportunities")
    for key, new_price in price_adjustments.items():
        seller_id, item_id = key.split("_", 1)
        print(f"   {seller_id}: ${new_price:.2f}")
    
    # Apply feedback
    print("\n[3/3] Applying price adjustments...")
    with get_db() as db:
        # Get initial prices
        from app.core.models import SellerInventory
        initial_prices = {}
        inventories = db.query(SellerInventory).join(Seller).filter(
            Seller.session_id == session_id
        ).all()
        
        for inv in inventories:
            initial_prices[inv.id] = inv.least_price
            print(f"   Initial: {inv.item_name} - Seller {inv.seller_id[:8]}... = ${inv.least_price:.2f}")
        
        # Apply feedback
        result = await price_feedback_service.apply_feedback_after_summary(
            db=db,
            session_id=session_id,
            ai_summaries=ai_summaries
        )
        
        print(f"\n✅ Feedback loop completed:")
        print(f"   Adjustments applied: {result.get('adjustments_applied', 0)}")
        
        if result.get('adjustments'):
            print("\n   Price Adjustments:")
            for adj in result['adjustments']:
                print(f"   - {adj['item_name']} (Seller {adj['seller_id'][:8]}...):")
                print(f"     ${adj['old_least_price']:.2f} → ${adj['new_least_price']:.2f}")
                print(f"     Reduction: {adj['reduction_pct']:.1f}%")
        else:
            print("   No adjustments were made (may be expected if prices are already optimal)")
        
        # Verify prices changed - refresh objects from database
        db.expire_all()  # Expire all objects to force reload
        print("\n   Final Prices:")
        for inv in inventories:
            db.refresh(inv)  # Refresh individual object
            final_price = inv.least_price
            initial_price = initial_prices.get(inv.id, final_price)
            if final_price != initial_price:
                print(f"   ✅ {inv.item_name} - Seller {inv.seller_id[:8]}...: ${initial_price:.2f} → ${final_price:.2f}")
            else:
                print(f"   - {inv.item_name} - Seller {inv.seller_id[:8]}...: ${final_price:.2f} (unchanged)")


async def main():
    """Run the complete test."""
    print_section("Galileo Integration & Feedback Loop Test")
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Step 1: Check Galileo setup
    if not check_galileo_setup():
        print("\n⚠️  Galileo is not properly configured.")
        print("   The test will continue but Galileo features will be disabled.")
        print("   To enable:")
        print("   1. Set GALILEO_ENABLED=true in .env")
        print("   2. Set GALILEO_API_KEY=your-key in .env")
        print("   3. Install: pip install 'galileo[openai]' python-dotenv")
    
    # Step 2: Initialize database
    print_step(2, "Initializing Database")
    Base.metadata.drop_all(bind=engine)
    init_db()
    print("✅ Database initialized")
    
    # Step 3: Create test session
    session_id, response, manager = await create_test_session()
    
    # Step 4: Simulate negotiation
    session_id, run_id = await simulate_negotiation(session_id, response, manager)
    
    # Step 5: Test Galileo logging
    await test_galileo_logging(session_id, run_id)
    
    # Step 6: Test feedback loop
    await test_feedback_loop(session_id)
    
    print_section("Test Complete")
    print(f"Finished at: {datetime.now().isoformat()}")
    print("\n✅ All tests completed!")
    print("\nNext steps:")
    print("1. Check your Galileo dashboard for logged traces")
    print("2. Verify price adjustments were applied correctly")
    print("3. Run another negotiation to see cumulative improvements")


if __name__ == "__main__":
    asyncio.run(main())

