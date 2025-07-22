# Worksheet Generator API

A FastAPI service that generates educational worksheets from textbook images using Google's Gemini AI.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables (create a `.env` file):
```
GOOGLE_API_KEY=your_google_api_key_here
```

3. Run the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## Usage

### API Endpoint

**POST** `/generate_worksheet_from_image`

Upload a textbook image and specify a grade level to generate a PDF worksheet.

**Parameters:**
- `image`: Image file (PNG, JPG, JPEG)
- `grade`: Grade level (1-12)

**Response:** PDF file download

### Example with curl

```bash
curl -X POST "http://localhost:8000/generate_worksheet_from_image" \
  -F "image=@path/to/textbook.png" \
  -F "grade=6" \
  --output worksheet_grade_6.pdf
```

### Interactive API Documentation

Visit `http://localhost:8000/docs` for the interactive Swagger UI where you can test the API directly.

## Features

- Generate fill-in-the-blank questions (6-8 per worksheet)
- Generate short answer questions (4-6 per worksheet)
- Grade-appropriate difficulty levels (1-12)
- Professional PDF formatting
- Fast API with automatic documentation

## File Structure

- `main.py` - FastAPI application and endpoints
- `agent/models.py` - Pydantic models for worksheet structure
- `agent/services/worksheet_service.py` - Core worksheet generation logic
- `agent/services/pdf_service.py` - PDF generation and formatting
