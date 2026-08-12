import json
from typing import Any

import streamlit as st

from ai_service import (
    QuizGenerationError,
    QuizGenerationResult,
    generate_quiz,
)
from validators import (
    MAX_STUDY_MATERIAL_LENGTH,
    MIN_STUDY_MATERIAL_LENGTH,
    validate_quiz_request,
)


st.set_page_config(
    page_title="StudyForge",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state() -> None:
    """
    Initialize values that remain available across Streamlit reruns.
    """
    defaults = {
        "quiz_result": None,
        "quiz_difficulty": None,
        "quiz_submitted": False,
        "user_answers": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_custom_css() -> None:
    """
    Apply lightweight styling to the Streamlit interface.
    """
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.6rem;
            font-weight: 750;
            margin-bottom: 0;
        }

        .subtitle {
            font-size: 1.1rem;
            opacity: 0.75;
            margin-top: 0.2rem;
            margin-bottom: 2rem;
        }

        .question-card {
            border: 1px solid rgba(128, 128, 128, 0.28);
            border-radius: 14px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }

        .option-row {
            padding: 0.45rem 0;
        }

        .metadata-label {
            font-size: 0.85rem;
            opacity: 0.7;
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.22);
            border-radius: 12px;
            padding: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def quiz_to_text(result: QuizGenerationResult) -> str:
    """
    Convert a generated quiz into a downloadable text document.
    """
    quiz = result.quiz

    lines = [
        quiz["title"],
        "=" * len(quiz["title"]),
        "",
    ]

    for index, item in enumerate(quiz["questions"], start=1):
        lines.append(f"Question {index}")
        lines.append(item["question"])
        lines.append("")

        for option_letter in ("A", "B", "C", "D"):
            lines.append(
                f"{option_letter}. {item['options'][option_letter]}"
            )

        lines.append("")
        lines.append(
            f"Correct Answer: {item['correct_answer']}"
        )

        if item["explanation"].strip():
            lines.append(
                f"Explanation: {item['explanation']}"
            )

        lines.extend(["", "-" * 60, ""])

    lines.extend(
        [
            "Generation Metadata",
            f"Model: {result.model}",
            f"Input tokens: {result.input_tokens}",
            f"Output tokens: {result.output_tokens}",
            f"Total tokens: {result.total_tokens}",
            (
                "Generation time: "
                f"{result.generation_time_seconds:.2f} seconds"
            ),
        ]
    )

    return "\n".join(lines)


def display_metadata(
    result: QuizGenerationResult,
    difficulty: str,
) -> None:
    """
    Display quiz-generation metadata.
    """
    st.subheader("Generation details")

    column1, column2, column3, column4 = st.columns(4)

    column1.metric(
        "Questions",
        len(result.quiz["questions"]),
    )

    column2.metric(
        "Difficulty",
        difficulty,
    )

    column3.metric(
        "Total tokens",
        f"{result.total_tokens:,}",
    )

    column4.metric(
        "Generation time",
        f"{result.generation_time_seconds:.2f}s",
    )

    with st.expander("View detailed API metadata"):
        metadata_column1, metadata_column2 = st.columns(2)

        with metadata_column1:
            st.write(f"**Model:** `{result.model}`")
            st.write(
                f"**Input tokens:** {result.input_tokens:,}"
            )

        with metadata_column2:
            st.write(
                f"**Output tokens:** {result.output_tokens:,}"
            )
            st.write(
                f"**Total tokens:** {result.total_tokens:,}"
            )


def display_quiz(result: QuizGenerationResult) -> None:
    """
    Display an interactive multiple-choice quiz.
    """
    quiz = result.quiz
    questions = quiz["questions"]

    st.divider()
    st.header(quiz["title"])

    if not st.session_state.quiz_submitted:
        st.info(
            "Select one answer for each question, then click "
            "**Submit quiz**."
        )

    for index, item in enumerate(questions, start=1):
        question_key = f"question_{index}"

        with st.container(border=True):
            st.subheader(f"Question {index}")
            st.markdown(f"**{item['question']}**")

            option_labels = []

            for option_letter in ("A", "B", "C", "D"):
                option_text = item["options"][option_letter]
                option_labels.append(
                    f"{option_letter}. {option_text}"
                )

            previous_answer = st.session_state.user_answers.get(
                question_key
            )

            default_index = None

            if previous_answer:
                for option_index, label in enumerate(option_labels):
                    if label.startswith(f"{previous_answer}."):
                        default_index = option_index
                        break

            selected_option = st.radio(
                label=f"Choose an answer for question {index}",
                options=option_labels,
                index=default_index,
                key=question_key,
                disabled=st.session_state.quiz_submitted,
                label_visibility="collapsed",
            )

            if selected_option:
                selected_letter = selected_option[0]
                st.session_state.user_answers[
                    question_key
                ] = selected_letter

            if st.session_state.quiz_submitted:
                selected_answer = (
                    st.session_state.user_answers.get(question_key)
                )
                correct_answer = item["correct_answer"]

                if selected_answer == correct_answer:
                    st.success(
                        f"Correct — the answer is {correct_answer}."
                    )
                else:
                    if selected_answer:
                        st.error(
                            f"Your answer: {selected_answer}. "
                            f"Correct answer: {correct_answer}."
                        )
                    else:
                        st.warning(
                            f"No answer selected. "
                            f"Correct answer: {correct_answer}."
                        )

                if item["explanation"].strip():
                    st.info(
                        f"Explanation: {item['explanation']}"
                    )

    if not st.session_state.quiz_submitted:
        answered_count = len(
            st.session_state.user_answers
        )

        st.caption(
            f"Answered: {answered_count} of {len(questions)}"
        )

        if st.button(
            "Submit quiz",
            type="primary",
            use_container_width=True,
            icon="✅",
        ):
            if answered_count < len(questions):
                st.warning(
                    "Please answer every question before submitting."
                )
            else:
                st.session_state.quiz_submitted = True
                st.rerun()

    else:
        display_quiz_score(result)

        if st.button(
            "Retake quiz",
            use_container_width=True,
            icon="🔄",
        ):
            reset_quiz_attempt()
            st.rerun()

def display_quiz_score(
    result: QuizGenerationResult,
) -> None:
    """
    Calculate and display the user's quiz score.
    """
    questions = result.quiz["questions"]
    correct_count = 0

    for index, item in enumerate(questions, start=1):
        question_key = f"question_{index}"

        selected_answer = (
            st.session_state.user_answers.get(question_key)
        )

        if selected_answer == item["correct_answer"]:
            correct_count += 1

    total_questions = len(questions)
    percentage = (
        correct_count / total_questions
    ) * 100

    st.divider()
    st.subheader("Quiz results")

    score_column, percentage_column = st.columns(2)

    score_column.metric(
        "Score",
        f"{correct_count} / {total_questions}",
    )

    percentage_column.metric(
        "Percentage",
        f"{percentage:.0f}%",
    )

    if percentage >= 80:
        st.success("Excellent work!")
    elif percentage >= 60:
        st.info("Good effort. Review the explanations and try again.")
    else:
        st.warning(
            "Keep studying and review the explanations before retrying."
        )

def reset_quiz_attempt() -> None:
    """
    Reset answers while keeping the generated quiz.
    """
    st.session_state.quiz_submitted = False
    st.session_state.user_answers = {}

    question_keys = [
        key
        for key in st.session_state.keys()
        if key.startswith("question_")
    ]

    for key in question_keys:
        del st.session_state[key]

def display_sidebar() -> tuple[str, int, bool, bool]:
    """
    Display quiz configuration controls in the sidebar.
    """
    with st.sidebar:
        st.header("Quiz settings")

        difficulty = st.selectbox(
            "Difficulty",
            options=["Easy", "Medium", "Hard"],
            index=1,
            help="Controls the complexity of generated questions.",
        )

        number_of_questions = st.selectbox(
            "Number of questions",
            options=[3, 5, 10],
            index=1,
        )

        include_explanations = st.checkbox(
            "Include explanations",
            value=True,
        )


        st.divider()

        st.caption(
            "StudyForge uses the OpenAI API to generate "
            "questions from the material you provide."
        )

    return (
        difficulty,
        number_of_questions,
        include_explanations
    )


def main() -> None:
    """
    Run the StudyForge application.
    """
    initialize_session_state()
    apply_custom_css()

    (
        difficulty,
        number_of_questions,
        include_explanations
    ) = display_sidebar()

    st.markdown(
        '<p class="main-title">📚 StudyForge</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<p class="subtitle">'
            "Turn your study material into an AI-generated "
            "multiple-choice quiz."
            "</p>"
        ),
        unsafe_allow_html=True,
    )

    study_material = st.text_area(
        "Study material",
        height=300,
        placeholder=(
            "Paste lecture notes, textbook content, "
            "or other study material here..."
        ),
        help=(
            f"Enter between {MIN_STUDY_MATERIAL_LENGTH} and "
            f"{MAX_STUDY_MATERIAL_LENGTH:,} characters."
        ),
    )

    character_count = len(study_material)

    count_column, limit_column = st.columns([1, 3])

    with count_column:
        st.caption(
            f"Characters: {character_count:,}"
        )

    with limit_column:
        remaining = (
            MAX_STUDY_MATERIAL_LENGTH - character_count
        )

        if remaining >= 0:
            st.caption(
                f"Remaining: {remaining:,}"
            )
        else:
            st.error(
                f"Input exceeds the limit by "
                f"{abs(remaining):,} characters."
            )

    generate_clicked = st.button(
        "Generate quiz",
        type="primary",
        use_container_width=True,
        icon="✨",
    )

    if generate_clicked:
        validation = validate_quiz_request(
            study_material=study_material,
            difficulty=difficulty,
            number_of_questions=number_of_questions,
        )

        if not validation.is_valid:
            st.error(validation.error_message)

        else:
            try:
                with st.spinner(
                    "Creating your quiz with OpenAI..."
                ):
                    result = generate_quiz(
                        study_material=study_material.strip(),
                        difficulty=difficulty,
                        number_of_questions=number_of_questions,
                        include_explanations=include_explanations,
                    )

                st.session_state.quiz_result = result
                st.session_state.quiz_difficulty = difficulty
                st.session_state.quiz_submitted = False
                st.session_state.user_answers = {}

                question_keys = [
                    key
                    for key in st.session_state.keys()
                    if key.startswith("question_")
                ]

                for key in question_keys:
                    del st.session_state[key]

                st.success(
                    "Your quiz was generated successfully."
                )

            except QuizGenerationError as error:
                st.error(str(error))

            except Exception:
                st.error(
                    "An unexpected error occurred. "
                    "Please try again."
                )

    result = st.session_state.quiz_result

    if result is not None:
        stored_difficulty = st.session_state.get(
            "quiz_difficulty",
            difficulty,
        )

        display_metadata(
            result=result,
            difficulty=stored_difficulty,
        )

        display_quiz(result)

        quiz_text = quiz_to_text(result)

        st.download_button(
            label="Download quiz as text",
            data=quiz_text,
            file_name="studyforge_quiz.txt",
            mime="text/plain",
            use_container_width=True,
            icon=":material/download:",
        )

        with st.expander("View raw quiz JSON"):
            st.json(result.quiz)


if __name__ == "__main__":
    main()