import math

SEUIL_DIFF_UTR = {"serré": 0.1, "équilibré": 0.3}

SURFACES = {
    "terre": {
        "jeux_par_set": {"serré": 12, "équilibré": 10, "déséquilibré": 8},
        "volatilité_base": "medium",
        "avantage_clutch": 1.1,
        "avantage_pressure": 0.9,
    },
    "dur": {
        "jeux_par_set": {"serré": 11, "équilibré": 9, "déséquilibré": 7},
        "volatilité_base": "medium",
        "avantage_clutch": 1.0,
        "avantage_pressure": 1.0,
    },
    "gazon": {
        "jeux_par_set": {"serré": 10, "équilibré": 8, "déséquilibré": 6},
        "volatilité_base": "high",
        "avantage_clutch": 0.9,
        "avantage_pressure": 1.1,
    },
}

TOURNOIS = {
    "Grand Chelem": {"volatilité": "high"},
    "Masters 1000": {"volatilité": "medium"},
    "ATP 500": {"volatilité": "low"},
}

AJUSTEMENT_METEO = {
    "vent": {"🔥 clutch": 0.98, "🧊 pressure": 1.02, "🎯 solide": 1.0},
    "humide": {"🔥 clutch": 1.0, "🧊 pressure": 0.98, "🎯 solide": 1.02},
    "soleil": {"🔥 clutch": 1.0, "🧊 pressure": 1.0, "🎯 solide": 1.0},
}

def jeux_par_set(utr_a, utr_b, surface):
    diff_utr = abs(utr_a - utr_b)
    if diff_utr < SEUIL_DIFF_UTR["serré"]:
        return SURFACES[surface]["jeux_par_set"]["serré"]
    if diff_utr < SEUIL_DIFF_UTR["équilibré"]:
        return SURFACES[surface]["jeux_par_set"]["équilibré"]
    return SURFACES[surface]["jeux_par_set"]["déséquilibré"]

def ajustement_profil(profil, surface):
    return SURFACES[surface].get(f"avantage_{profil.split()[0]}", 1.0)

def coefficient_forme(forme):
    victoires = forme.count("W")
    defaites = forme.count("L")
    if victoires >= 3: return 1.05
    if defaites >= 3: return 0.95
    return 1.0

def ajustement_classement(classement):
    if classement <= 10: return 1.05
    if classement <= 20: return 1.02
    return 1.0

def ajustement_fatigue(repos):
    return 0.95 if repos < 2 else 1.0

def ajustement_h2h(h2h, total=5):
    return 1.05 if h2h >= 3 else 1.0

def ajustement_service(service_won):
    return 1.03 if service_won > 70 else 1.0

def zone_jeux(utr_a, utr_b, sets, surface):
    jeux_set = jeux_par_set(utr_a, utr_b, surface)
    if sets == 3: return jeux_set * 2, jeux_set * 3
    return jeux_set * 3, jeux_set * 5

def profil(elo):
    if elo > 2150: return "🔥 clutch"
    if elo < 2000: return "🧊 pressure"
    return "🎯 solide"

def normalize(p1, p2):
    total = p1 + p2
    return p1 / total, p2 / total

def compute_match(utr_a, utr_b, elo_a, elo_b, surface="dur", sets=3, forme_a="WWWWW", forme_b="WWWWW", classement_a=50, classement_b=50, repos_a=3, repos_b=3, h2h_a=0, meteo="soleil", service_won_a=65, service_won_b=65, type_tournoi="ATP 250", cote_a=None, cote_b=None):
    proba_utr = 1 / (1 + 10 ** ((utr_b - utr_a) / 1.5))
    proba_elo = 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
    proba_a = (proba_utr * 0.6) + (proba_elo * 0.4)
    proba_b = 1 - proba_a
    profil_a, profil_b = profil(elo_a), profil(elo_b)
    proba_a *= ajustement_profil(profil_a, surface)
    proba_b *= ajustement_profil(profil_b, surface)
    proba_a *= coefficient_forme(forme_a)
    proba_b *= coefficient_forme(forme_b)
    proba_a *= ajustement_classement(classement_a)
    proba_b *= ajustement_classement(classement_b)
    proba_a *= ajustement_fatigue(repos_a)
    proba_b *= ajustement_fatigue(repos_b)
    proba_a *= ajustement_h2h(h2h_a)
    proba_a *= ajustement_service(service_won_a)
    proba_b *= ajustement_service(service_won_b)
    proba_a *= AJUSTEMENT_METEO[meteo].get(profil_a, 1.0)
    proba_b *= AJUSTEMENT_METEO[meteo].get(profil_b, 1.0)
    proba_a, proba_b = normalize(proba_a, proba_b)
    diff_utr = abs(utr_a - utr_b)
    if profil_a == "🧊 pressure" and profil_b == "🧊 pressure": volatility = "high"
    elif abs(proba_a - proba_b) < 0.05: volatility = SURFACES[surface]["volatilité_base"]
    else: volatility = "low"
    if type_tournoi in TOURNOIS: volatility = TOURNOIS[type_tournoi]["volatilité"]
    low, high = zone_jeux(utr_a, utr_b, sets, surface)
    mid = (low + high) / 2
    line = round(mid) + 0.5
    bet_type, bet_side, stake, edge_a, edge_b = "none", None, 0, None, None
    if cote_a and cote_b:
        book_a, book_b = 1 / cote_a, 1 / cote_b
        edge_a, edge_b = proba_a - book_a, proba_b - book_b
        if edge_a > 0.02: bet_type, bet_side = "winner", "A"
        elif edge_b > 0.02: bet_type, bet_side = "winner", "B"
        if bet_type != "none": stake = min(3, max(0.8, 2 if abs(edge_a if bet_side == "A" else edge_b) > 0.05 else 1.2))
    return {"proba_a": round(proba_a * 100, 1), "proba_b": round(proba_b * 100, 1), "volatility": volatility, "zone": (low, high), "line": line, "bet_type": bet_type, "bet_side": bet_side, "stake_percent": stake, "edge_a": edge_a, "edge_b": edge_b, "profil_a": profil_a, "profil_b": profil_b}

def format_result(home, away, result):
    lines = [
        f"🎯 Probabilités — {home} vs {away}",
        "━━━━━━━━━━━━━━━━━━",
        f"• {home} : {result['proba_a']}%",
        f"• {away} : {result['proba_b']}%",
        f"• Volatilité : {result['volatility']}",
        f"• Zone jeux : {result['zone'][0]}-{result['zone'][1]}",
    ]
    if result.get("bet_type") != "none":
        lines.append(f"💰 Pari suggéré : {result['bet_type']} {result['bet_side']} | mise {result['stake_percent']:.1f}%")
    return "\n".join(lines)
