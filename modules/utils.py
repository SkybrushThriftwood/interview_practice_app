import os
import logging
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
from functools import lru_cache
from modules.config import PROMPTS_TEMPLATE_DIR
from tenacity import retry, wait_exponential, stop_after_attempt


# --- setup logging ---
logger = logging.getLogger(__name__)


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

# ---------------------------------------------------------------------
# Helper: Safely extract output text
# ---------------------------------------------------------------------
def _extract_output_text(response):
    """
    Safely extract `response.output_text` from the Responses API.
    """
    try:
        text = response.output_text
        if not text:
            raise ValueError("OpenAI returned empty output_text.")
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from OpenAI response: {e}")
        return "I'm sorry, I couldn't generate a valid response."


# ---------------------------------------------------------------------
# Base OpenAI client — initialized once
# ---------------------------------------------------------------------
load_dotenv()
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------
# Retry-wrapped OpenAI call
# ---------------------------------------------------------------------
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
)
def _call_openai(
    sys_instructions: str,
    prompt_text: str,
    temperature: float = 0.2,
    structured_output: dict | None = None,
) -> str:
    """
    Internal low-level call with retry logic using OpenAI >=2.8.1.
    """
    request_kwargs = {
        "model": "gpt-4o-mini",
        "instructions": sys_instructions,
        "input": prompt_text,
        "max_output_tokens": 250,
        "temperature": temperature,
    }

    # Fix: Use 'response_format' instead of 'text'
    if structured_output is not None:
        request_kwargs["text"] = structured_output

    logger.debug("Sending request to OpenAI Responses API", extra={
        "instructions": sys_instructions,
        "prompt_preview": prompt_text[:200],
        "temperature": temperature,
        "structured_output": structured_output,
    })

    response = _client.responses.create(**request_kwargs)
    logger.debug("Received response from OpenAI", extra={"response": str(response)})

    # Extract text safely
    try:
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text
        elif hasattr(response, "output") and response.output:
            # Returns the first message's first text content
            content_blocks = response.output[0].get("content", [])
            if content_blocks:
                return content_blocks[0].get("text", "")
            return ""
        else:
            return str(response)
    except Exception as e:
        logger.error(f"Failed to extract text from OpenAI response: {e}")
        return ""
# ---------------------------------------------------------------------
# Public API — same name as before
# ---------------------------------------------------------------------
@handle_errors(default=None)
def openai_call(
    sys_instructions: str,
    prompt_text: str,
    temperature: float = 0.2,
    structured_output: dict | None = None,
) -> str:
    """
    Public wrapper for OpenAI Responses API calls.
    Keeps the original function name.
    
    Args:
        sys_instructions: System-level instructions for the model
        prompt_text: The main prompt content
        temperature: Sampling temperature
        response_format: Optional structured output format (dict)
    
    Returns:
        str: Model response text
    """
    try:
        return _call_openai(sys_instructions, prompt_text, temperature, structured_output)
    except Exception as e:
        logger.error(f"Error in 'openai_call': {e}")
        return ""
# Create global Jinja environment
env = Environment(loader=FileSystemLoader(PROMPTS_TEMPLATE_DIR))


# ---------------------------
# Safe caching: TEMPLATE ONLY
# ---------------------------
@lru_cache(maxsize=128)
def load_template(template_name: str):
    """
    Load and cache the Jinja2 template object itself.
    Rendering still happens fresh every time.
    """
    try:
        return env.get_template(template_name)
    except Exception as e:
        logger.error(f"Failed to load template '{template_name}': {e}")
        raise


# ---------------------------
# Rendering (NO CACHE!)
# ---------------------------
def render_template(template_name: str, **kwargs) -> str:
    """
    Render a template with the given variables.
    This function is intentionally NOT cached so that
    job_title, question history, and state updates always apply.
    """
    logger.info(f"[PROMPT LOADER] Loading prompt template: {template_name}")
    template = load_template(template_name)
    rendered = template.render(**kwargs)

    try:
        logger.debug(f"=== FULLY RENDERED PROMPT ({template_name}) ===\n{rendered}")
    except UnicodeEncodeError:
        # fallback for Windows console
        safe_log_file = Path("logs") / "full_prompt.log"
        safe_log_file.parent.mkdir(exist_ok=True)
        with safe_log_file.open("w", encoding="utf-8") as f:
            f.write(rendered)
        logger.debug(f"Prompt contained characters that cannot be printed in console. Written to {safe_log_file}")

    return rendered


# ---------------------------
# Combined loading helper
# ---------------------------
def load_prompt(template_name: str, **kwargs) -> str:
    """
    Public interface to render a template.
    """
    return render_template(template_name, **kwargs)

def build_prompt(category: str, base_instructions: str, technique: str, **kwargs) -> str:
    """
    Build the prompt by rendering:
    - base instruction template
    - technique template
    """
    logger.info(
        f"[PROMPT BUILDER] category={category}, "
        f"base={base_instructions}, technique={technique}"
    )
    base = load_prompt(f"{category}/{base_instructions}", **kwargs)
    technique_section = load_prompt(f"{category}/{technique}", **kwargs)

    return f"{base}\n\n{technique_section}"
