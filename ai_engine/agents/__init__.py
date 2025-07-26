"""
AI Agents Module

This module contains specialized AI agents for educational content generation:
- BaseAgent: Common functionality for all educational agents
- WorksheetAgent: Generates educational worksheets from textbook images
- LessonPlannerAgent: Creates comprehensive lesson plans
- StudyMaterialAgent: Produces detailed study materials
- AskSahayakAgent: A multilingual conversational assistant that maintains context across conversations.
- QuizAgent: Generates quizzes and assessments
- VisualAidDesignerAgent: Creates visual aids and diagrams using Mermaid
"""

__all__ = [
    "BaseAgent",
    "generate_worksheet_from_image",
    "generate_lesson_plan",
    "generate_study_material",
    "generate_quiz",
    "ask_sahayak_question",
    "generate_visual_aid",
]
