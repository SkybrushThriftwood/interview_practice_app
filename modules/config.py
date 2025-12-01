import os

USE_MOCK_API = False

# Base project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Jinja2 template folder
PROMPTS_TEMPLATE_DIR = os.path.join(BASE_DIR, "prompts")

# Active techniques
ACTIVE_QUESTION_TECHNIQUE = "contextual_progression.j2"
ACTIVE_SUMMARY_TECHNIQUE = "default.j2"
ACTIVE_VALIDATION_TECHNIQUE = "validate_job_title.j2"

# System instruction templates
SYSTEM_PROMPTS = {
    "job_title_validator": "system/job_title_validator.j2",
    "question_generator": "system/eval_and_question.j2",
    "answer_evaluator": "system/eval_and_question.j2",
    "summary_generator": "system/summary_generator.j2",
}

# Base instruction templates per category
BASE_PROMPTS = {
    "evaluation": "base_instructions.j2",
    "validation": "base_instructions.j2",
    "summary": "base_instructions.j2",
    "question": "base_instructions.j2",
}

PERSONA_MAP = {
            "Hiring Manager": "personality_hiring_manager.j2",
            "HR Professional": "personality_hr.j2",
            "Ideal Candidate": "personality_ideal_candidate.j2",
            "Mentor": "personality_mentor.j2",
            "Subject Matter Expert": "personality_sme.j2",
        }

EVALUATION_PERSONAS = {
    "Hiring Manager": "Focuses on how a candidate would be assessed for hiring suitability.",
    "HR Professional": "Evaluates answers using HR best practices, professionalism, and compliance.",
    "Ideal Candidate": "Provides feedback from the perspective of a top-performing candidate, someone who has mastered this job and knows exactly what excellence looks like. They will highlight what you did well and what could be improved in your answer.",
    "Mentor": "Offers constructive, step-by-step guidance for learning and improvement.",
    "Subject Matter Expert": "Focuses on technical accuracy and domain expertise; may skip behavioral aspects."
}