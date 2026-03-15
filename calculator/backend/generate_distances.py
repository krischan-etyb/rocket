"""Generate distances_cache.json for all 50 largest Bulgarian cities.

Uses a road graph with approximate distances between directly connected cities,
then computes shortest paths (Dijkstra) for all pairs.
Both directions (A->B and B->A) are stored automatically.
"""

import json
import heapq
from pathlib import Path

# 50 largest cities in Bulgaria
CITIES = [
    "sofia", "plovdiv", "varna", "burgas", "ruse",
    "stara zagora", "pleven", "sliven", "dobrich", "shumen",
    "pernik", "haskovo", "yambol", "pazardzhik", "blagoevgrad",
    "veliko tarnovo", "vratsa", "gabrovo", "asenovgrad", "vidin",
    "kazanlak", "kyustendil", "montana", "dimitrovgrad", "lovech",
    "silistra", "targovishte", "dupnitsa", "razgrad", "gorna oryahovitsa",
    "petrich", "gotse delchev", "karlovo", "smolyan", "sandanski",
    "sevlievo", "samokov", "lom", "nova zagora", "troyan",
    "aytos", "botevgrad", "velingrad", "svilengrad", "kardzhali",
    "harmanli", "panagyurishte", "chirpan", "pomorie", "popovo",
]

# Road connections with approximate distances in km.
# Only directly connected cities are listed; Dijkstra finds shortest paths.
EDGES = [
    # === SOFIA REGION ===
    ("sofia", "pernik", 35),
    ("sofia", "botevgrad", 57),
    ("sofia", "samokov", 60),
    ("sofia", "dupnitsa", 65),
    ("sofia", "kyustendil", 90),
    ("sofia", "blagoevgrad", 100),
    ("sofia", "pazardzhik", 112),
    ("sofia", "plovdiv", 150),
    ("sofia", "vratsa", 115),
    # === PERNIK ===
    ("pernik", "kyustendil", 70),
    ("pernik", "dupnitsa", 50),
    # === BOTEVGRAD CORRIDOR ===
    ("botevgrad", "lovech", 85),
    ("botevgrad", "pleven", 115),
    # === VRATSA-MONTANA-VIDIN ===
    ("vratsa", "montana", 50),
    ("montana", "vidin", 70),
    ("montana", "lom", 40),
    ("vidin", "lom", 90),
    # === PLEVEN-LOVECH ===
    ("pleven", "lovech", 35),
    ("pleven", "vratsa", 100),
    ("pleven", "veliko tarnovo", 95),
    ("pleven", "ruse", 160),
    # === LOVECH-TROYAN ===
    ("lovech", "troyan", 35),
    ("lovech", "gabrovo", 70),
    # === TROYAN ===
    ("troyan", "gabrovo", 65),
    # === VELIKO TARNOVO ===
    ("veliko tarnovo", "gabrovo", 45),
    ("veliko tarnovo", "gorna oryahovitsa", 10),
    ("veliko tarnovo", "sevlievo", 50),
    ("veliko tarnovo", "ruse", 100),
    # === GABROVO ===
    ("gabrovo", "sevlievo", 25),
    ("gabrovo", "kazanlak", 55),
    # === GORNA ORYAHOVITSA ===
    ("gorna oryahovitsa", "sevlievo", 45),
    ("gorna oryahovitsa", "popovo", 60),
    # === RUSE ===
    ("ruse", "razgrad", 70),
    ("ruse", "silistra", 120),
    ("ruse", "targovishte", 110),
    # === RAZGRAD-TARGOVISHTE-SHUMEN ===
    ("razgrad", "targovishte", 50),
    ("razgrad", "shumen", 60),
    ("razgrad", "popovo", 50),
    ("targovishte", "shumen", 40),
    ("targovishte", "popovo", 30),
    ("shumen", "popovo", 50),
    # === SHUMEN-VARNA-DOBRICH ===
    ("shumen", "varna", 90),
    ("shumen", "dobrich", 90),
    ("varna", "dobrich", 55),
    ("silistra", "dobrich", 120),
    # === PLOVDIV REGION ===
    ("plovdiv", "pazardzhik", 40),
    ("plovdiv", "asenovgrad", 20),
    ("plovdiv", "karlovo", 60),
    ("plovdiv", "stara zagora", 100),
    ("plovdiv", "haskovo", 90),
    ("plovdiv", "chirpan", 55),
    ("plovdiv", "dimitrovgrad", 50),
    ("plovdiv", "smolyan", 110),
    # === ASENOVGRAD ===
    ("asenovgrad", "smolyan", 90),
    # === PAZARDZHIK ===
    ("pazardzhik", "velingrad", 50),
    ("pazardzhik", "panagyurishte", 50),
    ("pazardzhik", "samokov", 80),
    # === KARLOVO ===
    ("karlovo", "kazanlak", 45),
    ("karlovo", "panagyurishte", 50),
    # === STARA ZAGORA ===
    ("stara zagora", "kazanlak", 35),
    ("stara zagora", "sliven", 100),
    ("stara zagora", "nova zagora", 50),
    ("stara zagora", "chirpan", 40),
    # === CHIRPAN ===
    ("chirpan", "dimitrovgrad", 30),
    ("chirpan", "nova zagora", 50),
    # === HASKOVO ===
    ("haskovo", "dimitrovgrad", 30),
    ("haskovo", "harmanli", 40),
    ("haskovo", "kardzhali", 50),
    ("haskovo", "svilengrad", 90),
    # === KARDZHALI ===
    ("kardzhali", "smolyan", 70),
    ("kardzhali", "dimitrovgrad", 60),
    # === HARMANLI-SVILENGRAD ===
    ("harmanli", "svilengrad", 50),
    ("harmanli", "dimitrovgrad", 40),
    # === SLIVEN-YAMBOL ===
    ("sliven", "yambol", 30),
    ("sliven", "nova zagora", 55),
    ("sliven", "kazanlak", 80),
    # === YAMBOL ===
    ("yambol", "nova zagora", 60),
    ("yambol", "burgas", 90),
    ("yambol", "aytos", 70),
    # === BURGAS COAST ===
    ("burgas", "aytos", 30),
    ("burgas", "pomorie", 20),
    ("burgas", "varna", 130),
    ("burgas", "sliven", 100),
    # === POMORIE ===
    ("pomorie", "aytos", 40),
    # === BLAGOEVGRAD ===
    ("blagoevgrad", "dupnitsa", 40),
    ("blagoevgrad", "sandanski", 75),
    ("blagoevgrad", "gotse delchev", 85),
    # === SANDANSKI-PETRICH ===
    ("sandanski", "petrich", 25),
    ("sandanski", "gotse delchev", 60),
    ("petrich", "gotse delchev", 70),
    # === SMOLYAN ===
    ("smolyan", "velingrad", 110),
    ("smolyan", "gotse delchev", 100),
    # === DUPNITSA-SAMOKOV ===
    ("dupnitsa", "samokov", 60),
    # === SAMOKOV ===
    ("samokov", "velingrad", 100),
    # === SILISTRA ===
    ("silistra", "razgrad", 100),
]


def dijkstra(graph, start, cities):
    """Shortest path from start to all other cities."""
    dist = {c: float("inf") for c in cities}
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in graph[u].items():
            nd = dist[u] + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def main():
    # Validate edges reference known cities
    city_set = set(CITIES)
    for c1, c2, _ in EDGES:
        if c1 not in city_set:
            print(f"WARNING: '{c1}' in edges but not in CITIES list")
        if c2 not in city_set:
            print(f"WARNING: '{c2}' in edges but not in CITIES list")

    # Build adjacency graph (undirected, keep shortest)
    graph = {c: {} for c in CITIES}
    for c1, c2, d in EDGES:
        if c2 not in graph[c1] or d < graph[c1][c2]:
            graph[c1][c2] = d
        if c1 not in graph[c2] or d < graph[c2][c1]:
            graph[c2][c1] = d

    # All-pairs shortest paths
    all_dist = {c: dijkstra(graph, c, CITIES) for c in CITIES}

    # Load existing cache to preserve international entries
    cache_path = Path(__file__).parent / "distances_cache.json"
    if cache_path.is_file():
        with cache_path.open(encoding="utf-8") as f:
            cache = json.load(f)
    else:
        cache = {}

    # Add Bulgarian city pairs (both directions come naturally from all_dist)
    added = 0
    unreachable = 0
    for c1 in CITIES:
        for c2 in CITIES:
            if c1 == c2:
                continue
            d = all_dist[c1][c2]
            if d < float("inf"):
                key = f"{c1}|{c2}|bg|bg"
                cache[key] = round(d, 1)
                added += 1
            else:
                unreachable += 1
                print(f"  UNREACHABLE: {c1} -> {c2}")

    # Save
    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"\nCities: {len(CITIES)}")
    print(f"Bulgarian pairs added: {added}")
    print(f"Unreachable pairs: {unreachable}")
    print(f"Total cache entries: {len(cache)}")

    # Spot-check some known distances
    print("\n--- Spot checks ---")
    checks = [
        ("sofia", "plovdiv", "~150"),
        ("sofia", "varna", "~440-470"),
        ("sofia", "burgas", "~380-400"),
        ("sofia", "veliko tarnovo", "~220"),
        ("plovdiv", "burgas", "~250-270"),
    ]
    for c1, c2, expected in checks:
        d = all_dist[c1][c2]
        print(f"  {c1} -> {c2}: {d:.1f} km (expected {expected})")


if __name__ == "__main__":
    main()
