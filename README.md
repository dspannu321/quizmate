# QuizMate

**AI-Powered Quiz Generator Using the OpenAI API**

QuizMate is a Python web application that transforms study material into interactive multiple-choice quizzes using Generative AI. Users can paste their notes or other study content, select the quiz difficulty and number of questions, generate a quiz, attempt it, and receive immediate scoring and explanations.

This project was developed for the **Generative AI Topic Group Project** as part of the Data Warehouse and Data Mining course.

---

## Features

- Generate multiple-choice quizzes from user-provided study material
- Easy, Medium, and Hard difficulty levels
- Generate 3, 5, or 10 questions
- Four answer choices per question
- Optional answer explanations
- Interactive quiz interface
- Automatic scoring
- Correct and incorrect answer feedback
- Retake generated quizzes
- Randomized answer positions using Python
- Input validation
- OpenAI API and runtime error handling
- API token usage display
- Quiz generation time display
- Download generated quizzes as text
- Structured JSON processing

---

## Technology Stack


| Technology    | Purpose                           |
| ------------- | --------------------------------- |
| Python        | Core application language         |
| Streamlit     | Web application interface         |
| OpenAI API    | Generative AI quiz creation       |
| python-dotenv | Environment variable management   |
| JSON          | Structured AI response processing |


---

## How QuizMate Works

The application follows this workflow:

**Study Material → Input Validation → Prompt Generation → OpenAI API → Structured JSON → Response Validation → Python Answer Randomization → Interactive Quiz → Scoring & Feedback**

The OpenAI model is responsible for generating the educational content, including:

- Question text
- Correct answer
- Three incorrect answers
- Optional explanation

Python handles deterministic application logic such as:

- Input validation
- Response validation
- Answer randomization
- A/B/C/D assignment
- Quiz scoring
- User interaction
- Error handling

This separation prevents the Generative AI model from controlling application logic that can be handled more reliably by Python.

---

## Project Structure

```text
QuizMate/
│
├── app.py
├── ai_service.py
├── prompts.py
├── validators.py
├── requirements.txt
├── README.md
├── .env
├── .env.example
└── .gitignore

```

### `app.py`

Contains the Streamlit web interface and handles:

- User input
- Quiz settings
- Quiz display
- User answers
- Session state
- Quiz submission
- Scoring
- Feedback
- Generation metadata
- Quiz download

### `ai_service.py`

Handles communication with the OpenAI API and includes:

- OpenAI client creation
- API requests
- JSON processing
- AI response validation
- Answer randomization
- API error handling
- Token usage
- Generation-time measurement

### `prompts.py`

Builds the structured prompt sent to the OpenAI API based on:

- Study material
- Difficulty
- Number of questions
- Explanation preference

### `validators.py`

Validates user input before an OpenAI API request is made.

---

# Installation

## 1. Download or Clone the Project

Clone the repository or download the source-code folder.

```bash
git clone https://github.com/dspannu321/quizmate
cd QuizMate

```

If the project was downloaded manually, open a terminal inside the QuizMate directory.

---

## 2. Create a Python Virtual Environment

```bash
python -m venv .venv

```

### Windows

Activate the environment using:

```powershell
.\.venv\Scripts\Activate.ps1

```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt

```

---

## 4. Configure the OpenAI API Key

Create a `.env` file in the root project directory.

Add:

```env
OPENAI_API_KEY=your_openai_api_key_here

```

Replace `your_openai_api_key_here` with a valid OpenAI API key.

**Do not commit the** `.env` **file to GitHub or share your API key.**

An `.env.example` file is included to demonstrate the required configuration without exposing a real API key.

---

## 5. Run QuizMate

Start the Streamlit application:

```bash
streamlit run app.py

```

Streamlit will display a local address, normally:

```text
http://localhost:8501

```

Open this address in a web browser if it does not open automatically.

---

# Using QuizMate

1. Paste study material into the Study Material field.
2. Select a difficulty level.
3. Select the desired number of questions.
4. Choose whether explanations should be generated.
5. Click **Generate Quiz**.
6. Wait for the OpenAI API to generate the quiz.
7. Select an answer for each question.
8. Click **Submit Quiz**.
9. Review the score, correct answers, and explanations.
10. Retake or download the quiz if desired.

---

# Prompt Design

QuizMate does not simply ask the model to "generate a quiz."

The prompt provides specific requirements, including:

- Exact number of questions
- Selected difficulty
- One correct answer per question
- Exactly three incorrect answers
- Believable incorrect answers
- No duplicate questions
- Questions grounded in the supplied study material
- Optional explanations
- Structured JSON output

The model does **not** assign A, B, C, or D positions.

Instead, the model returns one correct answer and three incorrect answers. Python then randomly shuffles these answers and assigns the letters A through D.

---

# Answer Randomization

During development, testing showed that allowing the Generative AI model to assign answer letters could result in the correct answer appearing repeatedly in the same position.

The application was redesigned so that OpenAI generates only the answer content.

Python then performs:

```python
random.shuffle(all_answers)

```

After shuffling, QuizMate assigns A, B, C, and D and determines the new location of the correct answer.

This ensures that answer positioning is controlled by application logic rather than relying on the language model for randomization.

---

# Input Validation

QuizMate validates input before making an API request.

Examples include:

- Empty study material
- Study material below the minimum length
- Study material exceeding the maximum length
- Invalid difficulty
- Invalid number of questions

This prevents unnecessary API requests when the input is invalid.

---

# Error Handling

QuizMate includes handling for several runtime and API errors, including:

- Missing OpenAI API key
- Invalid authentication
- API rate limits
- Insufficient API availability or credits
- Network connection problems
- OpenAI API errors
- Invalid JSON responses
- Invalid generated quiz structures
- Unexpected runtime errors

Errors are displayed to the user through the application instead of causing the program to fail without explanation.

---

# Test Cases

## Test Case 1 — Valid Study Material

**Input:** Valid study material containing more than 100 characters.

**Settings:**

- Difficulty: Medium
- Questions: 5
- Explanations: Enabled

**Expected Result:** QuizMate generates five multiple-choice questions and allows the user to complete and submit the quiz.

**Result:** PASS

---

## Test Case 2 — Empty Input

**Input:** No study material.

**Expected Result:** QuizMate displays a validation message requesting study material and does not send an unnecessary API request.

**Result:** PASS

---

## Test Case 3 — Input Below Minimum Length

**Input:** Study material containing fewer than 100 characters.

**Expected Result:** QuizMate informs the user that at least 100 characters are required.

**Result:** PASS

---

## Additional Functional Testing

The following functionality was also tested:

- Randomized correct-answer positions
- Quiz submission
- Score calculation
- Correct/incorrect feedback
- Answer explanations
- Quiz retake functionality
- API metadata display
- Quiz download

---

# Security

The OpenAI API key is stored locally using an environment variable.

The `.gitignore` file excludes:

```text
.env
.venv/
__pycache__/
*.pyc

```

The real API key should never be included in source code or uploaded to GitHub.

---

# Future Improvements

Possible future versions of QuizMate could include:

- PDF document upload
- PowerPoint upload
- Automatic document text extraction
- Flashcard generation
- True/False questions
- Additional question formats
- Saved quiz history
- User accounts
- Database storage
- Quiz performance analytics
- PDF quiz export
- Additional study modes

---

# Conclusion

QuizMate demonstrates how a Generative AI API can be integrated into a practical Python application.

The project combines the **OpenAI API for generative tasks** with conventional Python programming for validation, randomization, scoring, state management, and error handling.

This allows QuizMate to use the strengths of Generative AI while keeping deterministic application behavior under the control of traditional software logic.