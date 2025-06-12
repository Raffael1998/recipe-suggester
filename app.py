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
audio_data = mic.mic_recorder(
    start_prompt="Click to record",
    stop_prompt="Click to stop",
    key="request_rec",
)
text_request = st.text_input("Or type your request:")

# Sidebar editors for ingredient and utensil lists
with st.sidebar.form("ingredients_form"):
    st.write("Edit ingredients")
    ingredients = suggester.load_list(suggester.ingredient_file)
    sel_ing = st.multiselect("Ingredients", ingredients, default=ingredients, key="ing_select")
    new_ing = st.text_input("Add ingredient", key="new_ing")
    save_ing = st.form_submit_button("Save ingredients")
    if save_ing:
        if new_ing.strip():
            sel_ing.append(new_ing.strip())
        suggester.save_list(sel_ing, suggester.ingredient_file)
        st.success("Ingredients saved")

with st.sidebar.form("utensils_form"):
    st.write("Edit utensils")
    utensils = suggester.load_list(suggester.utensil_file)
    sel_utn = st.multiselect("Utensils", utensils, default=utensils, key="utn_select")
    new_utn = st.text_input("Add utensil", key="new_utn")
    save_utn = st.form_submit_button("Save utensils")
    if save_utn:
        if new_utn.strip():
            sel_utn.append(new_utn.strip())
        suggester.save_list(sel_utn, suggester.utensil_file)
        st.success("Utensils saved")

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
