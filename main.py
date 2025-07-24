from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
import asyncio
import logging
from typing import Optional

from ai_engine.services.worksheet_agent import generate_worksheet_from_image
from ai_engine.services.lesson_planner_agent import generate_lesson_plan
from ai_engine.services.study_material_agent import generate_study_material
from ai_engine.services.pdf_service import (
    worksheet_to_pdf_bytes,
    lesson_plan_to_pdf_bytes,
)
from ai_engine.services.firebase_service import firebase_service

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Educational AI Assistant API",
    description="Generate educational worksheets, lesson plans, and comprehensive study materials",
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

    Returns: JSON response with the Firebase URL of the generated worksheet PDF
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

        # Upload to Firebase Storage
        filename = f"worksheet_grade_{grade}.pdf"
        firebase_url = firebase_service.upload_bytes(
            content_bytes=pdf_bytes,
            folder="content/worksheet",
            filename=filename,
            content_type="application/pdf",
        )

        if not firebase_url:
            raise HTTPException(
                status_code=500, detail="Failed to upload worksheet to Firebase Storage"
            )

        logger.info(f"Worksheet uploaded to Firebase: {firebase_url}")

        # Return JSON response with the URL
        return {
            "success": True,
            "message": f"Worksheet generated successfully for grade {grade}",
            "url": firebase_url,
            "type": "worksheet",
            "grade": grade,
        }

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
    Generate a comprehensive lesson plan PDF based on teacher's requirements.

    - **teacher_requirements**: A string describing the topic, grade level, number of lessons,
      duration, learning objectives, and any other specific requirements. Can be simple
      (just a topic) or very detailed.

    Examples of input:
    - "Solar system for 5th grade, 4 lessons"
    - "Photosynthesis, grade 8, 3 lessons, 45 minutes each, hands-on activities"
    - "American Revolution"
    - "Fractions and decimals for grade 4, 5 lessons, include games and group activities"

    Returns: JSON response with the Firebase URL of the generated lesson plan PDF
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

        # Convert to PDF
        pdf_bytes = lesson_plan_to_pdf_bytes(lesson_plan)

        logger.info("Successfully generated lesson plan PDF")

        # Upload to Firebase Storage
        filename = "lesson_plan.pdf"
        firebase_url = firebase_service.upload_bytes(
            content_bytes=pdf_bytes,
            folder="content/lesson_plan",
            filename=filename,
            content_type="application/pdf",
        )

        if not firebase_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload lesson plan to Firebase Storage",
            )

        logger.info(f"Lesson plan uploaded to Firebase: {firebase_url}")

        # Return JSON response with the URL
        return {
            "success": True,
            "message": "Lesson plan generated successfully",
            "url": firebase_url,
            "type": "lesson_plan",
            "title": (
                lesson_plan.title if hasattr(lesson_plan, "title") else "Lesson Plan"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating lesson plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate lesson plan: {str(e)}"
        )


@app.post("/generate_study_material")
async def generate_study_material_endpoint(
    teacher_requirements: str = Form(
        ..., description="Teacher's requirements for the study material"
    )
):
    """
    Generate comprehensive study materials with detailed topics and subtopics.

    - **teacher_requirements**: A string describing the topic, grade level, subject area,
      difficulty level, and any other specific requirements. Can be simple
      (just a topic) or very detailed.

    Examples of input:
    - "Photosynthesis for 8th grade biology"
    - "World War II, high school level, comprehensive coverage"
    - "Basic algebra concepts for grade 7"
    - "Climate change and environmental science, intermediate level"
    - "Ancient civilizations for 6th grade social studies"

    Returns: JSON response with the Firebase URL of the generated study material text file
    """
    try:
        logger.info(
            f"Received request to generate study material: {teacher_requirements[:100]}..."
        )

        if not teacher_requirements.strip():
            logger.warning("Empty teacher requirements received")
            raise HTTPException(
                status_code=400, detail="Teacher requirements cannot be empty"
            )

        # Generate study material using the service
        study_material = await generate_study_material(teacher_requirements)

        logger.info("Successfully generated study material")

        # Convert string to bytes for upload
        study_material_bytes = study_material.encode("utf-8")

        # Upload to Firebase Storage
        filename = "study_material.txt"
        firebase_url = firebase_service.upload_bytes(
            content_bytes=study_material_bytes,
            folder="content/study_material",
            filename=filename,
            content_type="text/plain",
        )

        if not firebase_url:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload study material to Firebase Storage",
            )

        logger.info(f"Study material uploaded to Firebase: {firebase_url}")

        # Return JSON response with the URL
        return {
            "success": True,
            "message": "Study material generated successfully",
            "url": firebase_url,
            "type": "study_material",
            "requirements": (
                teacher_requirements[:100] + "..."
                if len(teacher_requirements) > 100
                else teacher_requirements
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating study material: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate study material: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
