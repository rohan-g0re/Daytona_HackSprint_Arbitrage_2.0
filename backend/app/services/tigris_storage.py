"""
Tigris storage service for conversation logs.

WHAT: Store and retrieve negotiation logs/transcripts in Tigris
WHY: Global, scalable storage for conversation history
HOW: Use boto3 S3-compatible API to interact with Tigris
"""

import json
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, Dict, Any

from ..core.config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TigrisStorageService:
    """Service for storing and retrieving logs from Tigris."""
    
    def __init__(self):
        """Initialize Tigris client."""
        print("=" * 80)
        print("🔍 TIGRIS DEBUG: TigrisStorageService.__init__ called")
        self.enabled = settings.TIGRIS_ENABLED
        self.bucket_name = settings.TIGRIS_BUCKET_NAME
        
        print(f"🔍 TIGRIS DEBUG: TIGRIS_ENABLED = {self.enabled}")
        print(f"🔍 TIGRIS DEBUG: TIGRIS_BUCKET_NAME = {self.bucket_name}")
        print(f"🔍 TIGRIS DEBUG: TIGRIS_ENDPOINT_URL = {settings.TIGRIS_ENDPOINT_URL}")
        print(f"🔍 TIGRIS DEBUG: TIGRIS_ACCESS_KEY_ID = {settings.TIGRIS_ACCESS_KEY_ID[:20]}..." if settings.TIGRIS_ACCESS_KEY_ID else "🔍 TIGRIS DEBUG: TIGRIS_ACCESS_KEY_ID = EMPTY")
        print(f"🔍 TIGRIS DEBUG: TIGRIS_REGION = {settings.TIGRIS_REGION}")
        print("=" * 80)
        
        if not self.enabled:
            print("❌ TIGRIS DEBUG: Tigris storage is DISABLED")
            logger.info("Tigris storage is disabled")
            self.client = None
            return
        
        print("✅ TIGRIS DEBUG: Tigris is ENABLED, creating boto3 client...")
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=settings.TIGRIS_ENDPOINT_URL,
                aws_access_key_id=settings.TIGRIS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.TIGRIS_SECRET_ACCESS_KEY,
                region_name=settings.TIGRIS_REGION
            )
            
            print("✅ TIGRIS DEBUG: boto3 client created successfully")
            
            # Ensure bucket exists
            print(f"✅ TIGRIS DEBUG: Checking/creating bucket: {self.bucket_name}")
            self._ensure_bucket_exists()
            print(f"✅ TIGRIS DEBUG: Bucket ready, initialization complete!")
            logger.info(f"Tigris storage initialized (bucket: {self.bucket_name})")
        except Exception as e:
            print(f"❌ TIGRIS DEBUG: Failed to initialize Tigris client: {e}")
            logger.error(f"Failed to initialize Tigris client: {e}")
            self.client = None
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        if not self.client:
            return
        
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.debug(f"Bucket {self.bucket_name} already exists")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket {self.bucket_name}")
                except Exception as create_error:
                    logger.error(f"Failed to create bucket {self.bucket_name}: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket {self.bucket_name}: {e}")
                raise
    
    def _get_object_key(self, session_id: str, run_id: str) -> str:
        """Generate object key for a negotiation log."""
        return f"sessions/{session_id}/{run_id}/{run_id}.json"
    
    def save_log(self, session_id: str, run_id: str, log_data: Dict[str, Any]) -> bool:
        """
        Save negotiation log to Tigris.
        
        Args:
            session_id: Session ID
            run_id: Negotiation run ID
            log_data: Log data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        print(f"🔍 TIGRIS DEBUG: save_log called - enabled={self.enabled}, has_client={self.client is not None}")
        
        if not self.enabled or not self.client:
            print(f"❌ TIGRIS DEBUG: save_log SKIPPED - enabled={self.enabled}, has_client={self.client is not None}")
            logger.debug("Tigris not enabled or client not available")
            return False
        
        object_key = self._get_object_key(session_id, run_id)
        print(f"✅ TIGRIS DEBUG: Attempting upload to bucket={self.bucket_name}, key={object_key}")
        
        try:
            # Convert log data to JSON string
            json_data = json.dumps(log_data, indent=2, default=str)
            print(f"✅ TIGRIS DEBUG: JSON data prepared, size={len(json_data)} bytes")
            
            # Upload to Tigris
            print(f"✅ TIGRIS DEBUG: Calling put_object...")
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json'
            )
            
            print(f"✅✅✅ TIGRIS DEBUG: SUCCESS! Log saved to Tigris: {object_key}")
            logger.info(f"Saved log to Tigris: {object_key}")
            return True
            
        except (ClientError, BotoCoreError) as e:
            print(f"❌ TIGRIS DEBUG: ClientError/BotoCoreError: {e}")
            logger.error(f"Failed to save log to Tigris ({object_key}): {e}")
            return False
        except Exception as e:
            print(f"❌ TIGRIS DEBUG: Unexpected error: {e}")
            logger.error(f"Unexpected error saving log to Tigris ({object_key}): {e}")
            return False
    
    def get_log(self, session_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve negotiation log from Tigris.
        
        Args:
            session_id: Session ID
            run_id: Negotiation run ID
            
        Returns:
            Log data dictionary if found, None otherwise
        """
        if not self.enabled or not self.client:
            logger.debug("Tigris not enabled or client not available")
            return None
        
        object_key = self._get_object_key(session_id, run_id)
        
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            # Read and parse JSON
            json_data = response['Body'].read().decode('utf-8')
            log_data = json.loads(json_data)
            
            logger.info(f"Retrieved log from Tigris: {object_key}")
            return log_data
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                logger.debug(f"Log not found in Tigris: {object_key}")
            else:
                logger.error(f"Error retrieving log from Tigris ({object_key}): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving log from Tigris ({object_key}): {e}")
            return None
    
    def delete_log(self, session_id: str, run_id: str) -> bool:
        """
        Delete negotiation log from Tigris.
        
        Args:
            session_id: Session ID
            run_id: Negotiation run ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        object_key = self._get_object_key(session_id, run_id)
        
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"Deleted log from Tigris: {object_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete log from Tigris ({object_key}): {e}")
            return False
    
    def list_logs(self, session_id: Optional[str] = None) -> list[str]:
        """
        List all log keys in Tigris.
        
        Args:
            session_id: Optional session ID to filter by
            
        Returns:
            List of object keys
        """
        if not self.enabled or not self.client:
            return []
        
        prefix = f"sessions/{session_id}/" if session_id else "sessions/"
        
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            return [obj['Key'] for obj in response['Contents']]
        except Exception as e:
            logger.error(f"Error listing logs from Tigris: {e}")
            return []


# Singleton instance
tigris_storage = TigrisStorageService()

