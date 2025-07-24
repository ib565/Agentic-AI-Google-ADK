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
    subject: str = Form(..., description="Subject area (e.g., Math, Science, History)"),
    topic: Optional[str] = Form(None, description="Specific topic (optional)"),
    description: Optional[str] = Form(
        None, description="Additional instructions or requirements (optional)"
    ),
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
            image_bytes=image_bytes,
            grade=grade,
            filename=image.filename or "image.png",
            subject=subject,
            topic=topic,
            description=description,
        )

        # Convert to PDF
        pdf_bytes = worksheet_to_pdf_bytes(worksheet)

        logger.info(f"Successfully generated worksheet PDF for grade {grade}")

        # Upload to Firebase Storage
        subject_part = f"_{subject.lower().replace(' ', '_')}" if subject else ""
        filename = f"worksheet{subject_part}_grade_{grade}.pdf"
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
            "subject": subject,
            "topic": topic,
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
    subject: str = Form(..., description="Subject area (e.g., Math, Science, History)"),
    grade: int = Form(..., description="Grade level (1-12)", ge=1, le=12),
    topic: Optional[str] = Form(None, description="Specific topic (optional)"),
    description: Optional[str] = Form(
        None, description="Additional instructions or requirements (optional)"
    ),
):
    """
    Generate a comprehensive lesson plan PDF based on structured input parameters.

    - **subject**: Subject area (e.g., Math, Science, History, English)
    - **grade**: Grade level (1-12)
    - **topic**: Specific topic within the subject (optional)
    - **description**: Additional instructions, requirements, or specific details (optional)

    Examples:
    - subject="Math", grade=5, topic="Fractions", description="Include hands-on activities"
    - subject="Science", grade=8, topic="Photosynthesis"
    - subject="History", grade=10, description="Focus on primary sources"

    Returns: JSON response with the Firebase URL of the generated lesson plan PDF
    """
    try:
        logger.info(
            f"Received request to generate lesson plan: subject={subject}, grade={grade}, topic={topic}"
        )

        # Generate lesson plan using the service with structured parameters
        lesson_plan = await generate_lesson_plan(subject, grade, topic, description)

        # Convert to PDF
        pdf_bytes = lesson_plan_to_pdf_bytes(lesson_plan)

        logger.info("Successfully generated lesson plan PDF")

        # Upload to Firebase Storage
        filename = f"lesson_plan_{subject.lower().replace(' ', '_')}_grade_{grade}.pdf"
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
            "subject": subject,
            "grade": grade,
            "topic": topic,
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
    subject: str = Form(..., description="Subject area (e.g., Math, Science, History)"),
    grade: int = Form(..., description="Grade level (1-12)", ge=1, le=12),
    topic: Optional[str] = Form(None, description="Specific topic (optional)"),
    description: Optional[str] = Form(
        None, description="Additional instructions or requirements (optional)"
    ),
):
    """
    Generate comprehensive study materials with detailed topics and subtopics.

    - **subject**: Subject area (e.g., Math, Science, History, English)
    - **grade**: Grade level (1-12)
    - **topic**: Specific topic within the subject (optional)
    - **description**: Additional instructions, requirements, or specific details (optional)

    Examples:
    - subject="Biology", grade=8, topic="Photosynthesis"
    - subject="History", grade=11, topic="World War II", description="Focus on European theater"
    - subject="Math", grade=7, topic="Basic Algebra"
    - subject="Science", grade=6, description="Climate change and environmental science"

    Returns: JSON response with the Firebase URL of the generated study material text file
    """
    try:
        logger.info(
            f"Received request to generate study material: subject={subject}, grade={grade}, topic={topic}"
        )

        # Generate study material using the service with structured parameters
        study_material = await generate_study_material(
            subject, grade, topic, description
        )

        logger.info("Successfully generated study material")

        # Convert string to bytes for upload
        study_material_bytes = study_material.encode("utf-8")

        # Upload to Firebase Storage
        filename = (
            f"study_material_{subject.lower().replace(' ', '_')}_grade_{grade}.txt"
        )
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
            "subject": subject,
            "grade": grade,
            "topic": topic,
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
