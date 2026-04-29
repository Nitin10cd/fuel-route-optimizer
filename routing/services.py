import requests
from django.conf import settings
from stations.services import find_optimal_fuel_stops


def get_coordinates_from_place(place_name):
    """
    Convert place name to coordinates using Nominatim (free).
    Example: "New York, NY" → (40.7128, -74.0060)
    """
    url    = "https://nominatim.openstreetmap.org/search"
    params = {
        'q'              : f"{place_name}, USA",
        'format'         : 'json',
        'limit'          : 1,
        'countrycodes'   : 'us',
    }
    headers = {'User-Agent': 'FuelRouteAPI/1.0'}

    response = requests.get(url, params=params, headers=headers, timeout=10)
    data     = response.json()

    if not data:
        raise ValueError(f"Location not found: {place_name}")

    return float(data[0]['lat']), float(data[0]['lon'])


def get_route_from_ors(start_coords, end_coords):
    """
    Get route from OpenRouteService API.
    Returns route geometry (coordinates) and total distance in miles.
    Only ONE API call made here.
    """
    api_key = settings.ORS_API_KEY
    url     = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"

    headers = {
        'Authorization' : api_key,
        'Content-Type'  : 'application/json',
    }

    body = {
        'coordinates': [
            [start_coords[1], start_coords[0]],  # ORS uses [lon, lat]
            [end_coords[1],   end_coords[0]],
        ]
    }

    response = requests.post(url, json=body, headers=headers, timeout=30)

    if response.status_code != 200:
        raise ValueError(f"ORS API error: {response.status_code} - {response.text}")

    data = response.json()

    # Extract route info
    feature     = data['features'][0]
    coordinates = feature['geometry']['coordinates']  # List of [lon, lat]
    summary     = feature['properties']['summary']
    
    distance_miles = summary['distance'] / 1609.34  # meters to miles
    duration_secs  = summary['duration']

    return {
        'coordinates'    : coordinates,
        'distance_miles' : round(distance_miles, 2),
        'duration_mins'  : round(duration_secs / 60, 1),
    }


def calculate_fuel_route(start, end):
    """
    Main service function — called by the API view.
    Steps:
    1. Geocode start and end (Nominatim)
    2. Get route from ORS (1 API call)
    3. Find optimal fuel stops along route
    4. Calculate total cost
    """
    # Step 1 — Geocode locations
    try:
        start_coords = get_coordinates_from_place(start)
    except Exception:
        raise ValueError(f"Could not find start location: '{start}'")

    try:
        end_coords = get_coordinates_from_place(end)
    except Exception:
        raise ValueError(f"Could not find end location: '{end}'")

    # Step 2 — Get route (single ORS API call)
    route_data = get_route_from_ors(start_coords, end_coords)

    coordinates    = route_data['coordinates']
    distance_miles = route_data['distance_miles']
    duration_mins  = route_data['duration_mins']

    # Step 3 — Find optimal fuel stops
    max_range = settings.VEHICLE_MAX_RANGE_MILES  # 500
    mpg       = settings.VEHICLE_MPG              # 10

    fuel_stops, total_fuel_cost = find_optimal_fuel_stops(
        route_coordinates = coordinates,
        max_range         = max_range,
        mpg               = mpg,
    )

    # Step 4 — Build response
    return {
        'route': {
            'start'          : start,
            'end'            : end,
            'start_coords'   : {'lat': start_coords[0], 'lng': start_coords[1]},
            'end_coords'     : {'lat': end_coords[0],   'lng': end_coords[1]},
            'distance_miles' : distance_miles,
            'duration_mins'  : duration_mins,
            'map_url'        : build_map_url(start_coords, end_coords, fuel_stops),
        },
        'vehicle': {
            'max_range_miles' : max_range,
            'mpg'             : mpg,
        },
        'fuel_stops'      : fuel_stops,
        'total_stops'     : len(fuel_stops),
        'total_fuel_cost' : f"${total_fuel_cost}",
    }


def build_map_url(start_coords, end_coords, fuel_stops):
    """
    Build a Google Maps URL showing route + all fuel stops.
    Free, no API key needed.
    """
    base = "https://www.google.com/maps/dir/"

    # Start point
    waypoints = [f"{start_coords[0]},{start_coords[1]}"]

    # Fuel stop waypoints (max 8 for Google Maps free)
    for stop in fuel_stops[:8]:
        waypoints.append(f"{stop['latitude']},{stop['longitude']}")

    # End point
    waypoints.append(f"{end_coords[0]},{end_coords[1]}")

    return base + "/".join(waypoints)