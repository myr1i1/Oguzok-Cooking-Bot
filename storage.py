import json, os


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


def is_fav(uid, rid):
    return rid in _load().get(str(uid), [])


def toggle_fav(uid, rid):
    d = _load()
    favs = d.setdefault(str(uid), [])
    if rid in favs: favs.remove(rid); added = False
    else: favs.append(rid); added = True
    _save(d); return added


def get_favs(uid):
    return _load().get(str(uid), [])