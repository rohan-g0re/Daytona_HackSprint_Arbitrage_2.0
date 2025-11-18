"""
Test price optimization feedback loop logging to Galileo.

WHAT: Verify price adjustments appear in Galileo dashboard
WHY: User needs to see feedback loop in action
HOW: Create mock data and test logging
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.services.galileo_service import galileo_feedback_service


def test_price_optimization_logging():
    """Test that price optimization traces appear in dashboard."""
    print("="*60)
    print("PRICE OPTIMIZATION LOGGING TEST")
    print("="*60)
    
    if not galileo_feedback_service.is_enabled():
        print("\n[ERROR] Galileo is not enabled!")
        print("Fix: Set GALILEO_ENABLED=true in .env")
        return False
    
    print("\n[OK] Galileo is enabled")
    
    try:
        session_id = "test_price_opt_session"
        
        # Start session
        print("\n[1/5] Starting session...")
        galileo_feedback_service.start_session(
            session_id=f"session_{session_id}",
            metadata={"test": "price_optimization", "session_id": session_id}
        )
        print(f"  [OK] Session started")
        
        # Add main analysis trace
        print("\n[2/5] Adding price optimization analysis trace...")
        trace_id = galileo_feedback_service.add_trace(
            name="price_optimization_analysis",
            input_text=f"Price optimization analysis for session {session_id} (2 completed deals)",
            output_text="",  # Will be updated
            metadata={
                "session_id": session_id,
                "outcomes_count": "2",
                "analysis_type": "price_optimization"
            }
        )
        print(f"  [OK] Analysis trace added: {trace_id}")
        
        # Add adjustment spans
        print("\n[3/5] Adding price adjustment spans...")
        
        # Adjustment 1: TechStore A lost, needs to lower price
        span_id_1 = galileo_feedback_service.add_span(
            name="adjust_techstore_a_laptop",
            input_text="Analyze TechStore A pricing for Gaming Laptop",
            output_text="Suggested: $1150.00 -> $980.00 (-14.78%)",
            metadata={
                "seller_id": "techstore_a",
                "item_name": "Gaming Laptop",
                "current_least_price": "1150.0",
                "suggested_least_price": "980.0",
                "reduction_pct": "-14.78",
                "won_deal": "False",
                "final_deal_price": "950.0"
            },
            span_type="workflow"
        )
        print(f"  [OK] Adjustment span 1: {span_id_1}")
        
        # Adjustment 2: TechStore C lost, needs to lower price
        span_id_2 = galileo_feedback_service.add_span(
            name="adjust_techstore_c_laptop",
            input_text="Analyze TechStore C pricing for Gaming Laptop",
            output_text="Suggested: $1000.00 -> $950.00 (-5.00%)",
            metadata={
                "seller_id": "techstore_c",
                "item_name": "Gaming Laptop",
                "current_least_price": "1000.0",
                "suggested_least_price": "950.0",
                "reduction_pct": "-5.0",
                "won_deal": "False",
                "final_deal_price": "950.0"
            },
            span_type="workflow"
        )
        print(f"  [OK] Adjustment span 2: {span_id_2}")
        
        # Conclude the first trace (required before adding another)
        print("\n[4/6] Concluding first trace...")
        if hasattr(galileo_feedback_service.galileo_logger, 'conclude'):
            galileo_feedback_service.galileo_logger.conclude()
            print("  [OK] First trace concluded")
        
        # Add summary trace
        print("\n[5/6] Adding summary trace...")
        summary_output = """Suggested 2 price adjustments:
Gaming Laptop: $1150.00 -> $980.00 (-14.78%)
Gaming Laptop: $1000.00 -> $950.00 (-5.00%)"""
        
        summary_id = galileo_feedback_service.add_trace(
            name="price_optimization_summary",
            input_text=f"Session {session_id}: Analyzed 2 negotiations",
            output_text=summary_output,
            metadata={
                "session_id": session_id,
                "adjustments_made": "2",
                "deals_analyzed": "2",
                "has_adjustments": "True"
            }
        )
        print(f"  [OK] Summary trace added: {summary_id}")
        
        # Flush
        print("\n[6/6] Flushing logger...")
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
        print(f"  - Session: session_{session_id}")
        print("  - Trace: price_optimization_analysis")
        print("  - Trace: price_optimization_summary")
        print("  - Spans: adjust_techstore_a_laptop, adjust_techstore_c_laptop")
        print("\nThe summary trace should show:")
        print("  - Input: Session analysis details")
        print("  - Output: List of all price adjustments")
        print("\nEach span should show:")
        print("  - Input: Which seller/item is being analyzed")
        print("  - Output: Old price -> New price (% reduction)")
        print("  - Metadata: Full details of the adjustment")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_price_optimization_logging()
    sys.exit(0 if success else 1)

