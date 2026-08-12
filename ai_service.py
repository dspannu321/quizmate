import json
import os
import time
from dataclasses import dataclass
from typing import Any
import random

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

from prompts import build_quiz_prompt


load_dotenv()


class QuizGenerationError(Exception):
    """Raised when StudyForge cannot generate a valid quiz."""


@dataclass
class QuizGenerationResult:
    """
    Contains the generated quiz and API request metadata.
    """

    quiz: dict[str, Any]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    generation_time_seconds: float
    model: str


def create_client() -> OpenAI:
    """
    Create an OpenAI client using the API key from .env.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise QuizGenerationError(
            "OPENAI_API_KEY was not found. Add it to the .env file."
        )

    return OpenAI(api_key=api_key)


def generate_quiz(
    study_material: str,
    difficulty: str = "Medium",
    number_of_questions: int = 5,
    include_explanations: bool = True,
) -> QuizGenerationResult:
    """
    Generate a multiple-choice quiz and return the quiz with metadata.
    """
    prompt = build_quiz_prompt(
        study_material=study_material,
        difficulty=difficulty,
        number_of_questions=number_of_questions,
        include_explanations=include_explanations,
    )

    model_name = "gpt-5-mini"

    try:
        client = create_client()

        start_time = time.perf_counter()

        response = client.responses.create(
            model=model_name,
            input=prompt,
        )

        elapsed_time = time.perf_counter() - start_time

        raw_output = response.output_text.strip()

        if not raw_output:
            raise QuizGenerationError(
                "OpenAI returned an empty response."
            )

        cleaned_output = remove_json_code_fences(raw_output)
        quiz = json.loads(cleaned_output)

        validate_ai_quiz_structure(
            quiz=quiz,
            expected_question_count=number_of_questions,
        )

        quiz = randomize_quiz_options(quiz)

        validate_quiz_structure(
            quiz=quiz,
            expected_question_count=number_of_questions,
        )

        usage = response.usage

        return QuizGenerationResult(
            quiz=quiz,
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            generation_time_seconds=elapsed_time,
            model=model_name,
        )

    except AuthenticationError as error:
        raise QuizGenerationError(
            "Authentication failed. Please check your OpenAI API key."
        ) from error

    except RateLimitError as error:
        raise QuizGenerationError(
            "The request was rate-limited, or the API account may "
            "not have sufficient credits."
        ) from error

    except APIConnectionError as error:
        raise QuizGenerationError(
            "Unable to connect to OpenAI. Check your internet connection."
        ) from error

    except APIError as error:
        raise QuizGenerationError(
            f"OpenAI API error: {error}"
        ) from error

    except json.JSONDecodeError as error:
        raise QuizGenerationError(
            "OpenAI returned a response that was not valid JSON."
        ) from error


def remove_json_code_fences(text: str) -> str:
    """
    Remove optional Markdown code fences from JSON output.
    """
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()
def validate_ai_quiz_structure(
    quiz: dict[str, Any],
    expected_question_count: int,
) -> None:
    """
    Validate the raw quiz structure returned by OpenAI
    before Python randomizes the answer positions.
    """
    if not isinstance(quiz, dict):
        raise QuizGenerationError(
            "The generated quiz is not a valid JSON object."
        )

    title = quiz.get("title")

    if not isinstance(title, str) or not title.strip():
        raise QuizGenerationError(
            "The generated quiz does not contain a valid title."
        )

    questions = quiz.get("questions")

    if not isinstance(questions, list):
        raise QuizGenerationError(
            "The generated quiz does not contain a question list."
        )

    if len(questions) != expected_question_count:
        raise QuizGenerationError(
            f"Expected {expected_question_count} questions, "
            f"but received {len(questions)}."
        )

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise QuizGenerationError(
                f"Question {index} is invalid."
            )

        question_text = question.get("question")

        if not isinstance(question_text, str) or not question_text.strip():
            raise QuizGenerationError(
                f"Question {index} has no valid question text."
            )

        correct_answer = question.get("correct_answer")

        if not isinstance(correct_answer, str) or not correct_answer.strip():
            raise QuizGenerationError(
                f"Question {index} has no valid correct answer."
            )

        incorrect_answers = question.get("incorrect_answers")

        if not isinstance(incorrect_answers, list):
            raise QuizGenerationError(
                f"Question {index} has no valid incorrect-answer list."
            )

        if len(incorrect_answers) != 3:
            raise QuizGenerationError(
                f"Question {index} must contain exactly "
                "three incorrect answers."
            )

        if not all(
            isinstance(answer, str) and answer.strip()
            for answer in incorrect_answers
        ):
            raise QuizGenerationError(
                f"Question {index} contains an invalid incorrect answer."
            )

        all_answers = [
            correct_answer.strip(),
            *[answer.strip() for answer in incorrect_answers],
        ]

        if len(set(all_answers)) != 4:
            raise QuizGenerationError(
                f"Question {index} contains duplicate answer choices."
            )

        explanation = question.get("explanation")

        if not isinstance(explanation, str):
            raise QuizGenerationError(
                f"Question {index} has an invalid explanation."
            )
            
def randomize_quiz_options(
    quiz: dict[str, Any],
) -> dict[str, Any]:
    """
    Randomize the correct and incorrect answer positions.

    The AI returns one correct answer and three incorrect answers.
    This function shuffles them and creates options A, B, C, and D.
    """

    option_letters = ("A", "B", "C", "D")

    for question in quiz["questions"]:
        correct_answer_text = question["correct_answer"]
        incorrect_answers = question["incorrect_answers"]

        all_answers = [
            correct_answer_text,
            *incorrect_answers,
        ]

        random.shuffle(all_answers)

        question["options"] = {
            letter: answer
            for letter, answer in zip(option_letters, all_answers)
        }

        question["correct_answer"] = next(
            letter
            for letter, answer in question["options"].items()
            if answer == correct_answer_text
        )

        del question["incorrect_answers"]

    return quiz

def validate_quiz_structure(
    quiz: dict[str, Any],
    expected_question_count: int,
) -> None:
    """
    Validate the top-level quiz structure.
    """
    if not isinstance(quiz, dict):
        raise QuizGenerationError(
            "The generated quiz is not a valid JSON object."
        )

    title = quiz.get("title")

    if not isinstance(title, str) or not title.strip():
        raise QuizGenerationError(
            "The generated quiz does not contain a valid title."
        )

    questions = quiz.get("questions")

    if not isinstance(questions, list):
        raise QuizGenerationError(
            "The generated quiz does not contain a question list."
        )

    if len(questions) != expected_question_count:
        raise QuizGenerationError(
            f"Expected {expected_question_count} questions, "
            f"but received {len(questions)}."
        )

    for index, question in enumerate(questions, start=1):
        validate_question(question, index)


def validate_question(
    question: dict[str, Any],
    question_number: int,
) -> None:
    """
    Validate one generated multiple-choice question.
    """
    if not isinstance(question, dict):
        raise QuizGenerationError(
            f"Question {question_number} is invalid."
        )

    question_text = question.get("question")

    if not isinstance(question_text, str) or not question_text.strip():
        raise QuizGenerationError(
            f"Question {question_number} has no valid question text."
        )

    options = question.get("options")

    if not isinstance(options, dict):
        raise QuizGenerationError(
            f"Question {question_number} has no valid options."
        )

    required_options = {"A", "B", "C", "D"}

    if set(options.keys()) != required_options:
        raise QuizGenerationError(
            f"Question {question_number} must contain "
            "options A, B, C, and D."
        )

    if not all(
        isinstance(value, str) and value.strip()
        for value in options.values()
    ):
        raise QuizGenerationError(
            f"Question {question_number} contains an invalid option."
        )

    if question.get("correct_answer") not in required_options:
        raise QuizGenerationError(
            f"Question {question_number} has an invalid correct answer."
        )

    if not isinstance(question.get("explanation"), str):
        raise QuizGenerationError(
            f"Question {question_number} has an invalid explanation."
        )