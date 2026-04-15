import random
from statistics import mean
from core.nba_history import nba_history_model


class NBAPredictor:
    def __init__(self):
        self.model = nba_history_model

    def _momentum(self, team: str, last_n: int = 5) -> float:
        """Momentum basé sur les 5 derniers matchs."""
        self.model.load()
        games = [g for g in self.model.games if g["team_home"] == team or g["team_away"] == team]
        games = games[-last_n:]
        if not games:
            return 0.0

        diffs = []
        for g in games:
            if g["team_home"] == team:
                diffs.append(g["points_home"] - g["points_away"])
            else:
                diffs.append(g["points_away"] - g["points_home"])

        return mean(diffs)

    def _simulate(self, home_score: float, away_score: float, edge: float, runs: int = 1000):
        """Simulation Monte‑Carlo simple."""
        home_wins = 0
        for _ in range(runs):
            hs = random.gauss(home_score + edge * 0.2, 8)
            as_ = random.gauss(away_score - edge * 0.2, 8)
            if hs > as_:
                home_wins += 1
        return home_wins / runs

    def predict(self, home: str, away: str) -> str:
        self.model.load()

        home_stats = self.model.team_stats.get(home)
        away_stats = self.model.team_stats.get(away)

        if not home_stats or not away_stats:
            return "Équipe inconnue dans l’historique."

        # Edge historique du matchup
        matchup = self.model.get_matchup_edge(home, away)
        if matchup:
            import re
            m = re.search(r"edge moyen \(home\) : ([\d\.\-]+)", matchup)
            matchup_edge = float(m.group(1)) if m else 0.0
        else:
            matchup_edge = 0.0

        # Momentum
        home_mom = self._momentum(home)
        away_mom = self._momentum(away)

        # Points moyens
        home_pf = home_stats["avg_points_for"]
        home_pa = home_stats["avg_points_against"]
        away_pf = away_stats["avg_points_for"]
        away_pa = away_stats["avg_points_against"]

        expected_home = (home_pf + away_pa) / 2
        expected_away = (away_pf + home_pa) / 2

        # Edge global
        global_edge = home_stats["avg_edge"] - away_stats["avg_edge"]

        # Edge final Shadow‑Edge v2
        final_edge = (
            matchup_edge * 0.4 +
            global_edge * 0.3 +
            (home_mom - away_mom) * 0.2
        )

        # Simulation Monte‑Carlo
        win_prob = self._simulate(expected_home, expected_away, final_edge)

        winner = home if win_prob > 0.5 else away

        return (
            f"🧠 **Shadow‑Predictor v2**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏀 Match : **{home} vs {away}**\n\n"
            f"📊 **Score attendu**\n"
            f"• {home} : {expected_home:.1f}\n"
            f"• {away} : {expected_away:.1f}\n\n"
            f"⚡ **Edge final (Shadow‑Edge)** : {final_edge:.2f}\n"
            f"📈 Momentum : {home} ({home_mom:.1f}) / {away} ({away_mom:.1f})\n\n"
            f"🎲 **Simulation Monte‑Carlo (1000 runs)**\n"
            f"• Probabilité de victoire {home} : {win_prob*100:.1f}%\n"
            f"→ **Équipe avantagée : {winner}**\n\n"
            f"📚 Basé sur ton historique NBA complet.\n"
        )


nba_predictor = NBAPredictor()
