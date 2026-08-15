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


DIFFICULTY_OPTIONS = ["Easy", "Medium", "Hard"]
QUESTION_COUNT_OPTIONS = [3, 5, 10]
OPTION_LETTERS = ("A", "B", "C", "D")

COURSE_NAME = "INFO 4330: Data Warehousing & Data Mining (S10)"
TEAM_MEMBERS = ("Dilawar Singh", "Arvind Lahar", "Anmoldeep Singh")


st.set_page_config(
    page_title="QuizMate",
    page_icon=":material/quiz:",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def initialize_session_state() -> None:
    defaults = {
        "quiz_result": None,
        "quiz_difficulty": None,
        "quiz_submitted": False,
        "user_answers": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_answer_widgets() -> None:
    answer_keys = [
        key
        for key in st.session_state.keys()
        if key.startswith("answer_")
    ]

    for key in answer_keys:
        del st.session_state[key]


def reset_quiz_attempt() -> None:
    st.session_state.quiz_submitted = False
    st.session_state.user_answers = {}
    reset_answer_widgets()


def count_correct_answers(result: QuizGenerationResult) -> int:
    correct_count = 0

    for index, item in enumerate(result.quiz["questions"], start=1):
        if st.session_state.user_answers.get(index) == item["correct_answer"]:
            correct_count += 1

    return correct_count


def quiz_to_text(result: QuizGenerationResult) -> str:
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

        for option_letter in OPTION_LETTERS:
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
            "",
            COURSE_NAME,
            f"Created by {', '.join(TEAM_MEMBERS)}",
        ]
    )

    return "\n".join(lines)


def render_generator_panel() -> tuple[str, str, int, bool, bool]:
    study_material = st.text_area(
        "Study material",
        height=220,
        placeholder=(
            "Paste lecture notes, textbook sections, or anything "
            "you want to be quizzed on..."
        ),
        key="study_material",
    )

    character_count = len(study_material)
    excess_characters = character_count - MAX_STUDY_MATERIAL_LENGTH

    if excess_characters > 0:
        st.error(
            f"Remove {excess_characters:,} characters to fit the limit.",
            icon=":material/error:",
        )
    else:
        st.caption(
            f"{character_count:,} of {MAX_STUDY_MATERIAL_LENGTH:,} "
            f"characters · {MIN_STUDY_MATERIAL_LENGTH} minimum"
        )

    st.space("xsmall")

    difficulty = st.segmented_control(
        "Difficulty",
        options=DIFFICULTY_OPTIONS,
        default="Medium",
        required=True,
        width="stretch",
        key="difficulty",
    )

    number_of_questions = st.segmented_control(
        "Questions",
        options=QUESTION_COUNT_OPTIONS,
        default=5,
        required=True,
        width="stretch",
        key="question_count",
    )

    include_explanations = st.toggle(
        "Include answer explanations",
        value=True,
        key="include_explanations",
    )

    st.space("xsmall")

    generate_clicked = st.button(
        "Generate quiz",
        type="primary",
        icon=":material/auto_awesome:",
        width="stretch",
    )

    return (
        study_material,
        difficulty or "Medium",
        number_of_questions or 5,
        include_explanations,
        generate_clicked,
    )


def display_metadata(
    result: QuizGenerationResult,
    difficulty: str,
) -> None:
    with st.container(horizontal=True):
        st.metric(
            "Questions",
            len(result.quiz["questions"]),
            border=True,
        )

        st.metric(
            "Difficulty",
            difficulty,
            border=True,
        )

        st.metric(
            "Tokens",
            f"{result.total_tokens:,}",
            border=True,
            help="Total tokens used to generate this quiz.",
        )

        st.metric(
            "Time",
            f"{result.generation_time_seconds:.1f}s",
            border=True,
            help="Time the model took to respond.",
        )

    with st.expander("Generation details", icon=":material/info:"):
        st.markdown(f"**Model:** `{result.model}`")
        st.markdown(f"**Input tokens:** {result.input_tokens:,}")
        st.markdown(f"**Output tokens:** {result.output_tokens:,}")
        st.markdown(f"**Total tokens:** {result.total_tokens:,}")


def display_question(index: int, item: dict) -> None:
    is_submitted = st.session_state.quiz_submitted

    with st.container(border=True):
        st.badge(f"Question {index}", color="primary")

        st.markdown(f"### {item['question']}")

        option_labels = [
            f"{letter}. {item['options'][letter]}"
            for letter in OPTION_LETTERS
        ]

        previous_answer = st.session_state.user_answers.get(index)

        default_index = (
            OPTION_LETTERS.index(previous_answer)
            if previous_answer in OPTION_LETTERS
            else None
        )

        selected_option = st.radio(
            f"Answer for question {index}",
            options=option_labels,
            index=default_index,
            key=f"answer_{index}",
            disabled=is_submitted,
            label_visibility="collapsed",
            width="stretch",
        )

        if selected_option:
            st.session_state.user_answers[index] = selected_option[0]

        if not is_submitted:
            return

        correct_answer = item["correct_answer"]
        selected_answer = st.session_state.user_answers.get(index)

        if selected_answer == correct_answer:
            st.success(
                f"Correct. {correct_answer} is the right answer.",
                icon=":material/check_circle:",
            )
        else:
            st.error(
                f"You chose {selected_answer}. "
                f"The correct answer is {correct_answer}.",
                icon=":material/cancel:",
            )

        explanation = item["explanation"].strip()

        if explanation:
            st.info(explanation, icon=":material/lightbulb:")


def display_quiz_score(result: QuizGenerationResult) -> None:
    questions = result.quiz["questions"]
    correct_count = count_correct_answers(result)
    total_questions = len(questions)
    percentage = (correct_count / total_questions) * 100

    with st.container(border=True):
        st.subheader("Your result")

        with st.container(horizontal=True):
            st.metric(
                "Score",
                f"{correct_count} / {total_questions}",
                border=True,
            )

            st.metric(
                "Percentage",
                f"{percentage:.0f}%",
                border=True,
            )

        if percentage >= 80:
            st.success(
                "Excellent work. You have a strong grasp of this material.",
                icon=":material/trophy:",
            )
        elif percentage >= 60:
            st.info(
                "Good effort. Review the explanations and try again.",
                icon=":material/trending_up:",
            )
        else:
            st.warning(
                "Review the study material and explanations, then retry.",
                icon=":material/menu_book:",
            )

        if st.button(
            "Retake quiz",
            icon=":material/refresh:",
            width="stretch",
        ):
            reset_quiz_attempt()
            st.rerun()


def display_quiz(result: QuizGenerationResult) -> None:
    questions = result.quiz["questions"]

    st.subheader(result.quiz["title"])

    if not st.session_state.quiz_submitted:
        st.caption("Pick one answer for each question, then submit.")

    for index, item in enumerate(questions, start=1):
        display_question(index, item)

    if st.session_state.quiz_submitted:
        display_quiz_score(result)
        return

    answered_count = len(st.session_state.user_answers)

    st.progress(
        answered_count / len(questions),
        text=f"{answered_count} of {len(questions)} answered",
    )

    if st.button(
        "Submit quiz",
        type="primary",
        icon=":material/task_alt:",
        width="stretch",
    ):
        if answered_count < len(questions):
            st.warning(
                "Answer every question before submitting.",
                icon=":material/warning:",
            )
        else:
            st.session_state.quiz_submitted = True
            st.rerun()


initialize_session_state()

st.badge("AI-powered study tool", icon=":material/auto_awesome:", color="blue")
st.title("QuizMate")
st.caption(
    "Turn your study material into a multiple-choice quiz, "
    "test your knowledge, and review every answer."
)

st.space("small")

has_quiz = st.session_state.quiz_result is not None

if has_quiz:
    with st.expander("Create a new quiz", icon=":material/edit_note:"):
        (
            study_material,
            difficulty,
            number_of_questions,
            include_explanations,
            generate_clicked,
        ) = render_generator_panel()
else:
    with st.container(border=True):
        (
            study_material,
            difficulty,
            number_of_questions,
            include_explanations,
            generate_clicked,
        ) = render_generator_panel()

if generate_clicked:
    validation = validate_quiz_request(
        study_material=study_material,
        difficulty=difficulty,
        number_of_questions=number_of_questions,
    )

    if not validation.is_valid:
        st.error(validation.error_message, icon=":material/error:")
    else:
        try:
            with st.spinner("Generating your quiz...", show_time=True):
                result = generate_quiz(
                    study_material=study_material.strip(),
                    difficulty=difficulty,
                    number_of_questions=number_of_questions,
                    include_explanations=include_explanations,
                )

        except QuizGenerationError as error:
            st.error(str(error), icon=":material/error:")

        except Exception:
            st.error(
                "An unexpected error occurred. Please try again.",
                icon=":material/error:",
            )

        else:
            st.session_state.quiz_result = result
            st.session_state.quiz_difficulty = difficulty
            reset_quiz_attempt()
            st.toast("Your quiz is ready.", icon=":material/check_circle:")
            st.rerun()

quiz_result = st.session_state.quiz_result

if quiz_result is not None:
    st.space("small")

    display_metadata(
        result=quiz_result,
        difficulty=st.session_state.quiz_difficulty or "Medium",
    )

    display_quiz(quiz_result)

    st.space("xsmall")

    st.download_button(
        "Download quiz",
        data=quiz_to_text(quiz_result),
        file_name="quizmate_quiz.txt",
        mime="text/plain",
        icon=":material/download:",
        width="stretch",
    )

    with st.expander("Raw quiz JSON", icon=":material/data_object:"):
        st.json(quiz_result.quiz)

st.space("medium")

with st.container(border=True, horizontal_alignment="center"):
    st.caption("Course project by")
    st.markdown(f"**{' · '.join(TEAM_MEMBERS)}**")
    st.caption(COURSE_NAME)
    st.caption("QuizMate · Built with Python, Streamlit and the OpenAI API")
