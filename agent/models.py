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
