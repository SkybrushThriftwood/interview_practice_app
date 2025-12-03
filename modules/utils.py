import os
import logging
import streamlit as st
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
from functools import lru_cache
from modules.config import PROMPTS_TEMPLATE_DIR, COST_PER_1M_INPUT_TOKENS, COST_PER_1M_OUTPUT_TOKENS
from modules.session_state import get_openai_settings
from tenacity import retry, wait_exponential, stop_after_attempt


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Environment and OpenAI client
# ---------------------------------------------------------------------
load_dotenv()
_client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------
# Retry-wrapped low-level OpenAI call
# ---------------------------------------------------------------------
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def _call_openai(
    sys_instructions: str,
    prompt_text: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_tokens: int = 250,
    structured_output: dict | None = None,
) -> str:
    """
    Internal low-level call to OpenAI with retry logic.
    Now also tracks token usage and cost inside Streamlit session state.
    """

    request_kwargs = {
        "model": model,
        "instructions": sys_instructions,
        "input": prompt_text,
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }

    if structured_output is not None:
        request_kwargs["text"] = structured_output

    logger.debug(
        f"Sending OpenAI request with model={model}, temp={temperature}, max_tokens={max_tokens}"
    )

    response = _client.responses.create(**request_kwargs)
    
    # --------
    # EXTRACT TEXT
    # --------
    if hasattr(response, "output_text") and response.output_text:
        text = response.output_text.strip()
    elif hasattr(response, "output") and response.output:
        blocks = response.output[0].get("content", [])
        text = blocks[0].get("text", "").strip() if blocks else ""
    else:
        text = ""

    # --------
    # TOKEN USAGE
    # --------
    prompt_tokens = getattr(getattr(response, "usage", None), "input_tokens", 0)
    completion_tokens = getattr(getattr(response, "usage", None), "output_tokens", 0)

    # --------
    # MODEL PRICING
    # --------
    input_price = COST_PER_1M_INPUT_TOKENS.get(model, 0)
    output_price = COST_PER_1M_OUTPUT_TOKENS.get(model, 0)

    # --------
    # SESSION STATE SAFE INITIALIZATION
    # --------
    ss = st.session_state
    ss.setdefault("input_tokens_total", 0)
    ss.setdefault("output_tokens_total", 0)
    ss.setdefault("cost_so_far", 0.0)

    # --------
    # UPDATE TOTAL COUNTS
    # --------
    ss.input_tokens_total += prompt_tokens
    ss.output_tokens_total += completion_tokens

    # Cost calculation (per 1M tokens)
    ss.cost_so_far += (
        (prompt_tokens * input_price / 1_000_000)
        + (completion_tokens * output_price / 1_000_000)
    )

    return text



# ---------------------------------------------------------------------
# Public API for OpenAI calls
# ---------------------------------------------------------------------
def openai_call(
    sys_instructions: str,
    prompt_text: str,
    structured_output: dict | None = None,
) -> str:
    """
    Public wrapper for OpenAI Responses API calls using session-state parameters.
    
    Args:
        sys_instructions: System-level instructions for the model.
        prompt_text: The main prompt content.
        structured_output: Optional structured output format (dict).
    
    Returns:
        str: Model response text
    """
    try:
        # Pull OpenAI parameters from Streamlit session state
        settings = get_openai_settings()
        return _call_openai(
            sys_instructions=sys_instructions,
            prompt_text=prompt_text,
            model=settings["model"],
            temperature=settings["temperature"],
            max_tokens=settings["max_tokens"],
            structured_output=structured_output,
        )
    

    except Exception as e:
        logger.exception(f"Error in openai_call: {e}")
        return "Error generating response. Please try again."


# ---------------------------------------------------------------------
# Jinja2 Environment for prompt templates
# ---------------------------------------------------------------------
env: Environment = Environment(loader=FileSystemLoader(PROMPTS_TEMPLATE_DIR))


@lru_cache(maxsize=128)
def load_template(template_name: str):
    """
    Load and cache a Jinja2 template.

    Args:
        template_name (str): Template filename

    Returns:
        jinja2.Template: Loaded template object
    """
    try:
        return env.get_template(template_name)
    except Exception as e:
        logger.error(f"Failed to load template '{template_name}': {e}")
        raise


def render_template(template_name: str, **kwargs) -> str:
    """
    Render a Jinja2 template with the given variables.

    Args:
        template_name (str): Template filename
        **kwargs: Variables for template rendering

    Returns:
        str: Rendered template text
    """
    logger.info(f"[PROMPT LOADER] Rendering template: {template_name}")
    template = load_template(template_name)
    rendered = template.render(**kwargs)

    try:
        logger.debug(f"=== FULLY RENDERED PROMPT ({template_name}) ===\n{rendered}")
    except UnicodeEncodeError:
        safe_log_file = Path("logs") / "full_prompt.log"
        safe_log_file.parent.mkdir(exist_ok=True)
        with safe_log_file.open("w", encoding="utf-8") as f:
            f.write(rendered)
        logger.debug(f"Prompt contains unprintable characters. Saved to {safe_log_file}")

    return rendered


def load_prompt(template_name: str, **kwargs) -> str:
    """
    Public interface to render a prompt template.

    Args:
        template_name (str): Template filename
        **kwargs: Template variables

    Returns:
        str: Rendered template text
    """
    return render_template(template_name, **kwargs)


def build_prompt(category: str, base_instructions: str, technique: str, **kwargs) -> str:
    """
    Build a full prompt by combining base instructions and technique template.

    Args:
        category (str): Prompt category (e.g., "questions", "evaluation")
        base_instructions (str): Base instruction template filename
        technique (str): Technique template filename
        **kwargs: Template variables

    Returns:
        str: Complete prompt text
    """
    logger.info(
        f"[PROMPT BUILDER] category={category}, base={base_instructions}, technique={technique}"
    )
    base = load_prompt(f"{category}/{base_instructions}", **kwargs)
    technique_section = load_prompt(f"{category}/{technique}", **kwargs)
    return f"{base}\n\n{technique_section}"