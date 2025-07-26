import io
import base64
import zlib
import logging
import requests
import json
from typing import Optional

from .firebase_service import firebase_service

logger = logging.getLogger(__name__)

# Configuration constant
KROKI_SERVER = "https://kroki.io"


def generate_diagram_image(
    mermaid_syntax: str, output_format: str = "png"
) -> Optional[bytes]:
    """
    Convert Mermaid syntax to image bytes using Kroki API

    Args:
        mermaid_syntax: The Mermaid code
        output_format: Output format (png, svg, pdf)

    Returns:
        Image bytes if successful, None if failed
    """
    try:
        # First try POST request to /mermaid/format endpoint (simpler)
        url = f"{KROKI_SERVER}/mermaid/{output_format}"
        headers = {"Content-Type": "application/json"}
        payload = {"diagram_source": mermaid_syntax}

        response = requests.post(
            url,
            data=json.dumps(payload),
            headers=headers,
            timeout=30,
        )

        # If POST fails, try GET with proper deflate + base64 encoding
        if response.status_code != 200:
            logger.warning(
                f"POST request failed with status {response.status_code}, trying GET request"
            )

            # Encode mermaid syntax using deflate + base64 (as required by Kroki)
            compressed = zlib.compress(mermaid_syntax.encode("utf-8"), 9)
            encoded_syntax = base64.urlsafe_b64encode(compressed).decode("ascii")

            # Use GET endpoint with proper encoding
            url = f"{KROKI_SERVER}/mermaid/{output_format}/{encoded_syntax}"
            response = requests.get(url, timeout=30)

        response.raise_for_status()

        logger.info(f"Successfully generated {output_format} diagram from Mermaid")
        return response.content

    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request to Kroki server: {e}")
        return None
    except Exception as e:
        logger.error(f"Error generating diagram: {e}")
        return None


def create_and_upload_diagram(
    mermaid_syntax: str,
    title: str,
    subject: str = "general",
    output_format: str = "png",
) -> Optional[str]:
    """
    Generate diagram from Mermaid syntax and upload to Firebase

    Args:
        mermaid_syntax: The Mermaid code
        title: Title for the diagram (used in filename)
        subject: Subject area for organizing uploads
        output_format: Output format (png, svg, pdf)

    Returns:
        Public URL of uploaded image if successful, None if failed
    """
    try:
        # Generate the diagram image
        image_bytes = generate_diagram_image(mermaid_syntax, output_format)

        if not image_bytes:
            logger.error("Failed to generate diagram image")
            return None

        # Prepare filename and folder
        safe_title = "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        safe_title = safe_title.replace(" ", "_").lower()
        filename = f"{safe_title}_diagram.{output_format}"
        folder = f"visual_aids/{subject.lower()}"

        # Set content type
        content_type = f"image/{output_format}"

        # Upload to Firebase
        public_url = firebase_service.upload_bytes(
            content_bytes=image_bytes,
            folder=folder,
            filename=filename,
            content_type=content_type,
        )

        if public_url:
            logger.info(f"Successfully uploaded diagram to: {public_url}")
            return public_url
        else:
            logger.error("Failed to upload diagram to Firebase")
            return None

    except Exception as e:
        logger.error(f"Error creating and uploading diagram: {e}")
        return None
