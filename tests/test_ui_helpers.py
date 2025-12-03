import pytest  # noqa: F401
import streamlit as st
from modules.ui.ui_helpers import display_job_title_input, display_question_type_dropdown, display_difficulty_dropdown

def test_job_title_input(monkeypatch):
    # Monkeypatch Streamlit input
    monkeypatch.setattr(st, "text_input", lambda label, placeholder="": "Software Engineer")
    result = display_job_title_input()
    assert result == "Software Engineer"

def test_question_type_dropdown(monkeypatch):
    monkeypatch.setattr(st, "selectbox", lambda label, options: "Technical")
    result = display_question_type_dropdown()
    assert result == "Technical"

def test_difficulty_dropdown(monkeypatch):
    monkeypatch.setattr(st, "selectbox", lambda label, options: "Hard")
    result = display_difficulty_dropdown()
    assert result == "Hard"
