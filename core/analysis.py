from typing import Optional


def build_auto_analysis(sport: str, surface: Optional[str] = None) -> str:
    text = (
        f"📈 **Analyse automatique — {sport}**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🧠 **Paramètres analysés par le moteur Shadow‑Edge :**\n"
        "• ELO / Power Rating (niveau réel des équipes/joueurs)\n"
        "• Momentum (forme récente, séries, dynamique)\n"
        "• Contexte (domicile / extérieur / pression / enjeu)\n"
    )
    if surface:
        text += f"• Surface : **{surface}**\n"
    text += (
        "• Météo (vent, température, humidité)\n"
        "• Style de jeu / match‑up\n"
        "• Historique des confrontations\n\n"
        "🔮 **Sortie du moteur prédictif :**\n"
        "→ Probabilités générées (placeholder pour l’instant)\n"
        "→ Prêt à connecter ton vrai modèle / API\n\n"
        "⚙️ Module en préparation — logique prête à accueillir tes données réelles."
    )
    return text
