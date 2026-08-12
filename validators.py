from dataclasses import dataclass


MIN_STUDY_MATERIAL_LENGTH = 100
MAX_STUDY_MATERIAL_LENGTH = 15_000
ALLOWED_DIFFICULTIES = {"Easy", "Medium", "Hard"}
ALLOWED_QUESTION_COUNTS = {3, 5, 10}


@dataclass
class ValidationResult:
    """
    Represents the result of validating user input.
    """

    is_valid: bool
    error_message: str = ""


def validate_study_material(study_material: str) -> ValidationResult:
    """
    Validate the study material entered by the user.
    """
    if not isinstance(study_material, str):
        return ValidationResult(
            is_valid=False,
            error_message="Study material must be text.",
        )

    cleaned_material = study_material.strip()

    if not cleaned_material:
        return ValidationResult(
            is_valid=False,
            error_message="Please enter study material before generating a quiz.",
        )

    if len(cleaned_material) < MIN_STUDY_MATERIAL_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Please provide at least "
                f"{MIN_STUDY_MATERIAL_LENGTH} characters of study material."
            ),
        )

    if len(cleaned_material) > MAX_STUDY_MATERIAL_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Study material must be "
                f"{MAX_STUDY_MATERIAL_LENGTH:,} characters or fewer."
            ),
        )

    return ValidationResult(is_valid=True)


def validate_difficulty(difficulty: str) -> ValidationResult:
    """
    Validate the selected quiz difficulty.
    """
    if difficulty not in ALLOWED_DIFFICULTIES:
        return ValidationResult(
            is_valid=False,
            error_message="Please select Easy, Medium, or Hard difficulty.",
        )

    return ValidationResult(is_valid=True)


def validate_question_count(number_of_questions: int) -> ValidationResult:
    """
    Validate the selected number of quiz questions.
    """
    if number_of_questions not in ALLOWED_QUESTION_COUNTS:
        return ValidationResult(
            is_valid=False,
            error_message="The quiz must contain 3, 5, or 10 questions.",
        )

    return ValidationResult(is_valid=True)


def validate_quiz_request(
    study_material: str,
    difficulty: str,
    number_of_questions: int,
) -> ValidationResult:
    """
    Validate all quiz-generation inputs.
    """
    validations = [
        validate_study_material(study_material),
        validate_difficulty(difficulty),
        validate_question_count(number_of_questions),
    ]

    for result in validations:
        if not result.is_valid:
            return result

    return ValidationResult(is_valid=True)

if __name__ == "__main__":
    test_cases = [
        {
            "name": "Empty input",
            "material": "",
            "difficulty": "Medium",
            "question_count": 5,
        },
        {
            "name": "Input too short",
            "material": "Data warehouses store data.",
            "difficulty": "Medium",
            "question_count": 5,
        },
        {
            "name": "Invalid difficulty",
            "material": "A" * 150,
            "difficulty": "Extreme",
            "question_count": 5,
        },
        {
            "name": "Valid input",
            "material": "A" * 150,
            "difficulty": "Medium",
            "question_count": 5,
        },
    ]

    for test_case in test_cases:
        result = validate_quiz_request(
            study_material=test_case["material"],
            difficulty=test_case["difficulty"],
            number_of_questions=test_case["question_count"],
        )

        print(f"\n{test_case['name']}")
        print(f"Valid: {result.is_valid}")
        print(f"Message: {result.error_message or 'No errors'}")