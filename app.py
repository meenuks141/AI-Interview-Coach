import os
import json
import re
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
TOTAL_QUESTIONS = 5
MAX_RETRIES = 3
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="centered"
)
def call_gemini(client, prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5
                )
            )
            if response.text:
                return response.text.strip()
            raise ValueError("Empty response from Gemini.")
        except Exception as error:
            message = str(error).lower()
            if "429" in message or "resource_exhausted" in message:
                if attempt < retries - 1:
                    print(
                        "Gemini quota exceeded. "
                        "Waiting before retrying..."
                    )
                    time.sleep(30)
                    continue
            elif "503" in message or "unavailable" in message:
                if attempt < retries - 1:
                    time.sleep(5)
                    continue
            raise RuntimeError(
                f"Gemini API Error: {error}"
            )
    raise RuntimeError("Gemini request failed after retries.")
ROLES = {
    "Python Developer": """
    Python programming, data structures, OOP,
    exception handling, debugging, APIs and practical coding.
    """,

    "Data Analyst": """
    SQL, Excel, Python, Pandas, statistics,
    data cleaning, visualization and business insights.
    """,

    "Frontend Developer": """
    HTML, CSS, JavaScript, responsive design,
    accessibility and frontend frameworks.
    """,

    "Backend Developer": """
    APIs, databases, authentication,
    server-side programming and scalability.
    """,

    "Machine Learning Engineer": """
    Machine learning algorithms, feature engineering,
    model evaluation, overfitting and deployment.
    """,

    "General Software Engineer": """
    Programming fundamentals, algorithms,
    software design, debugging and testing.
    """
}
DIFFICULTIES = {
    "Beginner": """
    Ask basic conceptual questions.
    Focus on definitions and simple examples.
    """,

    "Intermediate": """
    Ask practical questions.
    Focus on application, reasoning and examples.
    """,

    "Advanced": """
    Ask challenging scenario-based questions.
    Focus on technical depth and problem-solving.
    """
}
def get_client():
    if not API_KEY:
        st.error(
            "GEMINI_API_KEY is missing. "
            "Please configure your .env file."
        )
        st.stop()
    return genai.Client(api_key=API_KEY)
def call_gemini(client, prompt, retries=MAX_RETRIES):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5
                )
            )
            if response.text:
                return response.text.strip()
            raise ValueError("Empty response from Gemini.")
        except Exception as error:
            message = str(error).lower()
            temporary_error = any(
                word in message
                for word in [
                    "503",
                    "429",
                    "unavailable",
                    "resource_exhausted",
                    "timeout"
                ]
            )
            if temporary_error and attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise RuntimeError(
                    f"Gemini API Error: {error}"
                )
    raise RuntimeError("Gemini request failed.")
def extract_json(response):
    cleaned = re.sub(
        r"```(?:json)?",
        "",
        response,
        flags=re.IGNORECASE
    )
    cleaned = cleaned.replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Invalid JSON response.")
    return json.loads(cleaned[start:end + 1])
def generate_first_question(client, role, difficulty):

    prompt = f"""
    You are a professional technical interviewer.

    Conduct an interview for the following role:

    Role: {role}

    Required skills:
    {ROLES[role]}

    Difficulty:
    {difficulty}

    Difficulty instructions:
    {DIFFICULTIES[difficulty]}

    Generate exactly ONE interview question.

    The question must be relevant to the selected role
    and difficulty.

    Return only the question.
    Do not provide an answer or explanation.
    """

    return call_gemini(client, prompt)
def evaluate_answer(
    client,
    role,
    difficulty,
    question,
    answer,
    history
):

    prompt = f"""
    You are an experienced technical interview evaluator.

    Evaluate the candidate's answer.

    Role: {role}

    Role requirements:
    {ROLES[role]}

    Difficulty: {difficulty}

    Question:
    {question}

    Candidate Answer:
    {answer}

    Previous interview context:
    {json.dumps(history[-4:])}

    Evaluate using these three criteria:

    1. Correctness
    2. Depth
    3. Clarity

    Each criterion must receive an integer rating
    between 1 and 5.

    Return ONLY valid JSON in this format:

    {{
        "correctness": 4,
        "depth": 3,
        "clarity": 5,
        "feedback": "Detailed feedback about the answer.",
        "strengths": [
            "Good technical understanding"
        ],
        "improvements": [
            "Include practical examples"
        ]
    }}

    Evaluation guidelines:

    Correctness:
    Evaluate technical accuracy.

    Depth:
    Evaluate completeness and reasoning.

    Clarity:
    Evaluate communication and organization.

    Be fair, specific and constructive.

    Return valid JSON only.
    """

    response = call_gemini(client, prompt)
    result = extract_json(response)
    def rating(value):
        try:
            return max(1, min(5, int(round(float(value)))))
        except (ValueError, TypeError):
            return 1
    return {

        "correctness": rating(
            result.get("correctness")
        ),

        "depth": rating(
            result.get("depth")
        ),

        "clarity": rating(
            result.get("clarity")
        ),

        "feedback": str(
            result.get("feedback", "No feedback available.")
        ),

        "strengths": result.get("strengths", []),

        "improvements": result.get("improvements", [])

    }
def generate_next_question(
    client,
    role,
    difficulty,
    history,
    question_number
):

    prompt = f"""
    You are conducting a technical interview.

    Role: {role}

    Required skills:
    {ROLES[role]}

    Difficulty: {difficulty}

    Instructions:
    {DIFFICULTIES[difficulty]}

    Previous interview:

    {json.dumps(history)}

    Generate question number {question_number}
    out of {TOTAL_QUESTIONS}.

    Rules:

    1. Do not repeat previous questions.
    2. Consider the candidate's previous answers.
    3. Ask relevant technical questions.
    4. Keep the difficulty consistent.
    5. Generate exactly one question.

    Return only the question.
    """

    return call_gemini(client, prompt)
def calculate_score(evaluations):
    if not evaluations:
        return {
            "score": 0,
            "correctness": 0,
            "depth": 0,
            "clarity": 0
        }
    count = len(evaluations)
    avg_correctness = sum(
        item["correctness"]
        for item in evaluations
    ) / count
    avg_depth = sum(
        item["depth"]
        for item in evaluations
    ) / count
    avg_clarity = sum(
        item["clarity"]
        for item in evaluations
    ) / count
    final_score = (
        avg_correctness * 0.40
        + avg_depth * 0.35
        + avg_clarity * 0.25
    ) / 5 * 100
    return {

        "score": round(final_score, 2),

        "correctness": round(avg_correctness, 2),

        "depth": round(avg_depth, 2),

        "clarity": round(avg_clarity, 2)

    }
def generate_final_report(
    client,
    role,
    difficulty,
    history,
    score_data
):

    prompt = f"""
    You are a professional interview coach.

    Prepare a detailed performance report.

    Candidate interview role:
    {role}

    Difficulty:
    {difficulty}

    Deterministic score:
    {score_data["score"]}/100

    Average correctness:
    {score_data["correctness"]}/5

    Average depth:
    {score_data["depth"]}/5

    Average clarity:
    {score_data["clarity"]}/5

    Interview history:

    {json.dumps(history)}

    Generate a report containing:

    1. Overall Assessment

    2. Key Strengths

    3. Weaknesses and Areas to Improve

    4. Technical Knowledge Assessment

    5. Seven-Day Improvement Plan

    6. Interview Readiness

    IMPORTANT:

    Do not calculate or modify the final score.

    The score is calculated by Python.

    Use the actual interview answers as evidence.

    Give practical and specific recommendations.
    """
    return call_gemini(client, prompt)
def initialize_session():
    defaults = {
        "started": False,
        "finished": False,
        "role": None,
        "difficulty": None,
        "question": None,
        "question_number": 1,
        "history": [],
        "evaluations": [],
        "report": None,
        "score_data": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
initialize_session()
def reset_interview():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session()
st.title("🎯 AI Interview Coach")
st.write(
    "Practice technical interviews with AI-powered "
    "questions, instant feedback and performance analysis."
)
st.divider()
if not st.session_state.started:
    st.header("Configure Your Interview")
    with st.form("interview_setup"):
        role = st.selectbox(
            "Choose your interview role",
            list(ROLES.keys())
        )
        difficulty = st.selectbox(
            "Choose difficulty level",
            list(DIFFICULTIES.keys())
        )
        start = st.form_submit_button(
            "🚀 Start Interview",
            type="primary"
        )
    if start:
        try:
            client = get_client()
            with st.spinner("Preparing your interview..."):
                question = generate_first_question(
                    client,
                    role,
                    difficulty
                )
            st.session_state.role = role
            st.session_state.difficulty = difficulty
            st.session_state.question = question
            st.session_state.started = True
            st.rerun()
        except Exception as error:
            st.error(str(error))
elif not st.session_state.finished:
    st.header(
        st.session_state.role
    )
    st.caption(
        f"Difficulty: {st.session_state.difficulty}"
    )
    st.progress(
        (st.session_state.question_number - 1)
        / TOTAL_QUESTIONS
    )
    st.subheader(
        f"Question {st.session_state.question_number} "
        f"of {TOTAL_QUESTIONS}"
    )
    st.info(
        st.session_state.question
    )
    with st.form(
        f"answer_form_{st.session_state.question_number}"
    ):
        answer = st.text_area(
            "Enter your answer",
            height=180,
            placeholder="Write your answer here..."
        )
        submit = st.form_submit_button(
            "Submit Answer",
            type="primary"
        )
    if submit:
        if not answer.strip():
            st.warning(
                "Please enter an answer before submitting."
            )
        else:
            try:
                client = get_client()
                with st.spinner("Evaluating your answer..."):
                    evaluation = evaluate_answer(
                        client,
                        st.session_state.role,
                        st.session_state.difficulty,
                        st.session_state.question,
                        answer,
                        st.session_state.history
                    )
                entry = {
                    "question_number":
                    st.session_state.question_number,
                    "question":
                    st.session_state.question,
                    "answer":
                    answer,
                    "evaluation":
                    evaluation
                }
                st.session_state.history.append(entry)
                st.session_state.evaluations.append(
                    evaluation
                )
                st.session_state.last_evaluation = evaluation
                if (
                    st.session_state.question_number
                    == TOTAL_QUESTIONS
                ):
                    st.session_state.score_data = calculate_score(
                        st.session_state.evaluations
                    )
                    with st.spinner(
                        "Generating your final report..."
                    ):
                        st.session_state.report = generate_final_report(
                            client,
                            st.session_state.role,
                            st.session_state.difficulty,
                            st.session_state.history,
                            st.session_state.score_data
                        )
                    st.session_state.finished = True
                else:
                    next_question = generate_next_question(
                        client,
                        st.session_state.role,
                        st.session_state.difficulty,
                        st.session_state.history,
                        st.session_state.question_number + 1
                    )
                    st.session_state.question = next_question
                    st.session_state.question_number += 1
                st.rerun()
            except Exception as error:
                st.error(str(error))
    if (
        "last_evaluation" in st.session_state
        and st.session_state.question_number > 1
    ):
        evaluation = st.session_state.last_evaluation
        st.divider()
        st.subheader("Previous Answer Feedback")
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Correctness",
            f"{evaluation['correctness']}/5"
        )
        col2.metric(
            "Depth",
            f"{evaluation['depth']}/5"
        )
        col3.metric(
            "Clarity",
            f"{evaluation['clarity']}/5"
        )
        st.write(evaluation["feedback"])
else:
    st.success(
        "Congratulations! You completed the interview."
    )
    score = st.session_state.score_data
    st.header("📊 Your Interview Results")
    st.metric(
        "Overall Score",
        f"{score['score']}/100"
    )
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Correctness",
        f"{score['correctness']}/5"
    )
    col2.metric(
        "Depth",
        f"{score['depth']}/5"
    )
    col3.metric(
        "Clarity",
        f"{score['clarity']}/5"
    )
    st.divider()
    st.header("📝 Performance Report")
    st.markdown(
        st.session_state.report
    )
    with st.expander(
        "View Individual Question Evaluations"
    ):
        for item in st.session_state.history:
            st.subheader(
                f"Question {item['question_number']}"
            )
            st.write(
                "**Question:**",
                item["question"]
            )
            st.write(
                "**Your Answer:**",
                item["answer"]
            )
            evaluation = item["evaluation"]
            st.write(
                f"Correctness: {evaluation['correctness']}/5"
            )
            st.write(
                f"Depth: {evaluation['depth']}/5"
            )
            st.write(
                f"Clarity: {evaluation['clarity']}/5"
            )
            st.write(
                evaluation["feedback"]
            )
            st.divider()
    report_data = {
        "role": st.session_state.role,
        "difficulty": st.session_state.difficulty,
        "score": score,
        "interview_history": st.session_state.history,
        "final_report": st.session_state.report
    }
    st.download_button(
        label="📥 Download Interview Report",
        data=json.dumps(
            report_data,
            indent=4,
            ensure_ascii=False
        ),
        file_name="interview_report.json",
        mime="application/json"
    )
    if st.button("🔄 Start New Interview"):
        reset_interview()
        st.rerun()
st.divider()
st.caption(
    "AI Interview Coach | Powered by Gemini AI and Streamlit"
)
st.caption(
    "Individual evaluations are AI-generated. "
    "The final weighted score is calculated using Python."
)