import os
from typing import List
import openai


class RecipeSuggester:
    """Provide recipe suggestions using OpenAI."""

    def __init__(self, ingredient_file: str = "main_ingredients.txt", utensil_file: str = "ustensiles.txt"):
        self.ingredient_file = ingredient_file
        self.utensil_file = utensil_file
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @staticmethod
    def load_list(path: str) -> List[str]:
        """Return the non-empty stripped lines of a file if it exists."""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                return [line.strip() for line in handle if line.strip()]
        return []

    @staticmethod
    def save_list(items: List[str], path: str) -> None:
        """Save the provided items to the file one per line."""
        with open(path, "w", encoding="utf-8") as handle:
            for item in items:
                handle.write(item.strip() + "\n")

    @staticmethod
    def create_prompt(request_text: str, ingredients: List[str], utensils: List[str]) -> str:
        """Compose the prompt for the language model."""
        ingr = ", ".join(ingredients) if ingredients else "none"
        utn = ", ".join(utensils) if utensils else "none"
        return (
            "Tu es un assistant culinaire serviable. "
            f"L'utilisateur peut utiliser ces ingrédients de base : {ingr}. "
            f"Ustensiles disponibles : {utn}. "
            f"Demande de l'utilisateur : {request_text}. "
            "Suggère une recette adaptée en prenant en compte les ingrédients et ustensiles disponibles. "
            "Réponds uniquement en français."
        )

    def suggest_recipe(self, request_text: str) -> str:
        """Return a recipe suggestion for the given request."""
        ingredients = self.load_list(self.ingredient_file)
        utensils = self.load_list(self.utensil_file)
        prompt = self.create_prompt(request_text, ingredients, utensils)
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
