def format_fuel_results(mcp_result: dict) -> str:
    tool = mcp_result.get("tool")
    data = mcp_result.get("result", {})

    if not data.get("success"):
        return f"❌ {data.get('error', 'Erreur carburant inconnue')}"

    # Cas stations
    if tool in ("search_fuel_prices", "get_cheapest_station"):
        stations = (
            data.get("cheapest_stations")
            or data.get("results")
            or []
        )

        if not stations:
            return "Aucune station trouvée."

        out = "⛽ Stations trouvées :\n\n"
        for s in stations[:5]:
            out += (
                f"• {s['adresse']}, {s['ville']} ({s['cp']})\n"
                f"  💰 {s['price']:.3f} €/L\n"
            )

        return out

    # Cas statistiques
    if tool == "get_fuel_stats":
        stats = data.get("stats", {})
        gazole = stats.get("gazole", {})

        return (
            f"📊 Statistiques carburant ({stats.get('date')}):\n"
            f"Min: {gazole.get('min')} €/L\n"
            f"Max: {gazole.get('max')} €/L\n"
            f"Moyenne: {gazole.get('avg')} €/L"
        )

    return "Données carburant reçues mais non reconnues"
