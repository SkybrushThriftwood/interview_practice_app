import os
import logging
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from dotenv import load_dotenv
from functools import lru_cache
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
def openai_call(sys_instructions: str, prompt_text: str, temperature: float = 0.2) -> str:
    """
    Makes an API call to OpenAI using the Responses API.
    
    Args:
        prompt_text: The full merged prompt including instructions and all content.
        temperature: Sampling temperature (default 0.2)
    
    Returns:
        str: The model's response text
    """
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.responses.create(
        model="gpt-4",
        instructions=sys_instructions,
        input=prompt_text,  
        max_output_tokens=250,
        temperature=temperature,
    )

    return response.output_text

# --- Jinja2 environment ---
env = Environment(loader=FileSystemLoader(PROMPTS_TEMPLATE_DIR))
   

@lru_cache(maxsize=128)
def load_prompt(template_name: str, kwargs_tuple: tuple = ()) -> str:
    """
    Load a Jinja2 template and render it with kwargs.
    Cached to avoid repeated rendering in Streamlit reruns.
    
    kwargs_tuple: tuple of (key, value) pairs, e.g. tuple(sorted(kwargs.items()))
    """
    template = env.get_template(template_name)
    kwargs = dict(kwargs_tuple)
    return template.render(**kwargs)

def load_prompt_cached(template_name: str, **kwargs):
    return load_prompt(template_name, kwargs_tuple=tuple(sorted(kwargs.items())))

def build_prompt(category: str, technique: str, **kwargs) -> str:
    """
    Combine base instructions + selected technique prompt + Jinja variables.
    """
    base = load_prompt_cached(f"{category}/base_instructions.j2", **kwargs)
    technique = load_prompt_cached(f"{category}/technique_{technique}.j2", **kwargs)

    return base + "\n" + technique
