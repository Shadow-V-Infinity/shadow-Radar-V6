from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.sofa_api import (
    fetch_sofa_matches,
    format_matches_list,
    fetch_h2h,
    fetch_win_probability,
    fetch_odds,
    fetch_winning_odds,
    fetch_pregame_form,
    format_h2h,
    format_win_probability,
)
from core.tennis_probability_engine import compute_match, format_result

BTN_RETOUR_TENNIS = [[InlineKeyboardButton("⬅️ Retour", callback_data="menu_tennis")]]
BTN_RETOUR_MENU = [[InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")]]

async def show_tennis_menu(query):
    keyboard = [
        [InlineKeyboardButton("📅 Matchs du jour", callback_data="tennis_today")],
        [InlineKeyboardButton("💰 Value Bets", callback_data="tennis_value_bets")],
        [InlineKeyboardButton("⚔️ H2H", callback_data="tennis_h2h_menu")],
        [InlineKeyboardButton("🎯 Probabilités", callback_data="tennis_proba_menu")],
        [InlineKeyboardButton("🔔 Alertes", callback_data="tennis_alerts")],
        [InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")],
    ]
    text = "🎾 **RADAR TENNIS — MODULE PREMIUM**\n━━━━━━━━━━━━━━━━━━\nSélectionne une option :\n"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def tennis_today(query):
    events = await fetch_sofa_matches(sport="tennis")
    body = format_matches_list(events, max_events=15)
    text = f"📅 **Matchs du jour (Tennis)**\n━━━━━━━━━━━━━━━━━━\n{body}"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS), parse_mode="Markdown")

async def tennis_value_bets(query):
    await query.edit_message_text("💰 **Value Bets Tennis**\n━━━━━━━━━━━━━━━━━━\n⏳ Analyse en cours...", parse_mode="Markdown")
    events = await fetch_sofa_matches(sport="tennis")
    if not events:
        await query.edit_message_text("💰 **Value Bets Tennis**\n━━━━━━━━━━━━━━━━━━\n❌ Aucun match tennis trouvé.", reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS), parse_mode="Markdown")
        return
    value_bets = []
    for event in events[:25]:
        event_id = event.get("id")
        home = event.get("homeTeam", {}).get("name", "N/A")
        away = event.get("awayTeam", {}).get("name", "N/A")
        if not event_id: continue
        prob_data = await fetch_win_probability(event_id)
        if not prob_data: continue
        home_prob = prob_data.get("homeWinProbability", 0) / 100
        away_prob = prob_data.get("awayWinProbability", 0) / 100
        if home_prob <= 0 or away_prob <= 0: continue
        fair_home = round(1 / home_prob, 2)
        fair_away = round(1 / away_prob, 2)
        odds_data = await fetch_odds(event_id) or await fetch_winning_odds(event_id)
        if not odds_data: continue
        book_home = book_away = None
        markets = odds_data.get("markets", [])
        if markets:
            choices = markets[0].get("choices", [])
            for choice in choices:
                name = choice.get("name", "").lower()
                decimal = choice.get("decimalValue")
                if decimal:
                    decimal = float(decimal)
                    if "1" in name or "home" in name: book_home = decimal
                    elif "2" in name or "away" in name: book_away = decimal
        if not book_home or not book_away: continue
        edge_home = round((book_home / fair_home - 1) * 100, 1)
        edge_away = round((book_away / fair_away - 1) * 100, 1)
        if edge_home >= 5: value_bets.append({"match": f"{home} vs {away}", "bet": home, "cote": book_home, "fair": fair_home, "edge": edge_home})
        if edge_away >= 5: value_bets.append({"match": f"{home} vs {away}", "bet": away, "cote": book_away, "fair": fair_away, "edge": edge_away})
    if not value_bets:
        await query.edit_message_text("💰 **Value Bets Tennis**\n━━━━━━━━━━━━━━━━━━\n❌ Aucun value bet détecté.\n_(Edge min : 5%)_", reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS), parse_mode="Markdown")
        return
    value_bets.sort(key=lambda x: x["edge"], reverse=True)
    lines = ["💰 **Value Bets Tennis**\n━━━━━━━━━━━━━━━━━━"]
    for vb in value_bets[:10]:
        lines.append(f"\n🎯 **{vb['match']}**\n✅ {vb['bet']}\n📊 Cote : `{vb['cote']}` | Edge : **+{vb['edge']}%**")
    await query.edit_message_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS), parse_mode="Markdown")

async def tennis_h2h_menu(query):
    events = await fetch_sofa_matches(sport="tennis")
    if not events:
        await query.edit_message_text("❌ Aucun match trouvé.", reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS), parse_mode="Markdown")
        return
    keyboard = []
    for event in events[:10]:
        event_id = event.get("id")
        home = event.get("homeTeam", {}).get("shortName", "Home")
        away = event.get("awayTeam", {}).get("shortName", "Away")
        if event_id: keyboard.append([InlineKeyboardButton(f"⚔️ {home} vs {away}", callback_data=f"tennis_h2h_{event_id}")])
    keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data="menu_tennis")])
    await query.edit_message_text("⚔️ **H2H Tennis — Choisis un match**\n━━━━━━━━━━━━━━━━━━", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def tennis_h2h(query, event_id: int):
    h2h_data = await fetch_h2h(event_id)
    text = format_h2h(h2h_data, "Joueur 1", "Joueur 2")
    keyboard = [[InlineKeyboardButton("⬅️ Retour H2H", callback_data="tennis_h2h_menu")], [InlineKeyboardButton("🏠 Menu Tennis", callback_data="menu_tennis")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def tennis_proba_menu(query):
    events = await fetch_sofa_matches(sport="tennis")
    if not events:
        await query.edit_message_text("❌ Aucun match trouvé.", reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS), parse_mode="Markdown")
        return
    keyboard = [[InlineKeyboardButton(f"🎯 {e.get('homeTeam', {}).get('shortName')} vs {e.get('awayTeam', {}).get('shortName')}", callback_data=f"tennis_proba_{e.get('id')}")] for e in events[:10] if e.get('id')]
    keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data="menu_tennis")])
    await query.edit_message_text("🎯 **Probabilités Tennis**\n━━━━━━━━━━━━━━━━━━", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def tennis_proba(query, event_id: int):
    prob_data = await fetch_win_probability(event_id)
    text = format_win_probability(prob_data, "Home", "Away") if prob_data else "⚠️ Données indisponibles."
    keyboard = [[InlineKeyboardButton("⬅️ Retour", callback_data="tennis_proba_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def tennis_alerts(query):
    await query.edit_message_text("🔔 **Alertes Tennis**\n━━━━━━━━━━━━━━━━━━\nModule en préparation ⚙️", reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS), parse_mode="Markdown")

async def tennis_analysis(query):
    await tennis_value_bets(query)
