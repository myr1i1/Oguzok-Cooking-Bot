import json
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SYNONYMS = {
    # Курица
    "курица": "курица",
    "куриное филе": "курица",
    "куриная грудка": "курица",
    "филе курицы": "курица",
    "курочка": "курица",
    # Яйца
    "яйцо": "яйца",
    "яйца": "яйца",
    "яичный белок": "яйца",
    "желток": "яйца",
    # Овощи
    "помидор": "помидоры",
    "помидоры": "помидоры",
    "томат": "помидоры",
    "томаты": "помидоры",
    "огурец": "огурец",
    "огурцы": "огурец",
    "соленые огурцы": "огурец",
    "картошка": "картофель",
    "картофель": "картофель",
    "зеленый лук": "лук",
    "лук": "лук",
    # Молочка
    "мягкий творог": "творог",
    "творожный сыр": "творог",
    "творожок": "творог",
    "творог": "творог",
    "сгущенка": "сгущенное молоко",
    "сгущенное молоко": "сгущенное молоко",
    "йогурт": "греческий йогурт",
    "греческий йогурт": "греческий йогурт",
    # Бакалея и сладкое
    "овсянка": "овсяные хлопья",
    "овсяные хлопья": "овсяные хлопья",
    "геркулес": "овсяные хлопья",
    "паста": "макароны",
    "макароны": "макароны",
    "нутелла": "шоколадная паста",
    "шоколадная паста": "шоколадная паста",
    "хлеб": "хлеб",
    "тостовый хлеб": "хлеб",
    "батон": "хлеб",
    "лаваш": "лаваш",
    "тортилья": "лаваш",
    "масло": "растительное масло",
    "подсолнечное масло": "растительное масло",
    "оливковое масло": "растительное масло",
    "растительное масло": "растительное масло",
    "тунец": "консервированный тунец",
    "консервированный тунец": "консервированный тунец",
    "фасоль": "консервированная фасоль",
    "консервированная фасоль": "консервированная фасоль",
    "ананас": "консервированные ананасы",
    "ананасы": "консервированные ананасы",
    "консервированные ананасы": "консервированные ананасы",
}


class Recipe:
    def __init__(self, name, ingredients, steps, time, equipment, nutrition, tags):
        self.name = str(name)
        self.ingredients = ingredients
        self.norm_ingredients = {normalize_ingredients(i) for i in self.ingredients}
        self.steps = list(steps)
        self.time = int(time)
        self.equipment = list(equipment)
        self.nutrition = dict(nutrition)
        self.tags = list(tags)
        self.id = hashlib.md5(str(name).encode("utf-8")).hexdigest()[:8]

    def match(self, own_ingredients):
        own_norm = {normalize_ingredients(i) for i in own_ingredients if i.strip()}
        return len(self.norm_ingredients & own_norm)

    def match_equipment(self, own_equipment):
        own = [e.strip().lower().replace("ё", "ё") for e in own_equipment if e.strip()]

        matches = 0
        for eq in self.equipment:
            clean_eq = eq.strip().lower().replace("ё", "е")
            if clean_eq in own:
                matches += 1

        return matches


    def beauty_text(self):
        steps_text = ""
        for i, step in enumerate(self.steps, start=1):
            steps_text += f"{i}. {step}\n"

        n = self.nutrition
        if len(self.equipment) > 1:
            equipment2 = ', '.join(self.ingredients)
        equipment2 = self.equipment[0]

        return (
            f"ᓚᘏᗢ {self.name}\n\n"
            f"⊹ Время: {self.time} мин\n"
            f"⊹ Что нужно: {equipment2}\n"
            f"⊹ КБЖУ: {n['kcal']} ккал, Б {n['protein']}, "
            f"Ж {n['fat']}, У {n['carbs']}\n\n"
            f"⊹ Ингредиенты: {', '.join(self.ingredients)}\n\n"
            f"⊹ Как готовить:\n{steps_text}"
        )


def load_recipes(path=os.path.join(BASE_DIR, "recipes.json")):
    with open(path, encoding="utf-8") as file:
        data = json.load(file)

    recipes = []
    for item in data:
        recipe = Recipe(
            item["name"],
            item["ingredients"],
            item["steps"],
            item["time"],
            item["equipment"],
            item["nutrition"],
            item["tags"],
        )
        recipes.append(recipe)
    return recipes


def normalize_ingredients(text:str) -> str:
    cleaned_ingredient = " ".join(text.lower().replace("ё", "е").split())
    if cleaned_ingredient in SYNONYMS:
        return SYNONYMS[cleaned_ingredient]
    return cleaned_ingredient


def recipes_counter(path=os.path.join(BASE_DIR, "recipes.json")):
    with open(path, encoding="utf-8") as file:
        data = json.load(file)

    count = 0
    for item in data:
        if item["name"]:
            count += 1

    print(count)