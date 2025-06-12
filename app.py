import tempfile
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit_mic_recorder as mic

from suggester import RecipeSuggester

suggester = RecipeSuggester()


def transcribe_audio(data: Any, language: str) -> str:
    """Return transcribed text from uploaded data or raw bytes."""
    if data is None:
        return ""
    if isinstance(data, bytes):
        suffix = ".wav"
        buffer = data
    else:
        suffix = Path(data.name).suffix
        buffer = data.getbuffer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(buffer)
        tmp_path = Path(tmp.name)
    try:
        with open(tmp_path, "rb") as f:
            response = suggester.client.audio.transcriptions.create(
                model="whisper-1", file=f, language=language
            )
            return response.text.strip()
    finally:
        tmp_path.unlink(missing_ok=True)

st.title("Recipe Recommender")
st.write("Record your request or type it below.")

language = st.selectbox("Language", ["en", "fr"], index=1)
audio_data = mic.mic_recorder(key="request_rec")
text_request = st.text_input("Or type your request:")

if st.button("Generate recipe"):
    request_text = text_request.strip()
    if audio_data:
        request_text = f"{request_text} {transcribe_audio(audio_data['bytes'], language)}".strip()
    if not request_text:
        st.error("Please provide a request either by voice or text.")
    else:
        try:
            recipe = suggester.suggest_recipe(request_text)
            st.markdown(recipe)
        except Exception as exc:
            st.error(f"Error communicating with OpenAI: {exc}")

# Editors for ingredient and utensil lists
st.header("Edit ingredients")
with st.form("ingredients_form"):
    ing_text = st.text_area(
        "Ingredients (one per line)",
        "\n".join(suggester.load_list(suggester.ingredient_file)),
        height=150,
    )
    save_ing = st.form_submit_button("Save ingredients")
    if save_ing:
        items = [line.strip() for line in ing_text.splitlines() if line.strip()]
        suggester.save_list(items, suggester.ingredient_file)
        st.success("Ingredients saved")

st.header("Edit utensils")
with st.form("utensils_form"):
    utn_text = st.text_area(
        "Utensils (one per line)",
        "\n".join(suggester.load_list(suggester.utensil_file)),
        height=150,
    )
    save_utn = st.form_submit_button("Save utensils")
    if save_utn:
        items = [line.strip() for line in utn_text.splitlines() if line.strip()]
        suggester.save_list(items, suggester.utensil_file)
        st.success("Utensils saved")
