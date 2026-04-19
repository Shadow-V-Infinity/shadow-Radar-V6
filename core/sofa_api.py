import datetime
from typing import Optional, List, Dict

import aiohttp

SOFA_BASE_URL = "https://api.sofascore.com/api/v1"
SOFA_WEB_URL = "https://www.sofascore.com/api/v1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0 Mobile Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Ch-Ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": "Android",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


# ─── MATCHS DU JOUR ───────────────────────────────────────────────────────────

async def fetch_sofa_matches(
    sport: Optional[str] = None,
    tournament_id: Optional[int] = None,
    date: Optional[str] = None,
) -> List[Dict]:
    if date is None:
        date = datetime.date.today().strftime("%Y-%m-%d")

    if tournament_id is not None:
        url = f"{SOFA_BASE_URL}/unique-tournament/{tournament_id}/scheduled-events/{date}"
    elif sport is not None:
        url = f"{SOFA_BASE_URL}/sport/{sport}/scheduled-events/{date}"
    else:
        return []

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return data.get("events", [])
    except Exception:
        return []


# ─── H2H ──────────────────────────────────────────────────────────────────────

async def fetch_h2h(event_id: int) -> Dict:
    """Historique des confrontations directes entre les deux joueurs/équipes."""
    url = f"{SOFA_BASE_URL}/event/{event_id}/h2h"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


# ─── WIN PROBABILITY ──────────────────────────────────────────────────────────

async def fetch_win_probability(event_id: int) -> Dict:
    """Probabilité de victoire calculée par SofaScore."""
    url = f"{SOFA_WEB_URL}/event/{event_id}/win-probability"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


# ─── COTES BOOKMAKERS ─────────────────────────────────────────────────────────

async def fetch_odds(event_id: int) -> Dict:
    """Cotes des bookmakers partenaires SofaScore."""
    url = f"{SOFA_WEB_URL}/event/{event_id}/odds/1/featured"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


async def fetch_winning_odds(event_id: int) -> Dict:
    """Cotes gagnantes SofaScore."""
    url = f"{SOFA_WEB_URL}/event/{event_id}/winning-odds"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


# ─── PREGAME FORM ─────────────────────────────────────────────────────────────

async def fetch_pregame_form(event_id: int) -> Dict:
    """Forme récente des deux équipes/joueurs avant le match."""
    url = f"{SOFA_WEB_URL}/event/{event_id}/pregame-form"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


# ─── STATISTIQUES MATCH ───────────────────────────────────────────────────────

async def fetch_match_stats(event_id: int) -> Dict:
    """Stats détaillées du match (service, return, break points...)."""
    url = f"{SOFA_BASE_URL}/event/{event_id}/statistics"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


# ─── LINEUPS ──────────────────────────────────────────────────────────────────

async def fetch_lineups(event_id: int) -> Dict:
    """Compositions / joueurs confirmés."""
    url = f"{SOFA_WEB_URL}/event/{event_id}/lineups"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


# ─── INCIDENTS / POINT BY POINT ───────────────────────────────────────────────

async def fetch_incidents(event_id: int) -> Dict:
    """Incidents du match (buts, cartons, sets...)."""
    url = f"{SOFA_WEB_URL}/event/{event_id}/incidents"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


async def fetch_point_by_point(event_id: int) -> Dict:
    """Point par point (tennis uniquement)."""
    url = f"{SOFA_WEB_URL}/event/{event_id}/point-by-point"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


# ─── META ─────────────────────────────────────────────────────────────────────

async def fetch_event_meta(event_id: int) -> Dict:
    """Infos générales du match."""
    url = f"{SOFA_WEB_URL}/event/{event_id}/meta"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


# ─── CLASSEMENTS ──────────────────────────────────────────────────────────────

async def fetch_rankings(sport: str = "tennis") -> Dict:
    """Classements ATP/WTA ou autres sports."""
    url = f"{SOFA_BASE_URL}/sport/{sport}/rankings"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
    except Exception:
        return {}


# ─── FORMATAGE ────────────────────────────────────────────────────────────────

def format_matches_list(events: List[Dict], max_events: int = 10) -> str:
    if not events:
        return "Aucun match trouvé pour aujourd'hui.\n"

    import datetime as dt

    lines = []
    for e in events[:max_events]:
        home = e.get("homeTeam", {}).get("name", "N/A")
        away = e.get("awayTeam", {}).get("name", "N/A")
        time_ts = e.get("startTimestamp")
        if time_ts:
            d = dt.datetime.fromtimestamp(time_ts)
            time_str = d.strftime("%H:%M")
        else:
            time_str = "??:??"
        lines.append(f"• {time_str} — {home} vs {away}")
    return "\n".join(lines)


def format_h2h(h2h_data: Dict, home: str, away: str) -> str:
    """Formate les données H2H pour Telegram."""
    if not h2h_data:
        return "❌ H2H non disponible"

    team_duel = h2h_data.get("teamDuel", {})
    home_wins = team_duel.get("homeWins", 0)
    away_wins = team_duel.get("awayWins", 0)
    draws = team_duel.get("draws", 0)

    return (
        f"⚔️ **H2H — {home} vs {away}**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ {home} : {home_wins} victoires\n"
        f"✅ {away} : {away_wins} victoires\n"
        f"🤝 Nuls : {draws}\n"
    )


def format_win_probability(prob_data: Dict, home: str, away: str) -> str:
    """Formate les probabilités de victoire pour Telegram."""
    if not prob_data:
        return "❌ Probabilités non disponibles"

    home_prob = prob_data.get("homeWinProbability", 0)
    away_prob = prob_data.get("awayWinProbability", 0)

    return (
        f"🎯 **Probabilités SofaScore**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"• {home} : {home_prob:.1f}%\n"
        f"• {away} : {away_prob:.1f}%\n"
    )
