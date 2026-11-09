import json


class Recipe:
    def __init__(self, name, ingredients, steps, time, equipment, nutrition, tags):
        self.name = str(name)
        self.ingredients = list(ingredients)
        self.steps = list(steps)
        self.time = int(time)
        self.equipment = str(equipment)
        self.nutrition = dict(nutrition)
        self.tags = list(tags)

    def match(self, own_ingredients):
        matches = 0
        for ingr in own_ingredients.lower():
            if ingr in self.ingredients.lower():
                matches += 1
        return matches

    def beauty_text(self):
        steps_text = ""
        for i, step in enumerate(self.steps, start=1):
            steps_text += f"{i}. {step}\n"

        n = self.nutrition
        return (
            f"ᓚᘏᗢ {self.name}\n\n"
            f"⊹ Время: {self.time} мин\n"
            f"⊹ Что нужно: {self.equipment}\n"
            f"⊹ КБЖУ: {n['kcal']} ккал, Б {n['protein']}, "
            f"Ж {n['fat']}, У {n['carbs']}\n\n"
            f"⊹ Ингредиенты: {', '.join(self.ingredients)}\n\n"
            f"⊹ Как готовить:\n{steps_text}"
        )


def load_recipes(path="recipes.json"):
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