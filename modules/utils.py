import os
import logging
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from typing import Any
from dotenv import load_dotenv
from .config import PROMPTS_TEMPLATE_DIR

# --- setup logging ---
logger = logging.getLogger(__name__)
# No basicConfig here; configure it once in main.py/app.py

# --- decorator ---
def handle_errors(default=None):
    """
    Decorator to catch unexpected errors and return a fallback value.
    Useful for risky operations like API calls or file processing.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in '{func.__name__}': {e}", exc_info=True)
                return default
        return wrapper
    return decorator

@handle_errors(default=None)
def openai_call(instructions: str, user_input: str, temperature: float = 0.2) -> str:
    """
    Makes an API call to OpenAI using the Responses API.
    
    Args:
        instructions: System instructions for the model
        user_input: The user's prompt/input text (must be a string)
        temperature: Sampling temperature (default 0.2)
    
    Returns:
        str: The model's response text
    """
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.responses.create(
        model="gpt-4",
        instructions=instructions,
        input=user_input,  
        max_output_tokens=150,
        temperature=temperature,
    )

    return response.output_text

# --- Jinja2 environment ---
env = Environment(loader=FileSystemLoader(PROMPTS_TEMPLATE_DIR))

def get_prompt(template_name: str, **kwargs: Any) -> str:
    """
    Load a Jinja2 template by name and render it with variables.
    """
    try:
        template = env.get_template(template_name)
        if hasattr(template.module, kwargs.get("macro_name", "")):
            macro = getattr(template.module, kwargs.pop("macro_name"))
            return macro(**kwargs)
        return template.render(**kwargs)
    except Exception as e:
        logger.error(f"Error rendering template '{template_name}': {e}", exc_info=True)
        return ""
