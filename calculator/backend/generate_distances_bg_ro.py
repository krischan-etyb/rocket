"""Generate BG-RO cross-country distances for distances_cache.json.

Uses:
- Pre-computed BG internal distances (from existing cache)
- Romanian road graph with Dijkstra shortest paths
- Border crossings: Ruse-Giurgiu, Vidin-Calafat, Dobrich-Constanta
"""

import json
import heapq
from pathlib import Path

# 27 unique BG oblast capital cities
BG_CAPITALS = [
    "sofia", "plovdiv", "varna", "burgas", "ruse",
    "stara zagora", "pleven", "sliven", "dobrich", "shumen",
    "pernik", "haskovo", "yambol", "pazardzhik", "blagoevgrad",
    "veliko tarnovo", "vratsa", "gabrovo", "vidin", "kyustendil",
    "montana", "lovech", "silistra", "targovishte", "razgrad",
    "smolyan", "kardzhali",
]

# 41 unique RO county capital cities (including Bucharest)
RO_CAPITALS = [
    "alba iulia", "arad", "pitesti", "bacau", "oradea",
    "bistrita", "botosani", "brasov", "braila", "bucharest",
    "buzau", "calarasi", "resita", "cluj-napoca", "constanta",
    "sfantu gheorghe", "targoviste", "craiova", "galati", "giurgiu",
    "targu jiu", "miercurea ciuc", "deva", "slobozia", "iasi",
    "baia mare", "drobeta-turnu severin", "targu mures", "piatra neamt",
    "slatina", "ploiesti", "satu mare", "zalau", "sibiu", "suceava",
    "alexandria", "timisoara", "tulcea", "vaslui", "ramnicu valcea",
    "focsani",
]

# Border crossings: (bg_city, ro_city, crossing_distance_km)
BORDER_CROSSINGS = [
    ("ruse", "giurgiu", 5),                       # Friendship Bridge
    ("vidin", "craiova", 90),                      # Danube Bridge 2 via Calafat
    ("vidin", "drobeta-turnu severin", 120),        # Via Calafat, along Danube
    ("dobrich", "constanta", 130),                  # Kardam - Negru Voda crossing
]

# Romanian road network: (city1, city2, distance_km)
RO_EDGES = [
    # === WALLACHIA (Southern Romania) ===
    ("bucharest", "ploiesti", 60),
    ("bucharest", "giurgiu", 65),
    ("bucharest", "alexandria", 140),
    ("bucharest", "calarasi", 125),
    ("bucharest", "slobozia", 130),
    ("bucharest", "targoviste", 80),
    ("bucharest", "pitesti", 120),
    ("bucharest", "constanta", 225),
    ("bucharest", "buzau", 130),
    ("giurgiu", "alexandria", 100),
    ("giurgiu", "calarasi", 130),
    ("alexandria", "slatina", 90),
    ("alexandria", "craiova", 140),
    ("slatina", "pitesti", 70),
    ("slatina", "craiova", 80),
    ("slatina", "ramnicu valcea", 90),
    ("craiova", "drobeta-turnu severin", 115),
    ("craiova", "targu jiu", 120),
    ("targu jiu", "ramnicu valcea", 100),
    ("targu jiu", "deva", 130),
    ("drobeta-turnu severin", "resita", 100),
    ("drobeta-turnu severin", "timisoara", 190),
    ("resita", "timisoara", 100),
    ("slobozia", "calarasi", 55),
    ("slobozia", "braila", 100),
    ("calarasi", "constanta", 170),
    # === PLOIESTI - BRASOV CORRIDOR ===
    ("ploiesti", "brasov", 130),
    ("ploiesti", "buzau", 90),
    ("ploiesti", "targoviste", 55),
    ("targoviste", "pitesti", 80),
    ("targoviste", "brasov", 110),
    ("pitesti", "ramnicu valcea", 70),
    # === MOLDOVA (Eastern Romania) ===
    ("buzau", "focsani", 90),
    ("buzau", "braila", 80),
    ("focsani", "galati", 100),
    ("focsani", "bacau", 110),
    ("galati", "braila", 25),
    ("galati", "tulcea", 150),
    ("galati", "vaslui", 110),
    ("braila", "tulcea", 125),
    ("braila", "constanta", 190),
    ("tulcea", "constanta", 130),
    ("vaslui", "iasi", 75),
    ("vaslui", "bacau", 85),
    ("iasi", "botosani", 40),
    ("iasi", "suceava", 145),
    ("iasi", "piatra neamt", 120),
    ("bacau", "piatra neamt", 60),
    ("suceava", "botosani", 40),
    ("suceava", "piatra neamt", 120),
    # === TRANSYLVANIA ===
    ("brasov", "sibiu", 140),
    ("brasov", "sfantu gheorghe", 30),
    ("sfantu gheorghe", "miercurea ciuc", 60),
    ("miercurea ciuc", "targu mures", 130),
    ("miercurea ciuc", "bacau", 140),
    ("sibiu", "alba iulia", 75),
    ("sibiu", "deva", 120),
    ("sibiu", "targu mures", 110),
    ("sibiu", "ramnicu valcea", 110),
    ("alba iulia", "deva", 65),
    ("alba iulia", "cluj-napoca", 100),
    ("alba iulia", "targu mures", 110),
    ("deva", "timisoara", 150),
    ("deva", "arad", 140),
    ("arad", "timisoara", 55),
    ("arad", "oradea", 120),
    ("oradea", "cluj-napoca", 155),
    ("oradea", "satu mare", 130),
    ("oradea", "zalau", 110),
    ("satu mare", "baia mare", 65),
    ("baia mare", "bistrita", 130),
    ("baia mare", "zalau", 100),
    ("bistrita", "cluj-napoca", 110),
    ("bistrita", "targu mures", 110),
    ("bistrita", "suceava", 190),
    ("cluj-napoca", "targu mures", 100),
    ("cluj-napoca", "zalau", 85),
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
    cache_path = Path(__file__).parent / "distances_cache.json"

    # Load existing cache (contains BG-BG distances)
    with cache_path.open(encoding="utf-8") as f:
        cache = json.load(f)

    # --- Extract BG internal distances for oblast capitals ---
    bg_set = set(BG_CAPITALS)
    bg_dist = {c: {} for c in BG_CAPITALS}
    for key, val in cache.items():
        parts = key.split("|")
        if len(parts) == 4 and parts[2] == "bg" and parts[3] == "bg":
            c1, c2 = parts[0], parts[1]
            if c1 in bg_set and c2 in bg_set:
                bg_dist[c1][c2] = val
    # Self-distances
    for c in BG_CAPITALS:
        bg_dist[c][c] = 0

    # --- Build RO road graph and compute shortest distances ---
    ro_set = set(RO_CAPITALS)
    for c1, c2, _ in RO_EDGES:
        if c1 not in ro_set:
            print(f"WARNING: '{c1}' in RO edges but not in RO_CAPITALS")
        if c2 not in ro_set:
            print(f"WARNING: '{c2}' in RO edges but not in RO_CAPITALS")

    ro_graph = {c: {} for c in RO_CAPITALS}
    for c1, c2, d in RO_EDGES:
        if c2 not in ro_graph[c1] or d < ro_graph[c1][c2]:
            ro_graph[c1][c2] = d
        if c1 not in ro_graph[c2] or d < ro_graph[c2][c1]:
            ro_graph[c2][c1] = d

    ro_dist = {c: dijkstra(ro_graph, c, RO_CAPITALS) for c in RO_CAPITALS}

    # --- Compute BG <-> RO distances via border crossings ---
    added = 0
    for bg_city in BG_CAPITALS:
        for ro_city in RO_CAPITALS:
            best = float("inf")
            for bg_border, ro_border, crossing_d in BORDER_CROSSINGS:
                bg_leg = bg_dist[bg_city].get(bg_border, float("inf"))
                ro_leg = ro_dist[ro_border].get(ro_city, float("inf"))
                total = bg_leg + crossing_d + ro_leg
                if total < best:
                    best = total

            if best < float("inf"):
                key_fwd = f"{bg_city}|{ro_city}|bg|ro"
                key_rev = f"{ro_city}|{bg_city}|ro|bg"
                cache[key_fwd] = round(best, 1)
                cache[key_rev] = round(best, 1)
                added += 2

    # Save
    with cache_path.open("w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"BG capitals: {len(BG_CAPITALS)}")
    print(f"RO capitals: {len(RO_CAPITALS)}")
    print(f"BG-RO entries added: {added}")
    print(f"Total cache entries: {len(cache)}")

    # Spot checks
    print("\n--- Spot checks ---")
    checks = [
        ("sofia", "bucharest", "~380-400"),
        ("ruse", "bucharest", "~70"),
        ("ruse", "giurgiu", "~5"),
        ("sofia", "timisoara", "~530-560"),
        ("burgas", "constanta", "~310-330"),
        ("plovdiv", "bucharest", "~350-390"),
        ("vidin", "craiova", "~90"),
        ("varna", "constanta", "~310"),
    ]
    for bg, ro, expected in checks:
        key = f"{bg}|{ro}|bg|ro"
        d = cache.get(key, "N/A")
        print(f"  {bg} -> {ro}: {d} km (expected {expected})")


if __name__ == "__main__":
    main()
