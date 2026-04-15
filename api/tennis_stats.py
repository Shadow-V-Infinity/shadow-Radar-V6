# api/tennis_stats.py
#
# Source : Jeff Sackmann / Tennis Abstract
# https://github.com/JeffSackmann/tennis_atp
# Licence : CC BY-NC-SA 4.0

import io
import requests
import pandas as pd
from functools import lru_cache
from datetime import datetime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

RAW          = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master"
CURRENT_YEAR = datetime.now().year
FORM_MATCHES = 10      # nb de matchs récents pour la forme
ELO_DEFAULT  = 1500.0  # ELO de départ pour joueur inconnu
ELO_K        = 32      # facteur K standard


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

def _log(level: str, msg: str):
    icons = {"OK": "🟢", "ERROR": "🔴", "WARN": "🟡", "INFO": "🔵"}
    print(f"{icons.get(level, '⚪')} [tennis_stats] {msg}")


# ---------------------------------------------------------------------------
# Chargement CSV depuis GitHub
# ---------------------------------------------------------------------------

def _fetch_csv(url: str) -> pd.DataFrame | None:
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return pd.read_csv(io.StringIO(resp.text), low_memory=False)
    except Exception as e:
        _log("ERROR", f"fetch_csv({url}) → {e}")
        return None


@lru_cache(maxsize=4)
def _load_matches(year: int) -> pd.DataFrame:
    """Charge les matchs ATP d'une saison (mis en cache)."""
    df = _fetch_csv(f"{RAW}/atp_matches_{year}.csv")
    if df is None:
        _log("WARN", f"Pas de données pour {year}")
        return pd.DataFrame()
    _log("OK", f"Matchs {year} chargés ({len(df)} lignes)")
    return df


@lru_cache(maxsize=1)
def _load_players() -> pd.DataFrame:
    """Charge le fichier joueurs (player_id, name, hand, dob, ioc)."""
    df = _fetch_csv(f"{RAW}/atp_players.csv")
    if df is None:
        return pd.DataFrame()
    _log("OK", f"Joueurs chargés ({len(df)} entrées)")
    return df


@lru_cache(maxsize=1)
def _load_rankings() -> pd.DataFrame:
    """Charge le classement ATP courant."""
    df = _fetch_csv(f"{RAW}/atp_rankings_current.csv")
    if df is None:
        return pd.DataFrame()
    _log("OK", f"Classements chargés ({len(df)} entrées)")
    return df


def _get_recent_matches(n_years: int = 2) -> pd.DataFrame:
    """Concatène les matchs des n dernières saisons."""
    frames = [
        _load_matches(y)
        for y in range(CURRENT_YEAR - n_years + 1, CURRENT_YEAR + 1)
    ]
    frames = [df for df in frames if not df.empty]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Recherche d'un joueur (tolérant aux noms partiels / abréviés)
# ---------------------------------------------------------------------------

def _find_player_name(name: str, df_matches: pd.DataFrame) -> str | None:
    """
    Cherche le nom exact dans les colonnes winner_name / loser_name.
    Gère les abréviations type 'F. Cobolli' ou 'Cobolli'.
    """
    name_lower = name.lower().strip()

    all_names: set[str] = set()
    for col in ("winner_name", "loser_name"):
        if col in df_matches.columns:
            all_names.update(df_matches[col].dropna().unique())

    # 1. Correspondance exacte
    for n in all_names:
        if n.lower() == name_lower:
            return n

    # 2. Nom saisi contenu dans le nom complet (ex: 'Cobolli' → 'F. Cobolli')
    for n in all_names:
        parts = n.lower().split()
        if name_lower in parts or name_lower == n.lower().split(".")[-1].strip():
            return n

    # 3. Nom complet contient la saisie
    for n in all_names:
        if name_lower in n.lower():
            return n

    return None


# ---------------------------------------------------------------------------
# Calcul ELO
# ---------------------------------------------------------------------------

def _compute_elo(df: pd.DataFrame) -> dict[str, float]:
    """
    Calcule les scores ELO de tous les joueurs à partir des matchs.
    Algorithme K=32, probabilité logistique standard.
    """
    elo: dict[str, float] = {}

    if "tourney_date" in df.columns:
        df = df.sort_values("tourney_date")

    for _, row in df.iterrows():
        w = row.get("winner_name")
        l = row.get("loser_name")
        if pd.isna(w) or pd.isna(l):
            continue

        ew = elo.get(w, ELO_DEFAULT)
        el = elo.get(l, ELO_DEFAULT)

        exp_w = 1 / (1 + 10 ** ((el - ew) / 400))

        elo[w] = ew + ELO_K * (1 - exp_w)
        elo[l] = el + ELO_K * (0 - (1 - exp_w))

    return elo


# ---------------------------------------------------------------------------
# Forme récente
# ---------------------------------------------------------------------------

def _get_form(player_name: str, df: pd.DataFrame, n: int = FORM_MATCHES) -> str:
    """Retourne une chaîne type 'WWLWW' des n derniers matchs."""
    results = []

    df_sorted = (
        df.sort_values("tourney_date", ascending=False)
        if "tourney_date" in df.columns
        else df
    )

    for _, row in df_sorted.iterrows():
        if len(results) >= n:
            break
        if row.get("winner_name") == player_name:
            results.append("W")
        elif row.get("loser_name") == player_name:
            results.append("L")

    return "".join(results) if results else "WWWWW"


# ---------------------------------------------------------------------------
# Stats de service
# ---------------------------------------------------------------------------

def _get_service_stats(player_name: str, df: pd.DataFrame) -> float:
    """
    Retourne le % de points gagnés sur son service (moyenne sur 20 derniers matchs).
    Colonnes Sackmann : w_1stWon, w_1stIn, w_2ndWon, w_svpt (gagnant)
                        l_1stWon, l_1stIn, l_2ndWon, l_svpt (perdant)
    """
    try:
        w_rows = df[df["winner_name"] == player_name][
            ["w_1stIn", "w_1stWon", "w_2ndWon", "w_svpt"]
        ].dropna().tail(20)

        l_rows = df[df["loser_name"] == player_name][
            ["l_1stIn", "l_1stWon", "l_2ndWon", "l_svpt"]
        ].dropna().tail(20)

        total_won  = (
            w_rows["w_1stWon"].sum() + w_rows["w_2ndWon"].sum()
            + l_rows["l_1stWon"].sum() + l_rows["l_2ndWon"].sum()
        )
        total_svpt = w_rows["w_svpt"].sum() + l_rows["l_svpt"].sum()

        if total_svpt > 0:
            return round(total_won / total_svpt * 100, 1)

    except Exception as e:
        _log("WARN", f"service_stats({player_name}) → {e}")

    return 65.0  # défaut


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------

def get_player_stats(player_name: str) -> dict:
    """
    Retourne un dict complet pour un joueur :
      - elo         (float)
      - form        (str, ex: 'WWLWW')
      - service_won (float, %)
      - rank        (int)
      - found_name  (str, nom exact dans la DB)
    """
    result = {
        "elo":         ELO_DEFAULT,
        "form":        "WWWWW",
        "service_won": 65.0,
        "rank":        100,
        "found_name":  player_name,
    }

    try:
        df = _get_recent_matches(n_years=2)
        if df.empty:
            _log("WARN", "Aucune donnée de matchs disponible")
            return result

        found = _find_player_name(player_name, df)
        if not found:
            _log("WARN", f"Joueur '{player_name}' introuvable → valeurs par défaut")
            return result

        result["found_name"] = found
        _log("INFO", f"'{player_name}' → '{found}'")

        # ELO
        elo_map        = _compute_elo(df)
        result["elo"]  = round(elo_map.get(found, ELO_DEFAULT), 1)

        # Forme
        result["form"] = _get_form(found, df)

        # Stats service
        result["service_won"] = _get_service_stats(found, df)

        # Classement
        df_rank = _load_rankings()
        if not df_rank.empty:
            df_players = _load_players()
            if not df_players.empty:
                mask = df_players["name_last"].str.lower().str.contains(
                    found.split()[-1].lower(), na=False
                )
                matching = df_players[mask]
                if not matching.empty:
                    pid      = matching.iloc[0]["player_id"]
                    rank_row = df_rank[df_rank["player"] == pid]
                    if not rank_row.empty:
                        result["rank"] = int(rank_row.iloc[-1]["rank"])

        _log("OK", (
            f"{found} → ELO={result['elo']} | Forme={result['form']} "
            f"| Svc={result['service_won']}% | Rank=#{result['rank']}"
        ))

    except Exception as e:
        _log("ERROR", f"get_player_stats({player_name}) → {e}")

    return result
