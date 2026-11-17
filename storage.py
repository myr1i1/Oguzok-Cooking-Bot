import json, os

PATH = os.path.join(os.path.dirname(__file__), "favorites.json")

def _load():
    return json.load(open(PATH, encoding="utf-8")) if os.path.exists(PATH) else {}

def _save(d):
    json.dump(d, open(PATH, "w", encoding="utf-8"), ensure_ascii=False)

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