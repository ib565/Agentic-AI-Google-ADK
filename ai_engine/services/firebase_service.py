import os
import logging
from datetime import datetime
from typing import Optional
import firebase_admin
from firebase_admin import credentials, storage

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service for uploading files to Firebase Storage"""

    def __init__(self):
        self._initialized = False
        self._bucket = None

    def initialize(self):
        """Initialize Firebase Admin SDK with service account key"""
        if self._initialized:
            return True

        try:
            # Path to the service account key file
            cred_path = "google-services.json"

            if not os.path.exists(cred_path):
                logger.error(f"Service account key file not found at {cred_path}")
                return False

            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(
                    cred, {"storageBucket": "billbox-7c1c7.appspot.com"}
                )

            self._bucket = storage.bucket()
            self._initialized = True
            logger.info("Firebase initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            return False

    def upload_bytes(
        self, content_bytes: bytes, folder: str, filename: str, content_type: str
    ) -> Optional[str]:
        """
        Upload bytes content to Firebase Storage with timestamped filename

        Args:
            content_bytes: The file content as bytes
            folder: The folder path (e.g., 'content/worksheet')
            filename: Base filename (will be timestamped)
            content_type: MIME type of the content

        Returns:
            Public URL if successful, None if failed
        """
        if not self.initialize():
            return None

        try:
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_parts = filename.rsplit(".", 1) if "." in filename else [filename, ""]
            if len(name_parts) == 2:
                timestamped_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                timestamped_filename = f"{filename}_{timestamp}"

            # Create full storage path
            storage_path = f"{folder}/{timestamped_filename}"

            # Create a blob and upload
            blob = self._bucket.blob(storage_path)
            blob.upload_from_string(content_bytes, content_type=content_type)

            # Make the file publicly accessible
            blob.make_public()

            # Get the public URL
            public_url = blob.public_url

            logger.info(f"File uploaded successfully to {storage_path}")
            logger.info(f"Public URL: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return None


# Global instance
firebase_service = FirebaseService()
