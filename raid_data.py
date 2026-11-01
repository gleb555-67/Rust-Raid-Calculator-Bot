EXPLOSIVE_RECIPES = {
    "c4": {
        "name": "C4",
        "gunpowder": 1000,
        "metal": 200,
        "cloth": 5,
        "tech_trash": 2,
        "fuel": 60,
        "extra_sulfur": 200,
    },
    "rocket": {
        "name": "Ракета",
        "gunpowder": 650,
        "metal": 100,
        "fuel": 30,
        "metal_pipe": 2,
        "extra_sulfur": 100,
    },
    "satchel": {
        "name": "Сачель",
        "gunpowder": 240,
        "metal": 80,
        "cloth": 10,
        "rope": 1,
        "extra_sulfur": 0,
    },
    "ammo": {
        "name": "Разрывной 5.56",
        "gunpowder": 10,
        "metal": 5,
        "extra_sulfur": 5, 
    },
}

RAID_TARGETS = {
    "wood_wall": {
        "name": "Деревянная стена",
        "pure": {"c4": 1, "rocket": 1, "satchel": 2, "ammo": 41},
        "best_combo": None,
    },
    "stone_wall": {
        "name": "Каменная стена",
        "pure": {"c4": 2, "rocket": 4, "satchel": 10, "ammo": 185},
        "best_combo": None,
    },
    "sheet_wall": {
        "name": "Металлическая стена",
        "pure": {"c4": 4, "rocket": 8, "satchel": 23, "ammo": 400},
        "best_combo": {"c4": 3, "ammo": 70},
    },
    "armored_wall": {
        "name": "МВК стена",
        "pure": {"c4": 8, "rocket": 15, "satchel": 46, "ammo": 799},
        "best_combo": None,
    },
    "wood_door": {
        "name": "Деревянная дверь",
        "pure": {"c4": 1, "rocket": 1, "satchel": 2, "ammo": 18},
        "best_combo": None,
    },
    "sheet_door": {
        "name": "Металлическая дверь",
        "pure": {"c4": 1, "rocket": 2, "satchel": 4, "ammo": 63},
        "best_combo": None,
    },
    "garage_door": {
        "name": "Гаражная дверь",
        "pure": {"c4": 2, "rocket": 3, "satchel": 9, "ammo": 150},
        "best_combo": None,
    },
    "armored_door": {
        "name": "МВК дверь",
        "pure": {"c4": 3, "rocket": 6, "satchel": 18, "ammo": 250},
        "best_combo": None,
    },
}

def format_combo(combo: dict) -> str:
    parts = []
    for k, qty in combo.items():
        parts.append(f"{qty} {EXPLOSIVE_RECIPES[k]['name']}")
    return " + ".join(parts)

def calculate_step_by_step(combo: dict) -> dict:
    totals = {
        "gunpowder": 0, "extra_sulfur": 0, "metal": 0, "cloth": 0,
        "tech_trash": 0, "fuel": 0, "metal_pipe": 0, "rope": 0,
    }

    for item_key, qty in combo.items():
        recipe = EXPLOSIVE_RECIPES[item_key]
        for comp in ["gunpowder", "metal", "cloth", "tech_trash", "fuel", "metal_pipe", "rope"]:
            totals[comp] += recipe.get(comp, 0) * qty
        totals["extra_sulfur"] += recipe.get("extra_sulfur", 0) * qty

    gp = totals["gunpowder"]
    sulfur_for_gp = gp * 2      
    charcoal_for_gp = gp * 3    

    totals["sulfur"] = sulfur_for_gp + totals["extra_sulfur"]
    totals["charcoal"] = charcoal_for_gp

    return totals

def calculate_raid(target: dict) -> dict:
    options = []
    for kind, qty in target["pure"].items():
        combo = {kind: qty}
        totals = calculate_step_by_step(combo)
        options.append({
            "combo": combo, "text": format_combo(combo),
            "totals": totals, "is_combo": False,
        })

    if target.get("best_combo"):
        combo = target["best_combo"]
        totals = calculate_step_by_step(combo)
        options.append({
            "combo": combo, "text": format_combo(combo),
            "totals": totals, "is_combo": True,
        })

    options.sort(key=lambda x: x["totals"]["sulfur"])
    return {"best": options[0], "all": options}