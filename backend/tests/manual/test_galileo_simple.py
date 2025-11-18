"""
Simple Galileo connectivity test - minimal test to verify API key and connection.

WHAT: Most basic possible Galileo test
WHY: Diagnose why logs aren't appearing
HOW: Use the simplest Galileo API patterns from the docs
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()


def test_basic_import():
    """Test if Galileo SDK is installed."""
    print("="*60)
    print("STEP 1: Testing Galileo SDK Import")
    print("="*60)
    
    try:
        import galileo
        print("✅ Galileo SDK is installed")
        print(f"   Version: {getattr(galileo, '__version__', 'unknown')}")
        return True
    except ImportError as e:
        print("❌ Galileo SDK not installed!")
        print(f"   Error: {e}")
        print("\n   Fix: pip install galileo python-dotenv")
        return False


def test_env_config():
    """Test if environment variables are set."""
    print("\n" + "="*60)
    print("STEP 2: Testing Environment Configuration")
    print("="*60)
    
    api_key = os.getenv('GALILEO_API_KEY')
    enabled = os.getenv('GALILEO_ENABLED', 'false').lower() == 'true'
    project = os.getenv('GALILEO_PROJECT', 'Arbritrage')
    log_stream = os.getenv('GALILEO_LOG_STREAM', 'default')
    
    print(f"GALILEO_ENABLED: {enabled}")
    print(f"GALILEO_API_KEY: {'***' + api_key[-4:] if api_key and len(api_key) > 4 else 'NOT SET'}")
    print(f"GALILEO_PROJECT: {project}")
    print(f"GALILEO_LOG_STREAM: {log_stream}")
    
    if not enabled:
        print("\n❌ GALILEO_ENABLED is false or not set")
        print("   Fix: Add to .env file: GALILEO_ENABLED=true")
        return False
    
    if not api_key:
        print("\n❌ GALILEO_API_KEY is not set")
        print("   Fix: Add to .env file: GALILEO_API_KEY=gal_your_key_here")
        print("   Get key from: https://app.galileo.ai (Settings → API Keys)")
        return False
    
    print("\n✅ Environment configuration looks good")
    return True


def test_galileo_connection():
    """Test actual connection to Galileo."""
    print("\n" + "="*60)
    print("STEP 3: Testing Galileo Connection")
    print("="*60)
    
    try:
        from galileo import GalileoLogger
        
        # Initialize logger
        print("\n[1/4] Initializing GalileoLogger...")
        logger = GalileoLogger(
            project=os.getenv('GALILEO_PROJECT', 'Arbritrage'),
            log_stream=os.getenv('GALILEO_LOG_STREAM', 'default')
        )
        print("✅ Logger initialized")
        
        # Start a session
        print("\n[2/4] Starting session...")
        session = logger.start_session(
            session_name="test_session_simple"
        )
        print(f"✅ Session started: {session}")
        
        # Start a trace
        print("\n[3/4] Starting trace...")
        trace = logger.start_trace(
            name="test_trace",
            input="This is a test trace"
        )
        print(f"✅ Trace started: {trace}")
        
        # End trace
        print("\n[4/4] Ending trace and session...")
        if hasattr(trace, 'end'):
            trace.end()
            print("✅ Trace ended")
        
        if hasattr(session, 'end'):
            session.end()
            print("✅ Session ended")
        
        # Flush logger
        if hasattr(logger, 'flush'):
            print("\n[5/5] Flushing logger...")
            logger.flush()
            print("✅ Logger flushed")
        
        print("\n" + "="*60)
        print("✅ SUCCESS: Galileo connection test passed!")
        print("="*60)
        print("\n📊 Check your dashboard:")
        print("   URL: https://app.galileo.ai")
        print(f"   Project: {os.getenv('GALILEO_PROJECT', 'Arbritrage')}")
        print(f"   Log Stream: {os.getenv('GALILEO_LOG_STREAM', 'default')}")
        print("\n   You should see:")
        print("   - Session: test_session_simple")
        print("   - Trace: test_trace")
        print("\n" + "="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during Galileo connection test:")
        print(f"   {type(e).__name__}: {e}")
        
        import traceback
        print("\n   Full traceback:")
        traceback.print_exc()
        
        print("\n   Possible causes:")
        print("   1. Invalid API key")
        print("   2. Network connection issue")
        print("   3. Galileo API is down")
        print("   4. Incorrect SDK methods (API changed)")
        
        return False


def main():
    """Run all diagnostic tests."""
    print("\n" + "="*60)
    print("GALILEO DIAGNOSTIC TEST")
    print("="*60)
    print("\nThis will test your Galileo setup step by step.\n")
    
    # Test 1: SDK installed
    if not test_basic_import():
        print("\n❌ FAILED: Install Galileo SDK first")
        return False
    
    # Test 2: Environment config
    if not test_env_config():
        print("\n❌ FAILED: Fix environment configuration")
        return False
    
    # Test 3: Actual connection
    if not test_galileo_connection():
        print("\n❌ FAILED: Connection to Galileo failed")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYour Galileo integration is working correctly.")
    print("Logs should now appear in your dashboard.")
    print("\nIf you still don't see logs, wait 10-30 seconds and refresh.")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

