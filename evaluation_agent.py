import os
# from google.cloud import documentai_v1beta3 as documentai
from google.cloud import documentai_v1 as documentai

from google.cloud import storage
from google.cloud import aiplatform
import google.generativeai as genai
import json
from difflib import SequenceMatcher
from dotenv import load_dotenv
from google.genai.types import HttpOptions
import re

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')
PROJECT_ID=os.getenv("PROJECT_ID")
LOCATION=os.getenv("LOCATION")
PROCESSOR_ID=os.getenv("PROCESSOR_ID")

from google.api_core.client_options import ClientOptions
from google.cloud import documentai


def extract_text_from_pdf_with_docai(file_path, project_id, location, processor_id, mime_type="application/pdf"):
    """
    Extracts text from a PDF file using Google Cloud Document AI.

    Args:
        file_path (str): Path to the input PDF.
        project_id (str): Google Cloud project ID (alphanumeric).
        location (str): Region where the processor is deployed (e.g., 'us').
        processor_id (str): The processor ID from Document AI Console.
        mime_type (str): MIME type of the file. Default is 'application/pdf'.

    Returns:
        str: Extracted text from the document.
    """

    # Initialize the Document AI client with regional endpoint
    client = documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    )

    # Construct the full resource name for the processor
    resource_name = client.processor_path(project_id, location, processor_id)

    # Read the PDF file into memory
    with open(file_path, "rb") as f:
        file_content = f.read()

    # Create the RawDocument object
    raw_document = documentai.RawDocument(content=file_content, mime_type=mime_type)

    # Build the request
    request = documentai.ProcessRequest(name=resource_name, raw_document=raw_document)

    # Process the document
    result = client.process_document(request=request)
    document_object = result.document

    # Return the extracted text
    return document_object.text

# The local file in your current working directory


def extract_quiz_answers_from_text(raw_text: str) -> str:
    """
    Extract quiz answers from raw submission text using Gemini.
    Returns JSON-like structured data as a string.
    """

    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
        Extract the quiz answers from the student's submission below.

        STRICTLY format the output as a JSON array of objects with the following schema:

        - Each object must include:
        - "question_no": integer
        - "answer": list of strings

        - Optional field:
        - "question_text": string

        JSON Schema:
        {{
        "type": "array",
        "items": {{
            "type": "object",
            "properties": {{
            "question_no": {{ "type": "integer" }},
            "question_text": {{ "type": "string" }},
            "answer": {{
                "type": "array",
                "items": {{ "type": "string" }}
            }}
            }},
            "required": ["question_no", "answer"]
        }}
        }}

        Submission:
        {raw_text}
        """


    response = model.generate_content(prompt)
    # response= extract_json_if_needed(response)

    print("response", response)
    try:
        json_start = response.text.find('[')
        json_text = response.text[json_start:].strip()
        json_text = json_text.replace("```","").replace("'''","")
        #json_text = extract_json_if_needed(response)
        return json.loads(json_text)
    except Exception as e:
        raise ValueError(f"Failed to parse JSON from model response: {e}\nRaw output:\n{response.text}")


async def evaluate_quiz(student_json: list, evaluation_json: list) -> dict:
    """
    Evaluates student answers against correct answers and returns:
    - awarded marks per question
    - total possible marks
    - total scored marks
    - total marks for each question from evaluation_json
    """
    results = []
    total_possible = 0
    total_scored = 0

    # Create a lookup for evaluation questions by question_no
    eval_lookup = {q["question_no"]: q for q in evaluation_json}

    for eval_q in evaluation_json:
        q_no = eval_q["question_no"]
        correct_answers = [a.strip().lower() for a in eval_q.get("correct_answer", [])]
        marks = eval_q.get("marks", 0)
        total_possible += marks

        # Find the corresponding student answer
        student_q = next((q for q in student_json if q.get("question_no") == q_no), None)
        student_answers = [a.strip().lower() for a in student_q.get("answer", [])] if student_q else []

        correct_matches = [a for a in student_answers if a in correct_answers]

        if set(correct_matches) == set(correct_answers):
            awarded = marks
            status = "correct"
        elif correct_matches:
            awarded = marks * 0.5
            status = "partially_correct"
        else:
            awarded = 0
            status = "incorrect"

        total_scored += awarded

        results.append({
            "question_no": q_no,
            "question_text": eval_q.get("question_text", ""),
            "total_marks": marks,
            "awarded_marks": awarded,
            "status": status,
            "student_answer": student_answers,
            "correct_answer": correct_answers
        })

    return {
        "question_results": results,
        "total_marks": total_possible,
        "scored_marks": total_scored
    }



    


