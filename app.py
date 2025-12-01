import logging
import streamlit as st
import sys
from pathlib import Path
from modules.session_state import initialize_session_state
from modules.ui.ui_start_screen import render_main_screen
from modules.ui.ui_interview import render_interview_ui

def setup_logging():
    logger = logging.getLogger()

    # ⛔ Don't re-add handlers if already configured
    if logger.handlers:
        return

    logger.setLevel(logging.DEBUG)

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Console handler (INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    # File handler (DEBUG)
    file_handler = logging.FileHandler(log_dir / "app_debug.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(funcName)s:%(lineno)d): %(message)s"
    ))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False

def main():
    # Initialize session state cleanly
    setup_logging()
    initialize_session_state()

    # ------------------- Main Screen (Welcome) -------------------
    if not st.session_state.started:
        render_main_screen()
        return
            
    # ------------------- Interview Mode -------------------
    else:
        render_interview_ui()

        

if __name__ == "__main__":
    main()