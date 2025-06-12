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

st.title("Recommandation de recettes")
st.write("Enregistrez votre demande ou écrivez-la ci-dessous.")

LANGUAGE = "fr"
if "transcribed_text" not in st.session_state:
    st.session_state["transcribed_text"] = ""

audio_data = mic.mic_recorder(key="request_rec")
if audio_data and "bytes" in audio_data:
    st.session_state["transcribed_text"] = transcribe_audio(audio_data["bytes"], LANGUAGE)

st.write(st.session_state["transcribed_text"])

text_request = st.text_input("Ou écrivez votre demande :")

if st.button("Générer une recette"):
    request_text = text_request.strip()
    if audio_data:
        request_text = f"{request_text} {st.session_state['transcribed_text']}".strip()
    if not request_text:
        st.error("Veuillez fournir une demande par la voix ou le texte.")
    else:
        try:
            recipe = suggester.suggest_recipe(request_text)
            st.markdown(recipe)
        except Exception as exc:
            st.error(f"Erreur lors de la communication avec OpenAI : {exc}")

# Editors for ingredient and utensil lists
with st.expander("Modifier les ingrédients"):
    with st.form("ingredients_form"):
        ing_text = st.text_area(
            "Ingrédients (un par ligne)",
            "\n".join(suggester.load_list(suggester.ingredient_file)),
            height=150,
        )
        save_ing = st.form_submit_button("Enregistrer les ingrédients")
        if save_ing:
            items = [line.strip() for line in ing_text.splitlines() if line.strip()]
            suggester.save_list(items, suggester.ingredient_file)
            st.success("Ingrédients enregistrés")

with st.expander("Modifier les ustensiles"):
    with st.form("utensils_form"):
        utn_text = st.text_area(
            "Ustensiles (un par ligne)",
            "\n".join(suggester.load_list(suggester.utensil_file)),
            height=150,
        )
        save_utn = st.form_submit_button("Enregistrer les ustensiles")
        if save_utn:
            items = [line.strip() for line in utn_text.splitlines() if line.strip()]
            suggester.save_list(items, suggester.utensil_file)
            st.success("Ustensiles enregistrés")
