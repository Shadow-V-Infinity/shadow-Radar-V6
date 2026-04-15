import csv
from pathlib import Path
from collections import defaultdict
from typing import Dict, Tuple, List, Optional

HISTORY_FILE = Path("data/nba_history.csv")


class NBAHistoryModel:
    def __init__(self, csv_path: Path = HISTORY_FILE):
        self.csv_path = csv_path
        self.games: List[dict] = []
        self.team_stats: Dict[str, dict] = {}
        self.matchup_edge: Dict[Tuple[str, str], List[float]] = {}
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        if not self.csv_path.exists():
            return

        with self.csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row["points_home"] = int(row["points_home"])
                    row["points_away"] = int(row["points_away"])
                    row["edge_calculated"] = float(row["edge_calculated"])
                except Exception:
                    continue
                self.games.append(row)

        self._build_team_stats()
        self._build_matchup_edges()
        self._loaded = True

    def _build_team_stats(self):
        stats = defaultdict(lambda: {
            "games": 0,
            "points_for": 0,
            "points_against": 0,
            "edge_sum": 0.0,
        })

        for g in self.games:
            th = g["team_home"]
            ta = g["team_away"]
            ph = g["points_home"]
            pa = g["points_away"]
            edge = g["edge_calculated"]

            stats[th]["games"] += 1
            stats[th]["points_for"] += ph
            stats[th]["points_against"] += pa
            stats[th]["edge_sum"] += edge

            stats[ta]["games"] += 1
            stats[ta]["points_for"] += pa
            stats[ta]["points_against"] += ph
            stats[ta]["edge_sum"] += -edge

        for team, s in stats.items():
            g = max(s["games"], 1)
            s["avg_points_for"] = s["points_for"] / g
            s["avg_points_against"] = s["points_against"] / g
            s["avg_edge"] = s["edge_sum"] / g

        self.team_stats = stats

    def _build_matchup_edges(self):
        matchup = defaultdict(list)
        for g in self.games:
            th = g["team_home"]
            ta = g["team_away"]
            edge = g["edge_calculated"]
            matchup[(th, ta)].append(edge)
        self.matchup_edge = matchup

    def get_team_summary(self, team: str) -> Optional[str]:
        self.load()
        s = self.team_stats.get(team)
        if not s:
            return None
        return (
            f"📊 **Profil {team} (historique)**\n"
            f"• Matchs pris en compte : {s['games']}\n"
            f"• Points marqués moyens : {s['avg_points_for']:.1f}\n"
            f"• Points encaissés moyens : {s['avg_points_against']:.1f}\n"
            f"• Edge moyen (Shadow) : {s['avg_edge']:.2f}\n"
        )

    def get_matchup_edge(self, home: str, away: str) -> Optional[str]:
        self.load()
        edges = self.matchup_edge.get((home, away))
        if not edges:
            return None
        avg_edge = sum(edges) / len(edges)
        return (
            f"🧠 **Matchup historique {home} vs {away}**\n"
            f"• Matchs dans l’historique : {len(edges)}\n"
            f"• Edge moyen (home) : {avg_edge:.2f}\n"
            f"→ Plus l’edge est élevé, plus {home} domine historiquement.\n"
        )


nba_history_model = NBAHistoryModel()
