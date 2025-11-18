"""
Windows-compatible Galileo test (no Unicode characters).

WHAT: Test Galileo logging without emoji characters
WHY: Windows console doesn't support Unicode properly
HOW: Use ASCII-only output
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()


def test_basic():
    """Test basic Galileo functionality."""
    print("="*60)
    print("GALILEO WINDOWS TEST")
    print("="*60)
    
    # Check environment
    print("\n[1/5] Checking environment...")
    api_key = os.getenv('GALILEO_API_KEY')
    enabled = os.getenv('GALILEO_ENABLED', 'false').lower() == 'true'
    project = os.getenv('GALILEO_PROJECT', 'Arbritrage')
    log_stream = os.getenv('GALILEO_LOG_STREAM', 'default')
    
    print(f"  GALILEO_ENABLED: {enabled}")
    print(f"  GALILEO_API_KEY: {'***' + api_key[-4:] if api_key and len(api_key) > 4 else 'NOT SET'}")
    print(f"  GALILEO_PROJECT: {project}")
    print(f"  GALILEO_LOG_STREAM: {log_stream}")
    
    if not enabled:
        print("\n[ERROR] GALILEO_ENABLED is not true!")
        print("  Fix: Add to .env file: GALILEO_ENABLED=true")
        return False
    
    if not api_key:
        print("\n[ERROR] GALILEO_API_KEY is not set!")
        print("  Fix: Add to .env file: GALILEO_API_KEY=gal_your_key")
        print("  Get key from: https://app.galileo.ai")
        return False
    
    print("  [OK] Environment configured")
    
    # Test import
    print("\n[2/5] Importing Galileo SDK...")
    try:
        from galileo import GalileoLogger
        from galileo.config import GalileoPythonConfig
        print("  [OK] SDK imported")
    except ImportError as e:
        print(f"  [ERROR] Failed to import: {e}")
        return False
    
    # Initialize logger
    print("\n[3/5] Initializing GalileoLogger...")
    try:
        logger = GalileoLogger(
            project=project,
            log_stream=log_stream
        )
        print("  [OK] Logger initialized")
        print(f"  Logger object: {logger}")
        
        # Check available methods
        methods = [m for m in dir(logger) if not m.startswith('_') and callable(getattr(logger, m))]
        print(f"\n  Available methods ({len(methods)}):")
        for i in range(0, min(20, len(methods)), 5):
            print(f"    {', '.join(methods[i:i+5])}")
        
    except Exception as e:
        print(f"  [ERROR] Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Try to log
    print("\n[4/5] Attempting to create a trace...")
    try:
        # Check which methods exist
        if hasattr(logger, 'start_session'):
            print("  Method 'start_session' exists")
            session = logger.start_session(session_name="test_win")
            print(f"  Created session: {session}")
            
            if hasattr(logger, 'start_trace'):
                print("  Method 'start_trace' exists")
                trace = logger.start_trace(
                    name="test_trace_win",
                    input="Testing from Windows"
                )
                print(f"  Created trace: {trace}")
                
                # End trace
                if hasattr(trace, 'end'):
                    trace.end()
                    print("  Ended trace")
            
            # End session
            if hasattr(session, 'end'):
                session.end()
                print("  Ended session")
        else:
            print("  [WARNING] Method 'start_session' not found!")
            print("  Available logging methods:")
            for m in methods:
                if 'log' in m.lower() or 'trace' in m.lower() or 'session' in m.lower():
                    print(f"    - {m}")
        
    except Exception as e:
        print(f"  [ERROR] Failed to log: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Flush
    print("\n[5/5] Flushing logger...")
    try:
        if hasattr(logger, 'flush'):
            logger.flush()
            print("  [OK] Logger flushed")
        else:
            print("  [WARNING] No flush method available")
    except Exception as e:
        print(f"  [ERROR] Flush failed: {e}")
    
    # Show dashboard link
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nCheck your Galileo dashboard:")
    print(f"  URL: https://app.galileo.ai")
    print(f"  Project: {project}")
    print(f"  Log Stream: {log_stream}")
    print("\nYou should see:")
    print("  - Session: test_win")
    print("  - Trace: test_trace_win")
    print("\nIf you don't see logs:")
    print("  1. Wait 10-30 seconds and refresh")
    print("  2. Check the project name matches")
    print("  3. Verify API key is correct")
    print("="*60)
    
    return True


if __name__ == "__main__":
    success = test_basic()
    sys.exit(0 if success else 1)

