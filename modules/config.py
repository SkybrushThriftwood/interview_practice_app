import os

USE_MOCK_API = True

# Base project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Jinja2 template folder
PROMPTS_TEMPLATE_DIR = os.path.join(BASE_DIR, "prompts")

# Active techniques
ACTIVE_QUESTION_TECHNIQUE = "zero_shot"
ACTIVE_EVALUATION_TECHNIQUE = "zero_shot"
ACTIVE_SUMMARY_TECHNIQUE = "zero_shot"
ACTIVE_VALIDATION_TECHNIQUE = "default"

EVALUATION_PERSONAS = {
    "Hiring Manager": "Focuses on how a candidate would be assessed for hiring suitability.",
    "HR Professional": "Evaluates answers using HR best practices, professionalism, and compliance.",
    "Ideal Candidate": "Provides feedback from the perspective of a top-performing candidate, someone who has mastered this job and knows exactly what excellence looks like. They will highlight what you did well and what could be improved in your answer.",
    "Mentor": "Offers constructive, step-by-step guidance for learning and improvement.",
    "Subject Matter Expert": "Focuses on technical accuracy and domain expertise; may skip behavioral aspects."
}