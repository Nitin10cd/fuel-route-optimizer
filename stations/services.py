import math
from .models import FuelStation


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in miles between two coordinates"""
    R = 3958.8  # Earth radius in miles

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def get_stations_near_point(lat, lon, radius_miles=50):
    """
    Get all geocoded stations within radius_miles of a point.
    Uses bounding box first (fast DB query), then haversine filter.
    """
    # Bounding box approximation (1 degree lat ≈ 69 miles)
    lat_delta = radius_miles / 69.0
    lon_delta = radius_miles / (69.0 * math.cos(math.radians(lat)))

    # Fast DB query using bounding box
    candidates = FuelStation.objects.filter(
        is_geocoded=True,
        latitude__range=(lat - lat_delta, lat + lat_delta),
        longitude__range=(lon - lon_delta, lon + lon_delta),
    ).values(
        'id', 'name', 'city', 'state',
        'retail_price', 'latitude', 'longitude'
    )

    # Precise haversine filter
    nearby = []
    for station in candidates:
        dist = haversine_distance(
            lat, lon,
            station['latitude'],
            station['longitude']
        )
        if dist <= radius_miles:
            station['distance_miles'] = round(dist, 2)
            nearby.append(station)

    # Sort by price (cheapest first)
    nearby.sort(key=lambda x: x['retail_price'])
    return nearby


def find_optimal_fuel_stops(route_coordinates, max_range=500, mpg=10):
    """
    Core algorithm — find cheapest fuel stops along route.

    Strategy:
    - Start with full tank
    - At each point check if we can reach next point
    - When fuel is low, find cheapest station within range
    - Always look ahead to avoid expensive stops
    """
    if not route_coordinates:
        return [], 0.0

    fuel_stops    = []
    total_cost    = 0.0
    current_range = max_range  # Start with full tank
    total_distance = 0.0

    # Sample route points every ~20 coords to avoid too many DB queries
    step = max(1, len(route_coordinates) // 100)
    sampled = route_coordinates[::step]

    i = 0
    while i < len(sampled) - 1:
        curr_point = sampled[i]
        next_point = sampled[i + 1]

        # Distance to next point
        seg_dist = haversine_distance(
            curr_point[1], curr_point[0],
            next_point[1], next_point[0]
        )
        total_distance += seg_dist

        # If we can't make it to next point — find cheapest stop NOW
        if current_range - seg_dist < max_range * 0.2:  # Refuel at 20% tank
            lat, lon = curr_point[1], curr_point[0]

            # Find stations nearby
            nearby = get_stations_near_point(lat, lon, radius_miles=50)

            if nearby:
                # Pick cheapest station
                best = nearby[0]

                # Calculate fuel needed to fill up
                fuel_needed  = (max_range - current_range) / mpg
                cost         = fuel_needed * best['retail_price']
                total_cost  += cost

                fuel_stops.append({
                    'station_name'  : best['name'],
                    'city'          : best['city'],
                    'state'         : best['state'],
                    'latitude'      : best['latitude'],
                    'longitude'     : best['longitude'],
                    'price_per_gal' : round(best['retail_price'], 3),
                    'gallons'       : round(fuel_needed, 2),
                    'stop_cost'     : round(cost, 2),
                    'miles_driven'  : round(total_distance, 1),
                })

                current_range = max_range  # Tank full again

        current_range -= seg_dist
        i += 1

    # Final fuel cost for remaining distance
    remaining_fuel = total_distance / mpg
    if fuel_stops:
        last_price  = fuel_stops[-1]['price_per_gal']
        total_cost += remaining_fuel * last_price

    return fuel_stops, round(total_cost, 2)