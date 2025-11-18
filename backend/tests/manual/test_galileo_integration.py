"""
Test Galileo integration - verify logs appear in dashboard.

WHAT: Simple test to verify Galileo logging works
WHY: Ensure API key and configuration are correct
HOW: Create a simple trace and check for errors

Usage:
    1. Set GALILEO_ENABLED=true and GALILEO_API_KEY in .env
    2. Run: python tests/manual/test_galileo_integration.py
    3. Check Galileo console: https://app.galileo.ai
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.galileo_service import galileo_feedback_service


def test_galileo_connection():
    """Test basic Galileo connection and logging."""
    print("\n" + "="*60)
    print("GALILEO INTEGRATION TEST")
    print("="*60 + "\n")
    
    # Check if Galileo is enabled
    if not galileo_feedback_service.is_enabled():
        print("❌ Galileo is NOT enabled!")
        print("\nPossible reasons:")
        print("  1. GALILEO_ENABLED=false in .env")
        print("  2. GALILEO_API_KEY not set in .env")
        print("  3. Galileo SDK not installed (run: pip install galileo)")
        print("\nFix: Update your .env file and restart.")
        return False
    
    print("✅ Galileo is enabled and initialized!\n")
    
    # Try to create a test session and trace
    try:
        print("📝 Creating test session and trace...")
        
        test_session_id = "test_session_001"
        test_metadata = {
            "test_type": "integration_test",
            "purpose": "verify_galileo_logging"
        }
        
        # Create a test session with a trace
        with galileo_feedback_service.session(test_session_id, test_metadata):
            print("  ✓ Session created")
            
            # Create a test trace
            with galileo_feedback_service.trace(
                name="test_negotiation",
                input_text="Test negotiation for laptop",
                metadata={"item": "laptop", "quantity": 1}
            ) as trace:
                print("  ✓ Trace created")
                
                # Create test spans
                with galileo_feedback_service.span(
                    name="buyer_message",
                    input_text="What's your best price?",
                    metadata={"role": "buyer"}
                ) as buyer_span:
                    print("  ✓ Buyer span created")
                    if buyer_span and hasattr(buyer_span, 'set_output'):
                        buyer_span.set_output("Asking for price")
                
                with galileo_feedback_service.span(
                    name="seller_response",
                    input_text="I can offer $950",
                    metadata={"role": "seller", "price": 950}
                ) as seller_span:
                    print("  ✓ Seller span created")
                    if seller_span and hasattr(seller_span, 'set_output'):
                        seller_span.set_output("Offer: $950")
                
                # Set trace output
                if trace and hasattr(trace, 'set_output'):
                    trace.set_output("Test completed - Deal at $950")
                    print("  ✓ Trace output set")
        
        # Flush to ensure data is sent
        if hasattr(galileo_feedback_service.galileo_logger, 'flush'):
            galileo_feedback_service.galileo_logger.flush()
            print("  ✓ Logger flushed")
        
        print("\n✅ Test trace created successfully!")
        print("\n" + "="*60)
        print("CHECK YOUR GALILEO DASHBOARD")
        print("="*60)
        print("\n🔗 Go to: https://app.galileo.ai")
        print("📁 Project: Arbritrage")
        print("📝 Log Stream: default")
        print("\nYou should see:")
        print("  • Session: test_session_001")
        print("  • Trace: test_negotiation")
        print("  • Spans: buyer_message, seller_response")
        print("\n" + "="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating test trace: {e}")
        print(f"\nException type: {type(e).__name__}")
        import traceback
        print("\nFull traceback:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_galileo_connection()
    
    if success:
        print("✅ SUCCESS: Galileo integration is working!")
        sys.exit(0)
    else:
        print("❌ FAILED: Galileo integration is not working")
        print("\nTroubleshooting steps:")
        print("1. Check your .env file has GALILEO_ENABLED=true")
        print("2. Verify GALILEO_API_KEY is set correctly")
        print("3. Ensure galileo SDK is installed: pip install galileo")
        print("4. Check backend logs for error messages")
        sys.exit(1)

