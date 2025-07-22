from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
import asyncio
import logging
from typing import Optional

from ai_engine.services.worksheet_agent import generate_worksheet_from_image
from ai_engine.services.pdf_service import worksheet_to_pdf_bytes

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Worksheet Generator API",
    description="Generate educational worksheets from textbook images",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Worksheet Generator API is running"}


@app.post("/generate_worksheet_from_image")
async def generate_worksheet_from_image_endpoint(
    image: UploadFile = File(..., description="Textbook image file (PNG, JPG, JPEG)"),
    grade: int = Form(..., description="Grade level (e.g., 3, 6, 9)", ge=1, le=12),
):
    """
    Generate a worksheet PDF from a textbook image for a specific grade level.

    - **image**: Upload a textbook page image (PNG, JPG, or JPEG)
    - **grade**: Grade level for the worksheet (1-12)

    Returns: PDF file with the generated worksheet
    """
    try:
        logger.info(f"Received request to generate worksheet for grade {grade}")

        # Validate file type
        if not image.content_type or not image.content_type.startswith("image/"):
            logger.warning(f"Invalid file type: {image.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read image bytes
        image_bytes = await image.read()

        if len(image_bytes) == 0:
            logger.warning("Empty image file received")
            raise HTTPException(status_code=400, detail="Empty image file")

        logger.info(
            f"Processing image: {image.filename}, size: {len(image_bytes)} bytes"
        )

        # Generate worksheet using the service
        worksheet = await generate_worksheet_from_image(
            image_bytes=image_bytes, grade=grade, filename=image.filename or "image.png"
        )

        # Convert to PDF
        pdf_bytes = worksheet_to_pdf_bytes(worksheet)

        logger.info(f"Successfully generated worksheet PDF for grade {grade}")

        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=worksheet_grade_{grade}.pdf"
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating worksheet: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate worksheet: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
