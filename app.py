import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

from suggester import RecipeSuggester

suggester = RecipeSuggester()


def transcribe_audio(uploaded_file: Any, language: str) -> str:
    """Return transcribed text from an uploaded audio file or raw bytes."""
    if uploaded_file is None:
        return ""
    if isinstance(uploaded_file, bytes):
        suffix = ".wav"
        buffer = uploaded_file
    else:
        suffix = Path(uploaded_file.name).suffix
        buffer = uploaded_file.getbuffer()
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

audio_file = st.audio_input("Enregistrer votre demande")

text_request = st.text_input("Ou écrivez votre demande :")

if st.button("Générer une recette"):
    request_text = text_request.strip()
    if audio_file:
        request_text = f"{request_text} {transcribe_audio(audio_file, LANGUAGE)}".strip()
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
