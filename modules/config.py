import os

USE_MOCK_API = True

# Base project directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Jinja2 template folder
PROMPTS_TEMPLATE_DIR = os.path.join(BASE_DIR, "prompts", "templates")