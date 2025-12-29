from geopy.distance import geodesic

# ✅ Static mapping of city names to coordinates (you can extend this anytime)
LOCATION_COORDINATES = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "Houston": (29.7604, -95.3698),
    "San Francisco": (37.7749, -122.4194),
    "Miami": (25.7617, -80.1918),
    "Dallas": (32.7767, -96.7970),
    "Atlanta": (33.7490, -84.3880),
    "Boston": (42.3601, -71.0589),
    "Seattle": (47.6062, -122.3321),
}


def get_distance_between_locations(location1: str, location2: str):
    """
    Returns the distance in kilometers between two fixed location names.

    If one or both locations are not in LOCATION_COORDINATES,
    returns None (so your serializer can handle it gracefully).
    """
    coord1 = LOCATION_COORDINATES.get(location1)
    coord2 = LOCATION_COORDINATES.get(location2)

    if not coord1 or not coord2:
        return None  # Unknown location(s)

    distance_km = geodesic(coord1, coord2).km
    return round(distance_km, 2)
