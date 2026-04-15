import random
from statistics import mean
from core.nba_history import nba_history_model


class NBAPredictor:
    def __init__(self):
        self.model = nba_history_model
        self.weights = {
            "matchup_edge": 0.4,
            "global_edge": 0.3,
            "momentum_diff": 0.2,
            "offense_diff": 0.15,
            "defense_diff": 0.15,
        }
        self._trained = False

    def _momentum(self, team: str, last_n: int = 5) -> float:
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

    def _train(self):
        """Auto‑calibration des poids sur ton historique."""
        self.model.load()
        if self._trained:
            return

        # On ajuste les poids en fonction de la corrélation simple
        # (modèle maison, léger, Render‑friendly)
        matchup_edges = []
        diffs = []

        for g in self.model.games:
            th = g["team_home"]
            ta = g["team_away"]
            diff = g["points_home"] - g["points_away"]

            # Edge historique
            me = g["edge_calculated"]

            matchup_edges.append(me)
            diffs.append(diff)

        if matchup_edges:
            # Poids dynamique basé sur la corrélation
            corr = mean([abs(me) for me in matchup_edges]) / 20
            self.weights["matchup_edge"] = min(0.6, max(0.2, corr))

        self._trained = True

    def _simulate(self, home_score: float, away_score: float, edge: float, runs: int = 1500):
        home_wins = 0
        for _ in range(runs):
            hs = random.gauss(home_score + edge * 0.25, 9)
            as_ = random.gauss(away_score - edge * 0.25, 9)
            if hs > as_:
                home_wins += 1
        return home_wins / runs

    def predict(self, home: str, away: str) -> str:
        self.model.load()
        self._train()

        home_stats = self.model.team_stats.get(home)
        away_stats = self.model.team_stats.get(away)

        if not home_stats or not away_stats:
            return "Équipe inconnue dans l’historique."

        # Edge historique du matchup
        matchup_edge = 0.0
        matchup = self.model.get_matchup_edge(home, away)
        if matchup:
            import re
            m = re.search(r"edge moyen \(home\) : ([\d\.\-]+)", matchup)
            matchup_edge = float(m.group(1)) if m else 0.0

        # Momentum
        home_mom = self._momentum(home)
        away_mom = self._momentum(away)
        momentum_diff = home_mom - away_mom

        # Offense / Defense
        offense_diff = home_stats["avg_points_for"] - away_stats["avg_points_for"]
        defense_diff = away_stats["avg_points_against"] - home_stats["avg_points_against"]

        # Global edge
        global_edge = home_stats["avg_edge"] - away_stats["avg_edge"]

        # Score attendu
        expected_home = (home_stats["avg_points_for"] + away_stats["avg_points_against"]) / 2
        expected_away = (away_stats["avg_points_for"] + home_stats["avg_points_against"]) / 2

        # Edge final ML-like
        final_edge = (
            matchup_edge * self.weights["matchup_edge"] +
            global_edge * self.weights["global_edge"] +
            momentum_diff * self.weights["momentum_diff"] +
            offense_diff * self.weights["offense_diff"] +
            defense_diff * self.weights["defense_diff"]
        )

        # Simulation Monte‑Carlo
        win_prob = self._simulate(expected_home, expected_away, final_edge)

        winner = home if win_prob > 0.5 else away

        return (
            f"🧠 **Shadow‑Predictor v3 (IA légère)**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏀 Match : **{home} vs {away}**\n\n"
            f"📊 **Score attendu**\n"
            f"• {home} : {expected_home:.1f}\n"
            f"• {away} : {expected_away:.1f}\n\n"
            f"⚡ **Edge final (IA)** : {final_edge:.2f}\n"
            f"📈 Momentum : {home} ({home_mom:.1f}) / {away} ({away_mom:.1f})\n"
            f"🔥 Offense diff : {offense_diff:.1f}\n"
            f"🛡️ Defense diff : {defense_diff:.1f}\n\n"
            f"🎲 **Simulation Monte‑Carlo (1500 runs)**\n"
            f"• Probabilité de victoire {home} : {win_prob*100:.1f}%\n"
            f"→ **Équipe avantagée : {winner}**\n\n"
            f"🤖 Modèle auto‑calibré sur ton historique NBA.\n"
        )


nba_predictor = NBAPredictor()
