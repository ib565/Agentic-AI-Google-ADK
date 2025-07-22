# Sahayak - Empowering Teachers in Multi-Grade Classrooms using AI Agents

An intelligent educational assistant that helps teachers create worksheets and lesson plans using AI agents powered by Google's Gemini model.

## Features

### 1. Worksheet Generator Agent
- **Input**: Textbook page images + grade level
- **Output**: Structured worksheets with fill-in-the-blank and short answer questions
- **Format**: PDF download
- **Capabilities**: 
  - Analyzes textbook content from images
  - Adapts difficulty based on grade level (1-12)
  - Creates 6-8 fill-in-the-blank questions
  - Creates 4-6 short answer questions
  - Generates educational content appropriate for the specified grade

### 2. Lesson Planner Agent
- **Input**: Text description from teacher (topic, grade, requirements)
- **Output**: Comprehensive lesson plans in text format
- **Format**: Text file download
- **Capabilities**:
  - Handles varying levels of detail in teacher input
  - Creates structured lesson plans with title, goals, and individual lessons
  - Each lesson includes: title, content, duration, lesson number
  - Adapts to different grade levels and subjects
  - Includes diverse teaching methods and activities

## API Endpoints

### Health Check
```
GET /
```
Returns API status.

### Generate Worksheet
```
POST /generate_worksheet_from_image
```
**Parameters:**
- `image` (file): Textbook page image (PNG, JPG, JPEG)
- `grade` (int): Grade level (1-12)

**Returns:** PDF file with generated worksheet

### Generate Lesson Plan
```
POST /generate_lesson_plan
```
**Parameters:**
- `teacher_requirements` (string): Description of lesson plan requirements

**Returns:** Text file with comprehensive lesson plan

## Installation

1. Clone the repository
```bash
git clone <repository-url>
cd "Agentic AI Google"
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file with your Google AI credentials:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

### Running the API Server
```bash
python main.py
```

The API will be available at `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

### Using the Lesson Planner Agent

#### Example 1: Simple topic
```
Input: "Solar system"
```

#### Example 2: Topic with grade level
```
Input: "Photosynthesis for 8th grade"
```

#### Example 3: Detailed requirements
```
Input: "Fractions and decimals for 4th grade, 5 lessons, 45 minutes each, include hands-on activities and games"
```

#### Example 4: Very specific request
```
Input: "American Revolution for 7th grade, 4 lessons, focus on causes and major battles, include primary source analysis and role-playing activities"
```

### Running Example Scripts
```bash
# Test the lesson planner with example inputs
python example_lesson_planner.py
```

## Project Structure

```
Agentic AI Google/
├── ai_engine/
│   ├── models.py              # Data models for structured output
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py     # PDF generation utilities
│   │   ├── worksheet_agent.py # Worksheet generation agent
│   │   └── lesson_planner_agent.py # Lesson planning agent
│   └── textbook.png          # Sample textbook image
├── main.py                   # FastAPI application
├── example_lesson_planner.py # Example usage script
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Lesson Plan Output Format

The lesson planner agent generates structured text output with the following format:

```
LESSON PLAN TITLE: [Creative, engaging title]
GRADE LEVEL: [Target grade]
TOTAL DURATION: [Overall timeframe]
LEARNING GOALS: [Clear, measurable objectives]
OVERVIEW: [Brief description of what students will learn]

LESSON BREAKDOWN:
Lesson 1: [Title]
Duration: [Time needed]
Content: [Detailed description of activities, concepts to cover, teaching methods]
Key Learning Points: [What students should understand]

Lesson 2: [Title]
Duration: [Time needed]
Content: [Detailed description of activities, concepts to cover, teaching methods]
Key Learning Points: [What students should understand]

[Additional lessons as needed...]
```

## Technologies Used

- **FastAPI**: Web framework for building APIs
- **Google AI SDK**: For agent development and Gemini model integration
- **Pydantic**: Data validation and parsing
- **Python 3.8+**: Core language

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]