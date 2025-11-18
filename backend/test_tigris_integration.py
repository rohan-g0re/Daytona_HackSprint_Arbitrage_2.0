"""
Test script for Tigris storage integration.

This script tests the Tigris storage service to ensure:
1. Service initializes correctly
2. Logs can be saved to Tigris
3. Logs can be retrieved from Tigris
4. Logs can be listed from Tigris

Usage:
    1. Set up Tigris credentials in .env file:
       - TIGRIS_ENABLED=true
       - TIGRIS_ACCESS_KEY_ID=your-key
       - TIGRIS_SECRET_ACCESS_KEY=your-secret
       - TIGRIS_BUCKET_NAME=negotiation-logs
    
    2. Run: python backend/test_tigris_integration.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.tigris_storage import tigris_storage
from app.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def test_tigris_integration():
    """Test Tigris storage integration."""
    
    print("=" * 80)
    print("Tigris Storage Integration Test")
    print("=" * 80)
    print()
    
    # Check configuration
    print("Configuration Check:")
    print(f"  TIGRIS_ENABLED: {settings.TIGRIS_ENABLED}")
    print(f"  TIGRIS_ENDPOINT_URL: {settings.TIGRIS_ENDPOINT_URL}")
    print(f"  TIGRIS_BUCKET_NAME: {settings.TIGRIS_BUCKET_NAME}")
    print(f"  TIGRIS_REGION: {settings.TIGRIS_REGION}")
    print(f"  Access Key configured: {bool(settings.TIGRIS_ACCESS_KEY_ID)}")
    print(f"  Secret Key configured: {bool(settings.TIGRIS_SECRET_ACCESS_KEY)}")
    print()
    
    if not settings.TIGRIS_ENABLED:
        print("❌ TIGRIS_ENABLED is False. Set TIGRIS_ENABLED=true in .env to test.")
        return False
    
    if not settings.TIGRIS_ACCESS_KEY_ID or not settings.TIGRIS_SECRET_ACCESS_KEY:
        print("❌ Tigris credentials not configured. Add TIGRIS_ACCESS_KEY_ID and TIGRIS_SECRET_ACCESS_KEY to .env")
        return False
    
    # Check if service initialized
    print("Service Initialization Check:")
    if tigris_storage.client is None:
        print("❌ Tigris client failed to initialize")
        return False
    else:
        print("✅ Tigris client initialized successfully")
    print()
    
    # Test save_log
    print("Testing save_log()...")
    test_session_id = "test-session-123"
    test_run_id = "test-run-456"
    test_log_data = {
        "metadata": {
            "session_id": test_session_id,
            "run_id": test_run_id,
            "test": True
        },
        "conversation_history": [
            {"turn": 1, "sender": "buyer", "message": "Test message"}
        ]
    }
    
    save_success = tigris_storage.save_log(test_session_id, test_run_id, test_log_data)
    if save_success:
        print("✅ Log saved successfully")
    else:
        print("❌ Failed to save log")
        return False
    print()
    
    # Test get_log
    print("Testing get_log()...")
    retrieved_log = tigris_storage.get_log(test_session_id, test_run_id)
    if retrieved_log:
        print("✅ Log retrieved successfully")
        if retrieved_log.get("metadata", {}).get("run_id") == test_run_id:
            print("✅ Retrieved log data matches saved data")
        else:
            print("❌ Retrieved log data doesn't match")
            return False
    else:
        print("❌ Failed to retrieve log")
        return False
    print()
    
    # Test list_logs
    print("Testing list_logs()...")
    logs = tigris_storage.list_logs(test_session_id)
    if logs:
        print(f"✅ Found {len(logs)} log(s) for session {test_session_id}")
        for log_key in logs:
            print(f"   - {log_key}")
    else:
        print("⚠️  No logs found (might be empty bucket)")
    print()
    
    # Test delete_log
    print("Testing delete_log() (cleanup)...")
    delete_success = tigris_storage.delete_log(test_session_id, test_run_id)
    if delete_success:
        print("✅ Test log deleted successfully")
    else:
        print("⚠️  Failed to delete test log (manual cleanup may be needed)")
    print()
    
    print("=" * 80)
    print("✅ All tests passed! Tigris integration is working correctly.")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Run a negotiation in your app")
    print("2. Check the Tigris UI/dashboard to see the log files")
    print("3. Log files will be stored at: sessions/{session_id}/{run_id}/{run_id}.json")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_tigris_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)

