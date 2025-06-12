import os
import streamlit as st
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


def load_list(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []


def create_prompt(request_text, ingredients, utensils):
    ingr = ", ".join(ingredients) if ingredients else "none"
    utn = ", ".join(utensils) if utensils else "none"
    return (
        "You are a helpful cooking assistant. "
        f"The user can use these base ingredients: {ingr}. "
        f"Available utensils: {utn}. "
        f"User request: {request_text}. "
        "Suggest a recipe that fits the request, taking into account the available ingredients and utensils."
    )


st.title("Recipe Recommender")

st.write("Record your request or type it below.")

audio_bytes = None
transcription = ""

if hasattr(st, "audio_recorder"):
    audio_bytes = st.audio_recorder("Record your request")
else:
    uploaded = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a"])
    if uploaded is not None:
        audio_bytes = uploaded.read()

text_request = st.text_input("Or type your request:")

if st.button("Generate recipe"):
    if audio_bytes:
        with open("temp_audio.wav", "wb") as f:
            f.write(audio_bytes)
        with open("temp_audio.wav", "rb") as f:
            result = openai.Audio.transcribe("whisper-1", f)
            transcription = result["text"]
    request_text = " ".join([text_request, transcription]).strip()

    if not request_text:
        st.error("Please provide a request either by voice or text.")
    else:
        ingredients = load_list("main_ingredients.txt")
        utensils = load_list("ustensiles.txt")
        prompt = create_prompt(request_text, ingredients, utensils)
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
            )
            recipe = response["choices"][0]["message"]["content"]
            st.markdown(recipe)
        except Exception as e:
            st.error(f"Error communicating with OpenAI: {e}")
