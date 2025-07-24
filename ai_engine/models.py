from typing import List
from pydantic import BaseModel


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
