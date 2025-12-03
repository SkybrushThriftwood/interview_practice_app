"""
config.py

Project-wide configuration for the Interview Practice App.

Includes:
- API mode flags
- Directory paths
- Template paths and techniques
- System prompts and base instructions
- Persona mappings and evaluation descriptions
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# --- Configurable parameters from .env ---
USE_MOCK_API = os.getenv("USE_MOCK_API", "False") == "True"
ACTIVE_QUESTION_TECHNIQUE = os.getenv("ACTIVE_QUESTION_TECHNIQUE", "contextual_progression.j2")
ACTIVE_SUMMARY_TECHNIQUE = os.getenv("ACTIVE_SUMMARY_TECHNIQUE", "default.j2")
ACTIVE_VALIDATION_TECHNIQUE = os.getenv("ACTIVE_VALIDATION_TECHNIQUE", "validate_job_title.j2")

# --- Base project directory ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Jinja2 template folder
PROMPTS_TEMPLATE_DIR = os.getenv("PROMPTS_TEMPLATE_DIR", os.path.join(BASE_DIR, "prompts"))

# System instruction templates
SYSTEM_PROMPTS = {
    "job_title_validator": os.getenv(
        "SYSTEM_JOB_TITLE_VALIDATOR", "system/job_title_validator.j2"
    ),
    "question_generator": os.getenv(
        "SYSTEM_QUESTION_GENERATOR", "system/question.j2"
    ),
    "answer_evaluator": os.getenv(
        "SYSTEM_ANSWER_EVALUATOR", "system/evaluation.j2"
    ),
    "summary_generator": os.getenv(
        "SYSTEM_SUMMARY_GENERATOR", "system/summary_generator.j2"
    ),
}

# Base instruction templates per category
BASE_PROMPTS = {
    "evaluation": os.getenv("BASE_PROMPT_EVALUATION", "base_instructions.j2"),
    "validation": os.getenv("BASE_PROMPT_VALIDATION", "base_instructions.j2"),
    "summary": os.getenv("BASE_PROMPT_SUMMARY", "base_instructions.j2"),
    "question": os.getenv("BASE_PROMPT_QUESTION", "base_instructions.j2"),
}

# Personas
PERSONA_MAP = {
    "Hiring Manager": os.getenv("PERSONA_HIRING_MANAGER", "personality_hiring_manager.j2"),
    "HR Professional": os.getenv("PERSONA_HR", "personality_hr.j2"),
    "Ideal Candidate": os.getenv("PERSONA_IDEAL_CANDIDATE", "personality_ideal_candidate.j2"),
    "Mentor": os.getenv("PERSONA_MENTOR", "personality_mentor.j2"),
    "Subject Matter Expert": os.getenv("PERSONA_SME", "personality_sme.j2"),
}

EVALUATION_PERSONAS = {
    "Hiring Manager": "Focuses on how a candidate would be assessed for hiring suitability.",
    "HR Professional": "Evaluates answers using HR best practices, professionalism, and compliance.",
    "Ideal Candidate": "Provides feedback from the perspective of a top-performing candidate, someone who has mastered this job and knows exactly what excellence looks like. They will highlight what you did well and what could be improved in your answer.",
    "Mentor": "Offers constructive, step-by-step guidance for learning and improvement.",
    "Subject Matter Expert": "Focuses on technical accuracy and domain expertise; may skip behavioral aspects."
}

OPENAI_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1",
    ]


COST_PER_1M_INPUT_TOKENS = {
    "gpt-4o-mini": 0.15,
    "gpt-4o":2.50,
    "o3-mini": 1.10,
    "gpt-5": 1.25,
    "gpt-4.1":2.00
}
COST_PER_1M_OUTPUT_TOKENS = {
    "gpt-4o-mini": 0.075,
    "gpt-4o": 1.25,
    "o3-mini": 4.40,
    "gpt-5": 10.00,
    "gpt-4.1":8.00
}