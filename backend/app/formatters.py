"""Formateurs de réponse pour les sorties des outils MCP."""
from typing import Dict

def format_fuel_results(mcp_result: Dict) -> str:
    """Formate les résultats MCP carburant pour le LLM."""
    tool = mcp_result.get("tool")
    data = mcp_result.get("result", {})

    if not data.get("success"):
        return f"❌ Erreur: {data.get('error', 'Erreur inconnue')}"

    if tool == "get_cheapest_station":
        stations = data.get("cheapest_stations", [])
        location = data.get("location", "inconnue")
        fuel_type = data.get("fuel_type", "Gazole")

        if not stations:
            return f"Aucune station trouvée pour {location}"

        out = f"🚗 Stations les moins chères pour {fuel_type} à {location}:\n\n"
        for i, s in enumerate(stations, 1):
            out += (
                f"{i}. {s['adresse']}, {s['ville']} ({s['cp']})\n"
                f"   💰 {s['price']:.3f} €/L\n"
                f"   🕒 {s['updated']}\n\n"
            )
        return out

    if tool == "search_fuel_prices":
        stations = data.get("results", [])
        location = data.get("location", "inconnue")
        fuel_type = data.get("fuel_type", "Gazole")
        count = data.get("count", 0)

        if not stations:
            return f"Aucune station trouvée pour {location}"

        out = f"⛽ {count} stations pour {fuel_type} à {location}:\n\n"
        for i, s in enumerate(stations[:5], 1):
            out += (
                f"{i}. {s['adresse']}, {s['ville']} ({s['cp']})\n"
                f"   💰 {s['price']:.3f} €/L\n\n"
            )
        return out

    if tool == "get_fuel_stats":
        stats = data.get("stats", {})
        gazole = stats.get("gazole", {})

        return (
            f"📊 Statistiques nationales ({stats.get('date')}):\n\n"
            f"Stations: {stats.get('total_stations')}\n"
            f"Gazole:\n"
            f"• Min: {gazole.get('min'):.3f} €/L\n"
            f"• Max: {gazole.get('max'):.3f} €/L\n"
            f"• Moyenne: {gazole.get('avg'):.3f} €/L\n"
        )

    return "Données MCP reçues mais non formatées"


def format_traffic_results(mcp_result: Dict) -> str:
    """Formate les données de trafic Rennes pour le LLM."""
    data = mcp_result.get("result", {})

    if not data.get("success"):
        return f"❌ Erreur trafic: {data.get('error', 'Erreur inconnue')}"

    roads = data.get("roads", [])
    summary = data.get("summary", "Données de trafic")
    updated = data.get("updated", "maintenant")

    if not roads:
        return f"🟢 {summary} à Rennes (mis à jour à {updated})"

    txt = f"🚦 État du trafic Rennes - {summary} ({updated}):\n\n"

    critical = [r for r in roads if r.get("priority") == "critique"]
    high = [r for r in roads if r.get("priority") == "haute"]
    medium = [r for r in roads if r.get("priority") == "moyen"]

    def _fmt(item: Dict) -> str:
        street = item.get('street', '?')
        area = item.get('area')
        lat = item.get('lat')
        lon = item.get('lon')
        label = street if not area else f"{street} – {area}"
        if lat is not None and lon is not None:
            return f"{label} ({lat:.5f}, {lon:.5f})"
        return label

    if critical:
        txt += "🚨 CRITIQUE:\n"
        for r in critical:
            txt += f"  • {_fmt(r)} - {r.get('status', '?')}\n"
        txt += "\n"

    if high:
        txt += "⚠️ PERTURBATIONS:\n"
        for r in high:
            txt += f"  • {_fmt(r)} - {r.get('status', '?')}\n"
        txt += "\n"

    if medium:
        txt += "📍 DENSE:\n"
        for r in medium[:5]:
            txt += f"  • {_fmt(r)} - {r.get('status', '?')}\n"
        if len(medium) > 5:
            txt += f"  ... et {len(medium)-5} autres zones denses\n"

    txt += f"\n💡 {len(roads)} axe(s) perturbé(s) actuellement"
    return txt


def format_parking_results(mcp_result: Dict) -> str:
    """Formate les données de parkings Rennes pour le LLM."""
    data = mcp_result.get("result", {})

    if not data.get("success"):
        return f"❌ Erreur parkings: {data.get('error', 'Erreur inconnue')}"

    parkings = data.get("parkings", [])
    updated = data.get("updated", "maintenant")

    if not parkings:
        return f"⚠️ Aucune donnée de parking disponible (mis à jour à {updated})"

    txt = f"🅿️ Parkings à Rennes ({updated}):\n\n"

    for p in parkings[:10]:
        txt += f"• {p['name']}\n"
        txt += f"  {p['status']} - {p['available']}/{p['total']} places\n"
        if p.get('location'):
            txt += f"  📍 {p['location']}\n"
        txt += "\n"

    txt += f"💡 {len(parkings)} parking(s) surveillés"
    return txt


def format_drive_time_results(mcp_result: Dict) -> str:
    """Formate l'estimation du temps de trajet."""
    data = mcp_result.get("result", {})

    if not data.get("success"):
        return f"❌ Erreur estimation: {data.get('error', 'Erreur inconnue')}"

    origin = data.get("origin", ())
    destination = data.get("destination", ())
    distance_km = data.get("distance_km", 0)
    duration_base = data.get("duration_base_minutes", 0)
    duration_impact = data.get("traffic_impact_minutes", 0)
    duration_est = data.get("duration_estimated_minutes", 0)
    affected = data.get("affected_roads", [])
    warning = data.get("warning")

    txt = f"🚗 Estimation temps de trajet:\n\n"
    txt += f"  📍 Distance: {distance_km} km\n"
    txt += f"  ⏱️ Temps sans trafic: {duration_base:.0f}min\n"

    if duration_impact > 0:
        txt += f"  ⚠️ Impact trafic: +{duration_impact:.0f}min\n"
        txt += f"  📊 Estimation totale: {duration_est:.0f}min\n\n"

        if affected:
            txt += "Zones affectées:\n"
            for road in affected[:5]:
                street = road.get("street", "?")
                area = road.get("area", "")
                impact = road.get("impact_minutes", 0)
                status = road.get("status", "")
                label = f"{street} – {area}" if area else street
                txt += f"  • {label}: {status} (+{impact:.0f}min)\n"

        if warning:
            txt += f"\n⚠️ {warning}"
    else:
        txt += f"  ✅ Estimation: {duration_est:.0f}min (pas de perturbations)\n"

    return txt
