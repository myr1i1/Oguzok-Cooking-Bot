import json
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Recipe:
    def __init__(self, name, ingredients, steps, time, equipment, nutrition, tags):
        self.name = str(name)
        self.ingredients = ingredients
        self.steps = list(steps)
        self.time = int(time)
        self.equipment = equipment
        self.nutrition = dict(nutrition)
        self.tags = list(tags)
        self.id = hashlib.md5(str(name).encode("utf-8")).hexdigest()[:8]

    def match(self, own_ingredients):
        matches = 0
        for ingr in own_ingredients:
            if ingr.lower() in self.ingredients:
                matches += 1
        return matches

    def match_equipment(self, own_equipment):
        own = [e.lower() for e in own_equipment]
        return sum(1 for eq in self.equipment if eq.lower() in own)

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


def recipes_counter(path=os.path.join(BASE_DIR, "recipes.json")):
    with open(path, encoding="utf-8") as file:
        data = json.load(file)

    count = 0
    for item in data:
        if item["name"]:
            count += 1

    print(count)