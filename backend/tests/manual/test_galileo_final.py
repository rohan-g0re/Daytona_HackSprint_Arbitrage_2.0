"""
Final Galileo test using the correct SDK methods.

WHAT: Test the updated galileo_service with correct API
WHY: Verify logs now appear in the dashboard
HOW: Use add_trace and add_span methods
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.services.galileo_service import galileo_feedback_service


def test_galileo_logging():
    """Test Galileo logging with the corrected API."""
    print("="*60)
    print("GALILEO FINAL TEST")
    print("="*60)
    
    if not galileo_feedback_service.is_enabled():
        print("\n[ERROR] Galileo is not enabled!")
        print("Fix: Set GALILEO_ENABLED=true in .env")
        return False
    
    print("\n[OK] Galileo is enabled")
    
    try:
        # Start a session
        print("\n[1/4] Starting session...")
        session_id = "test_final_session"
        galileo_feedback_service.start_session(
            session_id=session_id,
            metadata={"test": "final", "purpose": "verify_logging"}
        )
        print(f"  [OK] Session started: {session_id}")
        
        # Add a trace
        print("\n[2/4] Adding trace...")
        trace_input = "Negotiate for Gaming Laptop"
        trace_output = "Deal: $950/unit with TechStore B"
        trace_metadata = {
            "item_name": "Gaming Laptop",
            "quantity": 1,
            "rounds": 3,
            "status": "completed"
        }
        
        trace_id = galileo_feedback_service.add_trace(
            name="negotiate_Gaming_Laptop",
            input_text=trace_input,
            output_text=trace_output,
            metadata=trace_metadata
        )
        print(f"  [OK] Trace added: {trace_id}")
        
        # Add spans
        print("\n[3/4] Adding spans...")
        
        # Buyer span
        buyer_span_id = galileo_feedback_service.add_span(
            name="round_1_buyer",
            input_text="I'm looking for a gaming laptop under $1000",
            metadata={"round": 1, "sender": "buyer", "role": "buyer"},
            span_type="agent"
        )
        print(f"  [OK] Buyer span added: {buyer_span_id}")
        
        # Seller span  
        seller_span_id = galileo_feedback_service.add_span(
            name="round_1_seller_TechStoreB",
            input_text="I can offer you a great gaming laptop at $980",
            output_text="Offer: $980/unit (qty: 1)",
            metadata={"round": 1, "sender": "TechStore B", "role": "seller", "offer_price": 980},
            span_type="agent"
        )
        print(f"  [OK] Seller span added: {seller_span_id}")
        
        # Flush
        print("\n[4/4] Flushing logger...")
        if hasattr(galileo_feedback_service.galileo_logger, 'flush'):
            galileo_feedback_service.galileo_logger.flush()
            print("  [OK] Logger flushed")
        
        # End session
        galileo_feedback_service.end_session()
        print("  [OK] Session ended")
        
        # Success message
        print("\n" + "="*60)
        print("TEST COMPLETE - SUCCESS!")
        print("="*60)
        print("\nCheck your Galileo dashboard:")
        print("  URL: https://app.galileo.ai")
        print(f"  Project: {os.getenv('GALILEO_PROJECT', 'Arbritrage')}")
        print(f"  Log Stream: {os.getenv('GALILEO_LOG_STREAM', 'default')}")
        print("\nYou should see:")
        print(f"  - Session: {session_id}")
        print("  - Trace: negotiate_Gaming_Laptop")
        print("  - Spans: round_1_buyer, round_1_seller_TechStoreB")
        print("\nIf you don't see logs:")
        print("  1. Wait 10-30 seconds and refresh")
        print("  2. Check Network tab in browser (any errors?)")
        print("  3. Verify project name matches in dashboard")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_galileo_logging()
    sys.exit(0 if success else 1)

