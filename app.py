import logging
import streamlit as st
from modules.session_state import initialize_session_state
from modules.ui.ui_start_screen import render_main_screen
from modules.ui.ui_interview import render_interview_ui

# --- Logging configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("interview_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    # Initialize session state cleanly
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