from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import asyncio
import logging
import base64
from typing import Optional

from ai_engine.services.worksheet_agent import generate_worksheet_from_image
from ai_engine.services.lesson_planner_agent import generate_lesson_plan
from ai_engine.services.study_material_agent import generate_study_material
from ai_engine.services.pdf_service import (
    worksheet_to_pdf_bytes,
    lesson_plan_to_pdf_bytes,
    study_material_to_pdf_bytes,
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


# Pydantic models for JSON request bodies
class WorksheetRequest(BaseModel):
    image_base64: str
    image_filename: Optional[str] = "image.png"
    grade: str
    subject: str
    topic: Optional[str] = None
    description: Optional[str] = None


class LessonPlanRequest(BaseModel):
    subject: str
    grade: str
    topic: Optional[str] = None
    description: Optional[str] = None


class StudyMaterialRequest(BaseModel):
    subject: str
    grade: str
    topic: Optional[str] = None
    description: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Educational AI Assistant API is running"}


@app.post("/generate_worksheet_from_image")
async def generate_worksheet_from_image_endpoint(request: WorksheetRequest):
    """
    Generate a worksheet PDF from a textbook image for a specific grade level.

    - **image_base64**: Base64 encoded image data (PNG, JPG, or JPEG)
    - **image_filename**: Original filename (optional, defaults to "image.png")
    - **grade**: Grade level for the worksheet (1-12)
    - **subject**: Subject area (e.g., Math, Science, History)
    - **topic**: Specific topic (optional)
    - **description**: Additional instructions or requirements (optional)

    Returns: JSON response with the Firebase URL of the generated worksheet PDF
    """
    try:
        logger.info(f"Received request to generate worksheet for grade {request.grade}")

        # Decode base64 image
        try:
            image_bytes = base64.b64decode(request.image_base64)
        except Exception as e:
            logger.warning(f"Invalid base64 image data: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid base64 image data")

        if len(image_bytes) == 0:
            logger.warning("Empty image data received")
            raise HTTPException(status_code=400, detail="Empty image data")

        logger.info(
            f"Processing image: {request.image_filename}, size: {len(image_bytes)} bytes"
        )

        # Generate worksheet using the service
        worksheet = await generate_worksheet_from_image(
            image_bytes=image_bytes,
            grade=request.grade,
            filename=request.image_filename,
            subject=request.subject,
            topic=request.topic,
            description=request.description,
        )

        # Convert to PDF
        pdf_bytes = worksheet_to_pdf_bytes(worksheet)

        logger.info(f"Successfully generated worksheet PDF for grade {request.grade}")

        # Upload to Firebase Storage
        subject_part = (
            f"_{request.subject.lower().replace(' ', '_')}" if request.subject else ""
        )
        filename = f"worksheet{subject_part}_grade_{request.grade}.pdf"
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
            "message": f"Worksheet generated successfully for grade {request.grade}",
            "url": firebase_url,
            "type": "worksheet",
            "grade": request.grade,
            "subject": request.subject,
            "topic": request.topic,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating worksheet: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate worksheet: {str(e)}"
        )


@app.post("/generate_lesson_plan")
async def generate_lesson_plan_endpoint(request: LessonPlanRequest):
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
            f"Received request to generate lesson plan: subject={request.subject}, grade={request.grade}, topic={request.topic}"
        )

        # Generate lesson plan using the service with structured parameters
        lesson_plan = await generate_lesson_plan(
            request.subject, request.grade, request.topic, request.description
        )

        # Convert to PDF
        pdf_bytes = lesson_plan_to_pdf_bytes(lesson_plan)

        logger.info("Successfully generated lesson plan PDF")

        # Upload to Firebase Storage
        filename = f"lesson_plan_{request.subject.lower().replace(' ', '_')}_grade_{request.grade}.pdf"
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
            "subject": request.subject,
            "grade": request.grade,
            "topic": request.topic,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating lesson plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate lesson plan: {str(e)}"
        )


@app.post("/generate_study_material")
async def generate_study_material_endpoint(request: StudyMaterialRequest):
    """
    Generate comprehensive study materials with detailed topics and subtopics as a formatted PDF.

    - **subject**: Subject area (e.g., Math, Science, History, English)
    - **grade**: Grade level (1-12)
    - **topic**: Specific topic within the subject (optional)
    - **description**: Additional instructions, requirements, or specific details (optional)

    Examples:
    - subject="Biology", grade=8, topic="Photosynthesis"
    - subject="History", grade=11, topic="World War II", description="Focus on European theater"
    - subject="Math", grade=7, topic="Basic Algebra"
    - subject="Science", grade=6, description="Climate change and environmental science"

    Returns: JSON response with the Firebase URL of the generated study material PDF
    """
    try:
        logger.info(
            f"Received request to generate study material: subject={request.subject}, grade={request.grade}, topic={request.topic}"
        )

        # Generate study material using the service with structured parameters
        study_material = await generate_study_material(
            request.subject, request.grade, request.topic, request.description
        )

        logger.info("Successfully generated study material")

        # Convert study material to PDF bytes
        pdf_bytes = study_material_to_pdf_bytes(study_material)

        # Upload to Firebase Storage
        filename = f"study_material_{request.subject.lower().replace(' ', '_')}_grade_{request.grade}.pdf"
        firebase_url = firebase_service.upload_bytes(
            content_bytes=pdf_bytes,
            folder="content/study_material",
            filename=filename,
            content_type="application/pdf",
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
            "subject": request.subject,
            "grade": request.grade,
            "topic": request.topic,
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
