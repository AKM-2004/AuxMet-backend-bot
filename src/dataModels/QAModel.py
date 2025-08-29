from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from typing_extensions import TypedDict

class Output_(BaseModel):
    question: str = Field(description="The interview question to ask")
    difficulty: Literal["Easy", "Medium", "Hard"] = Field(description="Question difficulty level")
    technical_subject: str = Field(description="Main technical subject/skill being tested")
    technical_topic: str = Field(description="Specific topic or concept being evaluated")
    


class summarize_(BaseModel):
    summary: str = Field(description="detail summary of the given context")


class question_analysis(BaseModel):
    questions_asked: int = Field(
        description="Total number of questions asked from this domain/topic"
    )
    answered_correctly: int = Field(
        description="Number of questions answered correctly from this domain/topic"
    )
    answered_incorrectly: int = Field(
        description="Number of questions answered incorrectly from this domain/topic"
    )
    questions_skipped: int = Field(
        description="Number of questions skipped or not answered from this domain/topic"
    )
    partial_answers: int = Field(
        description="Number of questions with partially correct answers from this domain/topic"
    )


class domain_specific_result(TypedDict):
    domainName: str = Field(description="Name of the domain")
    Number_of_question: int = Field(
        description="The number of questions that are asked in that domain"
    )
    Number_of_answers_correct: int = Field(
        description="Number of questions that are correctly answered from particular domain"
    )
    Number_of_answers_incorrect: int = Field(
        description="Number of questions that are answered incorrectly from particular domain"
    )
    Number_of_skipped_questions: int = Field(
        description="Number of questions that are skipped from that particular domain"
    )


class validation_output(BaseModel):
    average_technical_skills_score: float = Field(
        description="Average technical score calculated as: (correct_answers + 0.5*partial_answers) / total_attempted_questions. Range: 0.0 to 1.0",
        ge=0.0,
        le=1.0,
    )
    domain_specific_technical_knowledge_score: List[domain_specific_result] = Field(
        description="List of the Domain-wise technical knowledge evaluation"
    )
    communication_skills_score: float = Field(
        description="Score based on clarity, fluency, articulation, and professional tone. Range: 1.0 to 10.0",
        ge=1.0,
        le=10.0,
    )
    question_understanding_score: float = Field(
        description="Score measuring how well the candidate comprehended and interpreted the questions. Range: 1.0 to 10.0",
        ge=1.0,
        le=10.0,
    )
    problem_solving_approach_score: float = Field(
        description="Score evaluating the candidate's thought process, logical reasoning, and problem-solving methodology. Range: 1.0 to 10.0",
        ge=1.0,
        le=10.0,
    )
    depth_of_knowledge_score: float = Field(
        description="Score measuring the depth and comprehensiveness of answers. Moderate depth: 8-10, Basic depth: 1-7. Range: 1.0 to 10.0",
        ge=1.0,
        le=10.0,
    )


class message_response(BaseModel):
    role: str
    content: str


class WrongQAItem(BaseModel):
    question: str = Field(description="The question text")
    wrong_answer: str = Field(description="The incorrect answer provided")
    topic: str = Field(
        description="The main topic/concept area this question belongs to"
    )
    subconcept: str = Field(description="The specific subconcept within the topic")


class OutputParse(BaseModel):
    wrong_qa: List[WrongQAItem] = Field(
        description="List of questions with wrong answers, including their topics and subconcepts"
    )
