def format_traffic_results(traffic_data: dict) -> str:
    """
    Formate les données de trafic Rennes pour le LLM.
    - traffic_data: dict retourné par TrafficScraper.get_traffic_status()
    """
    if not traffic_data.get("success"):
        return f"❌ Erreur récupération trafic: {traffic_data.get('error', 'inconnue')}"

    summary = traffic_data.get("summary", "")
    updated = traffic_data.get("updated", "")
    roads = traffic_data.get("roads", [])

    # Priorité critique/haute pour LLM (max 10 tronçons)
    top_roads = [r for r in roads if r["priority"] in ("critique", "haute")][:10]

    text = f"🕒 Trafic Rennes – mise à jour {updated}\n"
    text += summary + "\n\n"

    for r in top_roads:
        text += f"• {r['street']} — {r['status']}\n"

    return text
