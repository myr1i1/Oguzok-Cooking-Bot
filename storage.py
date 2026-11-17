import json
import os

PATH = os.path.join(os.path.dirname(__file__), "favorites.json")


def _load():
    if not os.path.exists(PATH):
        return {}
    try:
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(d):
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def remember_user(uid, first_name, username):
    """Запомнить/обновить имя пользователя. Вызывать в /start."""
    d = _load()
    user = d.setdefault(str(uid), {})
    user["first_name"] = first_name
    user["username"] = username
    user.setdefault("favs", [])
    _save(d)


def is_fav(uid, rid):
    user = _load().get(str(uid), {})
    return rid in user.get("favs", [])


def toggle_fav(uid, rid):
    d = _load()
    user = d.setdefault(str(uid), {})
    favs = user.setdefault("favs", [])
    if rid in favs:
        favs.remove(rid)
        added = False
    else:
        favs.append(rid)
        added = True
    _save(d)
    return added


def get_favs(uid):
    user = _load().get(str(uid), {})
    return user.get("favs", [])


def get_user(uid):
    """Вернуть {first_name, username, favs} или None."""
    return _load().get(str(uid))