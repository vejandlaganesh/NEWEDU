from pydantic import BaseModel, Field
from typing import List, Optional

class QuizQuestionSchema(BaseModel):
    question_text: str = Field(description="The text of the multiple choice question.")
    option_a: str = Field(description="Option A text.")
    option_b: str = Field(description="Option B text.")
    option_c: str = Field(description="Option C text.")
    option_d: str = Field(description="Option D text.")
    correct_option: str = Field(description="The correct option letter. Must be exactly 'A', 'B', 'C', or 'D'.")
    explanation: str = Field(description="Explanation of why the correct option is correct.")
    marks: int = Field(default=1, description="Number of marks this question is worth.")

class GeneratedQuizSchema(BaseModel):
    title: str = Field(description="A catchy, relevant title for the quiz.")
    description: str = Field(description="A brief description of what the quiz covers.")
    questions: List[QuizQuestionSchema] = Field(description="List of multiple-choice questions for the quiz.")

class GeneratedQuestionsSchema(BaseModel):
    questions: List[QuizQuestionSchema] = Field(description="List of standalone multiple-choice questions.")

class GeneratedExplanationSchema(BaseModel):
    concept: str = Field(description="The core concept being explained.")
    explanation: str = Field(description="The detailed explanation text.")
    key_takeaways: List[str] = Field(description="A list of 3-5 key takeaways from the explanation.")

class GeneratedSummarySchema(BaseModel):
    summary: str = Field(description="A concise summary of the provided text.")
    topics_covered: List[str] = Field(description="List of main topics covered in the text.")

class LearningRecommendationSchema(BaseModel):
    strengths: List[str] = Field(description="Topics or areas where the student is performing well.")
    weaknesses: List[str] = Field(description="Topics or areas where the student needs improvement.")
    recommended_topics: List[str] = Field(description="Specific topics from the provided context that the student should review.", default=[])
    actionable_advice: List[str] = Field(description="Specific, actionable steps the student can take to improve.")
    encouragement_message: str = Field(description="A short encouraging message for the student.")

class GeneratedContentSchema(BaseModel):
    title: str = Field(description="The title of the generated content.")
    content: str = Field(description="The full generated content body, formatted using Markdown for readability.")
