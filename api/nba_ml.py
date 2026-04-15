import pandas as pd
import os
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from .nba_data import get_historical_data

class NBAPredictor:
    def __init__(self, model_type="linear"):
        self.model_type = model_type
        if model_type == "linear":
            self.model = LinearRegression()
        else:
            self.model = RandomForestRegressor(n_estimators=100)
        self.features = [
            "home_off_rating", "away_def_rating", "home_pace", "away_pace",
            "home_last_5_win_pct", "away_last_5_win_pct",
            "home_rest_days", "away_rest_days", "home_injury_impact", "is_home_game"
        ]
        self.target = "point_diff"
        self.trained = False

    def train(self, historical_data):
        """Entraîne le modèle avec des données historiques."""
        X = historical_data[self.features]
        y = historical_data[self.target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        self.trained = True
        return self.model.score(X_test, y_test)

    def predict(self, home_stats, away_stats):
        """Prédit un match."""
        if not self.trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez train() d'abord.")

        input_data = pd.DataFrame([{**home_stats, **away_stats, "is_home_game": 1}])
        point_diff = self.model.predict(input_data[self.features])[0]
        home_score = 110 + point_diff / 2
        away_score = 110 - point_diff / 2
        confidence = min(90, max(50, 50 + abs(point_diff) * 1.5))
        return {
            "home_score": round(home_score),
            "away_score": round(away_score),
            "confidence": round(confidence),
            "point_diff": round(point_diff, 1)
        }

# Instance globale du prédicteur
predictor = NBAPredictor(model_type="random_forest")  # Plus précis que la régression linéaire

# Entraînement automatique au démarrage si des données existent
if os.path.exists("data/nba_historical.csv"):
    historical_data = pd.read_csv("data/nba_historical.csv")
    predictor.train(historical_data)
else:
    print("⚠️ Fichier data/nba_historical.csv introuvable. Le modèle ne sera pas entraîné.")
    print("Générez-le avec: python -c 'from api.nba_data import get_historical_data; get_historical_data(500).to_csv(\"data/nba_historical.csv\", index=False)'")
