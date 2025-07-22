from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
import asyncio
import logging
from typing import Optional

from ai_engine.services.worksheet_agent import generate_worksheet_from_image
from ai_engine.services.lesson_planner_agent import generate_lesson_plan
from ai_engine.services.pdf_service import worksheet_to_pdf_bytes

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Educational AI Assistant API",
    description="Generate educational worksheets and lesson plans",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Educational AI Assistant API is running"}


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


@app.post("/generate_lesson_plan")
async def generate_lesson_plan_endpoint(
    teacher_requirements: str = Form(
        ..., description="Teacher's requirements for the lesson plan"
    )
):
    """
    Generate a comprehensive lesson plan based on teacher's requirements.

    - **teacher_requirements**: A string describing the topic, grade level, number of lessons,
      duration, learning objectives, and any other specific requirements. Can be simple
      (just a topic) or very detailed.

    Examples of input:
    - "Solar system for 5th grade, 4 lessons"
    - "Photosynthesis, grade 8, 3 lessons, 45 minutes each, hands-on activities"
    - "American Revolution"
    - "Fractions and decimals for grade 4, 5 lessons, include games and group activities"

    Returns: A comprehensive text-based lesson plan
    """
    try:
        logger.info(
            f"Received request to generate lesson plan: {teacher_requirements[:100]}..."
        )

        if not teacher_requirements.strip():
            logger.warning("Empty teacher requirements received")
            raise HTTPException(
                status_code=400, detail="Teacher requirements cannot be empty"
            )

        # Generate lesson plan using the service
        lesson_plan = await generate_lesson_plan(teacher_requirements)

        logger.info("Successfully generated lesson plan")

        # Return lesson plan as plain text
        return Response(
            content=lesson_plan,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=lesson_plan.txt"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating lesson plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate lesson plan: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
