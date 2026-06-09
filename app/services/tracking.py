from math import radians, cos, sin, asin, sqrt

# Haversine distance in kilometers
def haversine_km(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km


def estimate_eta_minutes(distance_km, speed_kmh=30.0):
    if distance_km is None:
        return None
    if speed_kmh <= 0:
        return None
    hours = distance_km / speed_kmh
    minutes = int(round(hours * 60))
    return max(1, minutes)


def calculate_eta_from_driver(driver_lat, driver_lng, dest_lat, dest_lng, speed_kmh=30.0):
    if None in (driver_lat, driver_lng, dest_lat, dest_lng):
        return None
    dist = haversine_km(driver_lat, driver_lng, dest_lat, dest_lng)
    return estimate_eta_minutes(dist, speed_kmh)
