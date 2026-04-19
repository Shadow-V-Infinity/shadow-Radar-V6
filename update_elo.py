import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import schedule
import logging
import os
from git import Repo

# Configurer le logging
logging.basicConfig(
    filename='data/tennis-elo-data/elo_update.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Chemins des fichiers
ATP_FILE = "data/tennis-elo-data/elo atp.csv"
WTA_FILE = "data/tennis-elo-data/elo wta.csv"
HISTORY_FILE = "data/tennis-elo-data/elo_history.csv"  # Historique complet

def load_data():
    """Charge les fichiers CSV avec toutes les colonnes."""
    def load_single_file(file_path):
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            # Renommer les colonnes pour standardiser (ex: "Player" → "name")
            df = df.rename(columns={
                "Player": "name",
                "Elo Rank": "elo_rank",
                "hElo Rank": "helo_rank",
                "cElo Rank": "celo_rank",
                "gElo Rank": "gelo_rank",
                "Peak Elo": "peak_elo",
                "Peak Month": "peak_month",
                "Log diff": "log_diff"
            })
            # Ajouter player_id si absent (utiliser l'index comme ID temporaire)
            if "player_id" not in df.columns:
                df["player_id"] = df.index + 1  # IDs temporaires
            return df
        else:
            return pd.DataFrame(columns=[
                "player_id", "name", "elo_rank", "elo", "helo_rank", "hElo",
                "celo_rank", "cElo", "gelo_rank", "gElo", "peak_elo",
                "peak_month", "ATP Rank", "log_diff", "last_updated"
            ])

    atp_df = load_single_file(ATP_FILE)
    wta_df = load_single_file(WTA_FILE)

    # Charger ou créer l'historique
    if os.path.exists(HISTORY_FILE):
        history_df = pd.read_csv(HISTORY_FILE)
    else:
        history_df = pd.DataFrame(columns=[
            "player_id", "date", "elo", "hElo", "cElo", "gElo", "tour"
        ])

    return atp_df, wta_df, history_df

def save_data(atp_df, wta_df, history_df):
    """Sauvegarde les fichiers et pousse sur GitHub."""
    # Garder uniquement les colonnes originales pour éviter les conflits
    atp_df.to_csv(ATP_FILE, index=False)
    wta_df.to_csv(WTA_FILE, index=False)
    history_df.to_csv(HISTORY_FILE, index=False)

    try:
        repo = Repo(".")
        repo.git.add("data/tennis-elo-data/")
        repo.index.commit("🤖 Mise à jour automatique des Elo (ATP/WTA)")
        origin = repo.remote(name="origin")
        origin.push()
        logging.info("Fichiers poussés sur GitHub.")
    except Exception as e:
        logging.error(f"Erreur Git: {e}")

def scrape_uts_elo(player_name, tour="atp"):
    """Scrape l'Elo d'un joueur depuis UTS (par nom)."""
    # TODO: Trouver l'ID du joueur sur UTS (nécessite une étape supplémentaire)
    # Pour l'instant, on simule une mise à jour locale
    logging.info(f"Simulation: Mise à jour pour {player_name} (Tour: {tour})")
    return {
        "name": player_name,
        "elo": int(pd.np.random.uniform(1500, 2500)),  # Simulation
        "hElo": int(pd.np.random.uniform(1500, 2500)),
        "cElo": int(pd.np.random.uniform(1500, 2500)),
        "gElo": int(pd.np.random.uniform(1500, 2500)),
        "last_updated": pd.Timestamp.now().strftime("%Y-%m-%d")
    }

def update_elo_files():
    """Met à jour les Elo ATP/WTA."""
    atp_df, wta_df, history_df = load_data()

    # Mettre à jour les 5 premiers joueurs ATP/WTA (pour l'exemple)
    for _, row in atp_df.head(5).iterrows():
        player_data = scrape_uts_elo(row["name"], "atp")
        if player_data:
            # Mettre à jour les colonnes Elo
            atp_df.loc[atp_df["name"] == row["name"], [
                "elo", "hElo", "cElo", "gElo", "last_updated"
            ]] = [
                player_data["elo"], player_data["hElo"],
                player_data["cElo"], player_data["gElo"],
                player_data["last_updated"]
            ]

            # Ajouter à l'historique
            history_df = pd.concat([history_df, pd.DataFrame([{
                "player_id": row["player_id"],
                "date": player_data["last_updated"],
                "elo": player_data["elo"],
                "hElo": player_data["hElo"],
                "cElo": player_data["cElo"],
                "gElo": player_data["gElo"],
                "tour": "atp"
            })], ignore_index=True)

        time.sleep(2)

    # Même logique pour WTA (optionnel)
    for _, row in wta_df.head(5).iterrows():
        player_data = scrape_uts_elo(row["name"], "wta")
        if player_data:
            wta_df.loc[wta_df["name"] == row["name"], [
                "elo", "hElo", "cElo", "gElo", "last_updated"
            ]] = [
                player_data["elo"], player_data["hElo"],
                player_data["cElo"], player_data["gElo"],
                player_data["last_updated"]
            ]

            history_df = pd.concat([history_df, pd.DataFrame([{
                "player_id": row["player_id"],
                "date": player_data["last_updated"],
                "elo": player_data["elo"],
                "hElo": player_data["hElo"],
                "cElo": player_data["cElo"],
                "gElo": player_data["gElo"],
                "tour": "wta"
            })], ignore_index=True)

        time.sleep(2)

    save_data(atp_df, wta_df, history_df)

def job():
    logging.info("Début de la mise à jour des Elo...")
    update_elo_files()
    logging.info("Mise à jour terminée.")

if __name__ == "__main__":
    # Exécution immédiate
    job()

    # Planification quotidienne
    schedule.every().day.at("08:00").do(job)

    while True:
        schedule.run_pending()
        time.sleep(60)
