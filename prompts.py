def build_quiz_prompt(
    study_material: str,
    difficulty: str,
    number_of_questions: int,
    include_explanations: bool,
) -> str:
    """
    Build the prompt used to generate multiple-choice quiz content.

    OpenAI generates the question, one correct answer, and three
    incorrect answers. Python will later randomize their positions.
    """

    explanation_instruction = (
        "Include a short explanation for every correct answer."
        if include_explanations
        else "Use an empty string for every explanation."
    )

    return f"""
You are an academic quiz-generation assistant.

Create a multiple-choice quiz using only the study material provided below.

QUIZ REQUIREMENTS:
- Generate exactly {number_of_questions} questions.
- Difficulty level: {difficulty}.
- Each question must have exactly one correct answer.
- Each question must have exactly three incorrect answers.
- Incorrect answers must be believable but clearly incorrect.
- Avoid duplicate or nearly identical questions.
- Do not use information that is not supported by the study material.
- {explanation_instruction}

IMPORTANT:
- Do not assign answer letters such as A, B, C, or D.
- Do not create an options object.
- Provide the correct answer as text.
- Provide the three incorrect answers as a list.
- Python will randomize the answer positions later.

Return only valid JSON using this exact structure:

{{
  "title": "A short title for the quiz",
  "questions": [
    {{
      "question": "Question text",
      "correct_answer": "The correct answer text",
      "incorrect_answers": [
        "First incorrect answer",
        "Second incorrect answer",
        "Third incorrect answer"
      ],
      "explanation": "Short explanation, or an empty string if explanations are disabled"
    }}
  ]
}}

STUDY MATERIAL:
{study_material}
""".strip()