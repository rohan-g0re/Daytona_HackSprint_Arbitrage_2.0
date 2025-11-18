"""
Test Galileo using galileo_context API (from quickstart guide).

WHAT: Test using the recommended galileo_context API
WHY: GalileoLogger manual API might not work as expected
HOW: Follow the exact quickstart guide pattern
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()


def test_with_context_api():
    """Test using galileo_context (recommended in quickstart)."""
    print("="*60)
    print("Testing with galileo_context API")
    print("="*60)
    
    try:
        from galileo import galileo_context
        from galileo.config import GalileoPythonConfig
        
        # Initialize context
        print("\n[1/5] Initializing galileo_context...")
        galileo_context.init(
            project=os.getenv('GALILEO_PROJECT', 'Arbritrage'),
            log_stream=os.getenv('GALILEO_LOG_STREAM', 'default')
        )
        print("✅ Context initialized")
        
        # Get the logger instance
        print("\n[2/5] Getting logger instance...")
        logger = galileo_context.get_logger_instance()
        print(f"✅ Logger: {logger}")
        
        # Log a simple trace (check what methods are available)
        print("\n[3/5] Checking available methods...")
        methods = [m for m in dir(logger) if not m.startswith('_')]
        print(f"   Available methods: {', '.join(methods[:10])}...")
        
        # Try to log something
        print("\n[4/5] Attempting to log a trace...")
        
        # Try different approaches
        if hasattr(logger, 'start_session'):
            print("   Trying start_session...")
            session = logger.start_session(session_name="test_session")
            print(f"   ✅ Session: {session}")
            
            if hasattr(session, 'end'):
                session.end()
        
        # Flush context
        print("\n[5/5] Flushing context...")
        if hasattr(galileo_context, 'flush'):
            galileo_context.flush()
            print("✅ Context flushed")
        
        # Get URLs
        try:
            config = GalileoPythonConfig.get()
            console_url = config.console_url or "https://app.galileo.ai"
            print(f"\n🔗 Check dashboard: {console_url}")
        except:
            print(f"\n🔗 Check dashboard: https://app.galileo.ai")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_openai_integration():
    """Test if OpenAI integration pattern works."""
    print("\n" + "="*60)
    print("Testing with OpenAI-style integration")
    print("="*60)
    
    try:
        # This is the pattern from the quickstart guide
        print("\nTrying OpenAI integration pattern...")
        print("(This requires OpenAI API key, but tests the logging pattern)")
        
        from galileo import galileo_context
        
        # Initialize
        galileo_context.init(
            project=os.getenv('GALILEO_PROJECT', 'Arbritrage'),
            log_stream=os.getenv('GALILEO_LOG_STREAM', 'default')
        )
        
        # Import OpenAI wrapper
        try:
            import galileo.openai as openai_wrapper
            print("✅ OpenAI integration is available")
            print("   This means automatic logging should work")
        except:
            print("⚠️  OpenAI integration not available")
            print("   Install with: pip install 'galileo[openai]'")
        
        # Flush
        if hasattr(galileo_context, 'flush'):
            galileo_context.flush()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("GALILEO CONTEXT API TEST")
    print("="*60)
    
    # Check environment
    api_key = os.getenv('GALILEO_API_KEY')
    enabled = os.getenv('GALILEO_ENABLED', 'false').lower() == 'true'
    
    if not enabled or not api_key:
        print("\n❌ Galileo not configured properly")
        print(f"   GALILEO_ENABLED: {enabled}")
        print(f"   GALILEO_API_KEY: {'set' if api_key else 'NOT SET'}")
        return False
    
    # Test context API
    if not test_with_context_api():
        print("\n❌ Context API test failed")
        return False
    
    # Test OpenAI integration
    test_openai_integration()
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Check https://app.galileo.ai")
    print("2. Look for your project: Arbritrage")
    print("3. Check log stream: default")
    print("\nIf you don't see logs, the SDK might need a different API.")
    print("Check: https://v2docs.galileo.ai/sdk-api/logging/logging-basics")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

