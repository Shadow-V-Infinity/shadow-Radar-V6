import datetime
from typing import Optional, List, Dict

import aiohttp

SOFA_BASE_URL = "https://api.sofascore.com/api/v1"


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
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return data.get("events", [])
    except Exception:
        return []


def format_matches_list(events: List[Dict], max_events: int = 10) -> str:
    if not events:
        return "Aucun match trouvé pour aujourd’hui.\n"

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
