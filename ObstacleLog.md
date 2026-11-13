AI Interview Coach – Obstacle Log

During the development of AI Interview Coach, I encountered several challenges while integrating the Gemini API and implementing the interactive interview workflow.

1. Gemini API Integration

Challenge:
Integrating the Gemini API and obtaining consistent responses required additional configuration and testing.

Solution:
Used the official Google GenAI Python SDK and configured API credentials securely using environment variables with python-dotenv.

2. Gemini API Rate Limits

Challenge:
During testing, the application encountered 429 RESOURCE_EXHAUSTED errors because the free-tier daily request quota for the selected Gemini model was exhausted.

Solution:

* Implemented retry handling for temporary API errors.
* Made the Gemini model configurable through environment variables.
* Optimized testing to reduce unnecessary API requests.
* Continued testing after quota availability was restored.

Status: Successfully tested the application across three different roles: Python Developer, Data Analyst and Frontend Developer.

3. Structured JSON Evaluation

Challenge:
The LLM sometimes returned JSON responses surrounded by Markdown code blocks or additional text, making direct JSON parsing unreliable.

Solution:
Implemented an extract_json() function using regular expressions to extract the JSON object before parsing it with Python’s json.loads().

4. Maintaining Interview Conversation State

Challenge:
The application needed to maintain the selected role, difficulty, current question, previous answers and evaluation results across Streamlit reruns.

Solution:
Implemented st.session_state to maintain interview progress and preserve conversation history.

5. Consistent Performance Scoring

Challenge:
Relying entirely on the LLM for the final score could result in inconsistent scoring.

Solution:
Implemented a deterministic Python scoring function using weighted averages:

* Correctness: 40%
* Depth: 35%
* Clarity: 25%

This ensures the final score is calculated consistently from individual evaluations.

6. Final Performance Report

Challenge:
Generating a useful final report required considering all interview answers rather than evaluating only the last response.

Solution:
Stored individual questions, answers and evaluations in interview history and passed the complete history to Gemini when generating the final report.

Conclusion

The development process helped me understand practical LLM integration, API error handling, structured JSON processing, Streamlit session management and deterministic evaluation.

The application successfully demonstrates role-based AI interviews, automated answer evaluation and Python-based performance scoring, providing an interactive technical interview practice experience.