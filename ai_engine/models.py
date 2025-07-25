from typing import List, Optional
from pydantic import BaseModel


# API Request Models
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


class AskSahayakRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "default_user"


class QuizRequest(BaseModel):
    subject: str
    grade: str
    topic: Optional[str] = None
    description: Optional[str] = None


# AI Output Models
class FillInTheBlankQuestion(BaseModel):
    question_text: str  # Text with blanks marked as _____ or [blank]
    answer: str  # The correct answer for the blank


class ShortAnswerQuestion(BaseModel):
    question: str  # The question text
    expected_answer: str  # Sample/expected answer (for teacher reference)


class WorksheetOutput(BaseModel):
    title: str
    grade_level: int
    subject: str
    fill_in_blanks: List[FillInTheBlankQuestion]
    short_answers: List[ShortAnswerQuestion]


class Lesson(BaseModel):
    lesson_number: int
    title: str
    duration: str
    content: str
    key_learning_points: str


class LessonPlanOutput(BaseModel):
    title: str
    grade_level: str
    total_duration: str
    learning_goals: str
    overview: str
    lessons: List[Lesson]


class StudySection(BaseModel):
    section_title: str
    content: str


class StudyMaterialOutput(BaseModel):
    title: str
    grade_level: str
    subject: str
    overview: str
    learning_objectives: str
    sections: List[StudySection]
    key_concepts: str
    practice_problems: str


class AskSahayakOutput(BaseModel):
    response: str
    session_id: str


class QuizQuestion(BaseModel):
    question_type: str
    question_no: int
    question_text: str
    options: List[str]
    answer: List[str]
    marks: float


class QuizOutput(BaseModel):
    number_of_questions: int
    total_marks: int
    questions: List[QuizQuestion]
