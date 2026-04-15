# api/tennis_api.py

import requests
from datetime import date
from config import TENNIS_API_KEY

BASE_URL           = "https://api.api-tennis.com/tennis/"
ATP_EVENT_TYPE_KEY = "265"   # Atp Singles

# ---------------------------------------------------------------------------
# Logger debug
# ---------------------------------------------------------------------------

def _log(level: str, module: str, msg: str):
    icons = {"OK": "🟢", "ERROR": "🔴", "WARN": "🟡", "INFO": "🔵"}
    print(f"{icons.get(level, '⚪')} [{module}] {msg}")


def _safe_key(key: str) -> str:
    """Masque la clé API : affiche les 4 premiers + *** """
    if not key or len(key) < 5:
        return "***"
    return key[:4] + "***"


# ---------------------------------------------------------------------------
# Appel générique
# ---------------------------------------------------------------------------

def _get(method: str, params: dict = {}) -> list | dict:
    """Appel générique à l'API api-tennis.com avec debug complet."""
    full_params = {"method": method, "APIkey": TENNIS_API_KEY, **params}

    # URL lisible sans clé complète
    debug_params = {k: (_safe_key(v) if k == "APIkey" else v) for k, v in full_params.items()}
    debug_url = requests.Request("GET", BASE_URL, params=debug_params).prepare().url
    _log("INFO", "tennis_api", f"→ {debug_url}")

    try:
        resp = requests.get(BASE_URL, params=full_params, timeout=10)

        # Détail sur les erreurs auth
        if resp.status_code in (401, 403):
            _log("ERROR", "tennis_api", f"HTTP {resp.status_code} sur {method} — réponse brute : {resp.text[:300]}")
            return []

        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            _log("WARN", "tennis_api", f"{method} — success=0 : {str(data)[:200]}")
            return []

        result = data.get("result", [])
        count  = len(result) if isinstance(result, list) else "dict"
        _log("OK", "tennis_api", f"{method} → {count} résultats")
        return result

    except requests.exceptions.Timeout:
        _log("ERROR", "tennis_api", f"{method} — timeout (>10s)")
        return []
    except requests.exceptions.ConnectionError:
        _log("ERROR", "tennis_api", f"{method} — connexion impossible (réseau ?)")
        return []
    except Exception as e:
        _log("ERROR", "tennis_api", f"{method} — exception : {e}")
        return []


# ---------------------------------------------------------------------------
# Matchs en direct
# ---------------------------------------------------------------------------

def fetch_tennis_matches() -> list[dict]:
    """Retourne les matchs ATP en direct (livescore)."""
    try:
        result = _get("get_livescore", {"event_type_key": ATP_EVENT_TYPE_KEY})
        matches = []
        for m in result:
            matches.append({
                "id":         m.get("event_key"),
                "player1":    m.get("event_first_player", "?"),
                "player2":    m.get("event_second_player", "?"),
                "tournament": m.get("tournament_name", "Tournoi inconnu"),
                "status":     f'{m.get("event_status", "")} {m.get("event_game_result", "")}'.strip(),
                "date":       m.get("event_date", ""),
            })
        return matches
    except Exception as e:
        _log("ERROR", "tennis_api", f"fetch_tennis_matches — {e}")
        return []


# ---------------------------------------------------------------------------
# Matchs programmés aujourd'hui
# ---------------------------------------------------------------------------

def fetch_tennis_matches_scheduled() -> list[dict]:
    """Retourne les matchs ATP programmés aujourd'hui."""
    try:
        today  = date.today().strftime("%Y-%m-%d")
        result = _get("get_fixtures", {
            "date_start":     today,
            "date_stop":      today,
            "event_type_key": ATP_EVENT_TYPE_KEY,
        })
        matches = []
        for m in result:
            matches.append({
                "id":         m.get("event_key"),
                "player1":    m.get("event_first_player", "?"),
                "player2":    m.get("event_second_player", "?"),
                "tournament": m.get("tournament_name", "Tournoi inconnu"),
                "status":     m.get("event_status", "Programmé"),
                "date":       f'{m.get("event_date", "")} {m.get("event_time", "")}'.strip(),
            })
        return matches
    except Exception as e:
        _log("ERROR", "tennis_api", f"fetch_tennis_matches_scheduled — {e}")
        return []


# ---------------------------------------------------------------------------
# UTR d'un joueur (base locale)
# ---------------------------------------------------------------------------

_UTR_FALLBACK = {
    "novak djokovic":     16.5, "djokovic":    16.5,
    "rafael nadal":       16.0, "nadal":       16.0,
    "roger federer":      15.8, "federer":     15.8,
    "carlos alcaraz":     15.5, "alcaraz":     15.5,
    "jannik sinner":      15.3, "sinner":      15.3,
    "daniil medvedev":    15.0, "medvedev":    15.0,
    "alexander zverev":   14.8, "zverev":      14.8,
    "stefanos tsitsipas": 14.5, "tsitsipas":   14.5,
}

def fetch_player_utr(player_name: str) -> float:
    """Retourne le score UTR depuis la base locale."""
    try:
        key = player_name.lower()
        for k, v in _UTR_FALLBACK.items():
            if key in k or k in key:
                _log("OK", "tennis_api", f"UTR {player_name} → {v} (local)")
                return v
        _log("WARN", "tennis_api", f"UTR {player_name} inconnu → défaut 10.0")
        return 10.0
    except Exception as e:
        _log("ERROR", "tennis_api", f"fetch_player_utr — {e}")
        return 10.0


# ---------------------------------------------------------------------------
# Classement ATP
# ---------------------------------------------------------------------------

def fetch_atp_rankings() -> list[dict]:
    """Retourne le classement ATP."""
    try:
        result   = _get("get_standings", {"event_type": "ATP"})
        rankings = []
        for entry in result:
            rankings.append({
                "rank":   int(entry.get("place", 0)),
                "player": entry.get("player", "Inconnu"),
                "points": int(entry.get("points", 0)),
            })
        if rankings:
            return rankings

        _log("WARN", "tennis_api", "Classement ATP vide → repli statique")
        return [
            {"rank": 1, "player": "Jannik Sinner",    "points": 11830},
            {"rank": 2, "player": "Carlos Alcaraz",   "points": 9255},
            {"rank": 3, "player": "Novak Djokovic",   "points": 8685},
            {"rank": 4, "player": "Alexander Zverev", "points": 6885},
            {"rank": 5, "player": "Daniil Medvedev",  "points": 6685},
        ]
    except Exception as e:
        _log("ERROR", "tennis_api", f"fetch_atp_rankings — {e}")
        return []
