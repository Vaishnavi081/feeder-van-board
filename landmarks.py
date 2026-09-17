# landmarks.py

LANDMARKS = [
  { "id": "old-bus-stand", "name": "Old Bus Stand", "aliases": ["bus stand", "purana stand", "old stand", "patha stand"] },
  { "id": "petrol-pump-jn", "name": "Petrol Pump Junction", "aliases": ["petrol bunk", "bunk", "hp pump", "indian oil"] },
  { "id": "water-tank-circle", "name": "Water Tank Circle", "aliases": ["tank circle", "overhead tank", "ohtank", "tankbund", "tank bund"] },
  { "id": "panchayat-office", "name": "Panchayat Office", "aliases": ["gram panchayat", "gp office", "sarpanch office"] },
  { "id": "mandi-gate", "name": "Mandi Gate", "aliases": ["market gate", "sabzi mandi", "santha gate", "market yard"] },
  { "id": "rly-gate-4", "name": "Railway Gate No. 4", "aliases": ["gate no 4", "phatak", "rly gate", "railway gate"] },
  { "id": "hanuman-temple-jn", "name": "Hanuman Temple Junction", "aliases": ["temple jn", "anjaneya swamy", "hanuman gudi", "gudi"] },
  { "id": "school-jn", "name": "School Junction", "aliases": ["zp school", "govt school stop", "high school"] },
  { "id": "x-roads", "name": "Cross Roads (X Roads)", "aliases": ["x roads", "4 roads", "char rasta", "chowrasta", "chow rasta"] },
  { "id": "new-bridge", "name": "New Bridge", "aliases": ["kotha vantena", "naya pul", "bridge"] },
  { "id": "collectorate-jn", "name": "Collectorate Junction", "aliases": ["collector office", "rtc x roads", "collectorate"] },
  { "id": "station-rd", "name": "Railway Station Road", "aliases": ["station road", "rly station", "railway station"] },
]

LANDMARKS_BY_ID = { l["id"]: l for l in LANDMARKS }

ROUTES = [
  {
    "id": "kondapur-siddipet",
    "village": "Kondapur",
    "destination": "Siddipet Bus Stand",
    "stopIds": ["panchayat-office", "x-roads", "water-tank-circle", "old-bus-stand"],
  },
  {
    "id": "ghanpur-jangaon",
    "village": "Ghanpur",
    "destination": "Jangaon Railway Station",
    "stopIds": ["hanuman-temple-jn", "mandi-gate", "rly-gate-4", "station-rd"],
  },
  {
    "id": "regode-station",
    "village": "Regode",
    "destination": "Station Ghanpur",
    "stopIds": ["school-jn", "new-bridge", "rly-gate-4"],
  },
  {
    "id": "chinnakodur-siddipet",
    "village": "Chinnakodur",
    "destination": "Siddipet Bus Stand",
    "stopIds": ["petrol-pump-jn", "collectorate-jn", "old-bus-stand"],
  },
  {
    "id": "nangunoor-medak",
    "village": "Nangunoor",
    "destination": "Medak Bus Depot",
    "stopIds": ["panchayat-office", "x-roads", "petrol-pump-jn"],
  },
]

def route_label(route):
    return f"{route['village']} \u2192 {route['destination']}"

def get_stops_for_route(route_id):
    route = next((r for r in ROUTES if r["id"] == route_id), None)
    if not route:
        return []
    return [LANDMARKS_BY_ID[id] for id in route["stopIds"] if id in LANDMARKS_BY_ID]

import re

def normalize_text(text):
    # Remove spaces and non-alphanumeric chars for robust matching
    return re.sub(r'[^a-z0-9]', '', (text or "").lower())

def search_landmarks(query, route_id=None):
    pool = get_stops_for_route(route_id) if route_id else LANDMARKS
    q = normalize_text(query)
    if not q:
        return pool
    
    results = []
    for l in pool:
        name_norm = normalize_text(l["name"])
        aliases_norm = [normalize_text(a) for a in l["aliases"]]
        if q in name_norm or any(q in a for a in aliases_norm):
            results.append(l)
    return results
