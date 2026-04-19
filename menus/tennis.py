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

BTN_RETOUR_TENNIS = [[InlineKeyboardButton("⬅️ Retour", callback_data="menu_tennis")]]
BTN_RETOUR_MENU = [[InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")]]


# ─── MENU PRINCIPAL TENNIS ────────────────────────────────────────────────────

async def show_tennis_menu(query):
    keyboard = [
        [InlineKeyboardButton("📅 Matchs du jour", callback_data="tennis_today")],
        [InlineKeyboardButton("💰 Value Bets", callback_data="tennis_value_bets")],
        [InlineKeyboardButton("⚔️ H2H", callback_data="tennis_h2h_menu")],
        [InlineKeyboardButton("🎯 Probabilités", callback_data="tennis_proba_menu")],
        [InlineKeyboardButton("🔔 Alertes", callback_data="tennis_alerts")],
        [InlineKeyboardButton("⬅️ Retour", callback_data="open_menu")],
    ]
    await query.edit_message_text(
        "🎾 **RADAR TENNIS — MODULE PREMIUM**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Sélectionne une option :\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ─── MATCHS DU JOUR ───────────────────────────────────────────────────────────

async def tennis_today(query):
    events = await fetch_sofa_matches(sport="tennis")
    body = format_matches_list(events, max_events=15)
    await query.edit_message_text(
        "📅 **Matchs du jour (Tennis)**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"{body}",
        reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS),
        parse_mode="Markdown",
    )


# ─── VALUE BETS ───────────────────────────────────────────────────────────────

async def tennis_value_bets(query):
    await query.edit_message_text("💰 **Value Bets Tennis**\n━━━━━━━━━━━━━━━━━━\n⏳ Analyse en cours...", parse_mode="Markdown")

    events = await fetch_sofa_matches(sport="tennis")

    if not events:
        await query.edit_message_text(
            "💰 **Value Bets Tennis**\n━━━━━━━━━━━━━━━━━━\n❌ Aucun match tennis trouvé.",
            reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS),
            parse_mode="Markdown",
        )
        return

    value_bets = []

    for event in events[:25]:
        event_id = event.get("id")
        home = event.get("homeTeam", {}).get("name", "N/A")
        away = event.get("awayTeam", {}).get("name", "N/A")

        if not event_id:
            continue

        # Probabilités SofaScore
        prob_data = await fetch_win_probability(event_id)
        if not prob_data:
            continue

        home_prob = prob_data.get("homeWinProbability", 0) / 100
        away_prob = prob_data.get("awayWinProbability", 0) / 100

        if home_prob <= 0 or away_prob <= 0:
            continue

        fair_home = round(1 / home_prob, 2)
        fair_away = round(1 / away_prob, 2)

        # Cotes — essaie odds d'abord puis winning-odds
        odds_data = await fetch_odds(event_id)
        if not odds_data:
            odds_data = await fetch_winning_odds(event_id)
        if not odds_data:
            continue

        book_home = book_away = None

        # Parsing format markets/choices
        markets = odds_data.get("markets", [])
        if markets:
            choices = markets[0].get("choices", [])
            for choice in choices:
                name = choice.get("name", "").lower()
                # Format décimal direct
                decimal = choice.get("decimalValue")
                if not decimal:
                    # Format fractionnel
                    frac = choice.get("fractionalValue", "")
                    if frac and "/" in frac:
                        try:
                            num, den = frac.split("/")
                            decimal = round(int(num) / int(den) + 1, 2)
                        except Exception:
                            pass
                if decimal:
                    decimal = float(decimal)
                    if "1" in name or "home" in name or name == "w1":
                        book_home = decimal
                    elif "2" in name or "away" in name or name == "w2":
                        book_away = decimal

        # Parsing format alternatif (winning-odds)
        if not book_home or not book_away:
            outcomes = odds_data.get("winningOdds", {}).get("outcomes", [])
            for outcome in outcomes:
                odd = outcome.get("decimalOdds")
                position = outcome.get("position", 0)
                if odd:
                    if position == 1:
                        book_home = float(odd)
                    elif position == 2:
                        book_away = float(odd)

        if not book_home or not book_away:
            continue

        edge_home = round((book_home / fair_home - 1) * 100, 1)
        edge_away = round((book_away / fair_away - 1) * 100, 1)

        if edge_home >= 5:
            value_bets.append({
                "match": f"{home} vs {away}",
                "bet": home,
                "cote": book_home,
                "fair": fair_home,
                "edge": edge_home,
            })
        if edge_away >= 5:
            value_bets.append({
                "match": f"{home} vs {away}",
                "bet": away,
                "cote": book_away,
                "fair": fair_away,
                "edge": edge_away,
            })

    if not value_bets:
        await query.edit_message_text(
            "💰 **Value Bets Tennis**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "❌ Aucun value bet détecté aujourd'hui.\n"
            "_(Edge minimum requis : 5%)_",
            reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS),
            parse_mode="Markdown",
        )
        return

    value_bets.sort(key=lambda x: x["edge"], reverse=True)

    lines = ["💰 **Value Bets Tennis**\n━━━━━━━━━━━━━━━━━━"]
    for vb in value_bets[:10]:
        lines.append(
            f"\n🎯 **{vb['match']}**\n"
            f"✅ {vb['bet']}\n"
            f"📊 Cote : `{vb['cote']}` | Fair : `{vb['fair']}`\n"
            f"💰 Edge : **+{vb['edge']}%**"
        )

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS),
        parse_mode="Markdown",
    )


# ─── H2H ──────────────────────────────────────────────────────────────────────

async def tennis_h2h_menu(query):
    events = await fetch_sofa_matches(sport="tennis")

    if not events:
        await query.edit_message_text(
            "❌ Aucun match tennis trouvé.",
            reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS),
            parse_mode="Markdown",
        )
        return

    keyboard = []
    for event in events[:10]:
        event_id = event.get("id")
        home = event.get("homeTeam", {}).get("shortName") or event.get("homeTeam", {}).get("name", "?")
        away = event.get("awayTeam", {}).get("shortName") or event.get("awayTeam", {}).get("name", "?")
        # Fix ? vs ? — si toujours vide on skip
        if not home or not away or home == away:
            continue
        if event_id:
            keyboard.append([
                InlineKeyboardButton(f"⚔️ {home} vs {away}", callback_data=f"tennis_h2h_{event_id}")
            ])

    keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data="menu_tennis")])

    await query.edit_message_text(
        "⚔️ **H2H Tennis — Choisis un match**\n━━━━━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def tennis_h2h(query, event_id: int):
    events = await fetch_sofa_matches(sport="tennis")
    home = away = "?"
    for e in events:
        if e.get("id") == event_id:
            home = e.get("homeTeam", {}).get("name", "?")
            away = e.get("awayTeam", {}).get("name", "?")
            break

    h2h_data = await fetch_h2h(event_id)
    text = format_h2h(h2h_data, home, away)

    keyboard = [
        [InlineKeyboardButton("⬅️ Retour H2H", callback_data="tennis_h2h_menu")],
        [InlineKeyboardButton("🏠 Menu Tennis", callback_data="menu_tennis")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ─── PROBABILITES ─────────────────────────────────────────────────────────────

async def tennis_proba_menu(query):
    events = await fetch_sofa_matches(sport="tennis")

    if not events:
        await query.edit_message_text(
            "❌ Aucun match tennis trouvé.",
            reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS),
            parse_mode="Markdown",
        )
        return

    keyboard = []
    for event in events[:10]:
        event_id = event.get("id")
        home = event.get("homeTeam", {}).get("shortName") or event.get("homeTeam", {}).get("name", "?")
        away = event.get("awayTeam", {}).get("shortName") or event.get("awayTeam", {}).get("name", "?")
        if not home or not away or home == away:
            continue
        if event_id:
            keyboard.append([
                InlineKeyboardButton(f"🎯 {home} vs {away}", callback_data=f"tennis_proba_{event_id}")
            ])

    keyboard.append([InlineKeyboardButton("⬅️ Retour", callback_data="menu_tennis")])

    await query.edit_message_text(
        "🎯 **Probabilités Tennis — Choisis un match**\n━━━━━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def tennis_proba(query, event_id: int):
    events = await fetch_sofa_matches(sport="tennis")
    home = away = "?"
    for e in events:
        if e.get("id") == event_id:
            home = e.get("homeTeam", {}).get("name", "?")
            away = e.get("awayTeam", {}).get("name", "?")
            break

    prob_data = await fetch_win_probability(event_id)

    if not prob_data:
        # Fallback : calcul depuis les cotes
        odds_data = await fetch_odds(event_id)
        if not odds_data:
            odds_data = await fetch_winning_odds(event_id)

        text = (
            f"🎯 **Probabilités — {home} vs {away}**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⚠️ Probabilités SofaScore non disponibles pour ce match.\n"
        )
    else:
        text = format_win_probability(prob_data, home, away)

    # Forme récente
    form_data = await fetch_pregame_form(event_id)
    if form_data:
        home_form = form_data.get("homeTeam", {}).get("form", "")
        away_form = form_data.get("awayTeam", {}).get("form", "")
        if home_form or away_form:
            text += (
                f"\n📋 **Forme récente**\n"
                f"• {home} : `{home_form}`\n"
                f"• {away} : `{away_form}`\n"
            )

    keyboard = [
        [InlineKeyboardButton("⬅️ Retour Probabilités", callback_data="tennis_proba_menu")],
        [InlineKeyboardButton("🏠 Menu Tennis", callback_data="menu_tennis")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ─── ALERTES ──────────────────────────────────────────────────────────────────

async def tennis_alerts(query):
    await query.edit_message_text(
        "🔔 **Alertes Tennis**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Module en préparation ⚙️",
        reply_markup=InlineKeyboardMarkup(BTN_RETOUR_TENNIS),
        parse_mode="Markdown",
    )


# ─── COMPAT ───────────────────────────────────────────────────────────────────

async def tennis_analysis(query):
    await tennis_value_bets(query)
