import os
import sys
import django
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuel_route.settings')
django.setup()

from stations.models import FuelStation
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

geolocator = Nominatim(user_agent="fuel_route_api_v1")

# Cache to avoid duplicate API calls for same city/state
location_cache = {}


def geocode_city_state(city, state):
    key = f"{city},{state}"
    if key in location_cache:
        return location_cache[key]

    try:
        query = f"{city}, {state}, USA"
        location = geolocator.geocode(query, timeout=10)
        if location:
            coords = (location.latitude, location.longitude)
            location_cache[key] = coords
            return coords
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"  ⚠️ Geocoding error for {city}, {state}: {e}")

    location_cache[key] = None
    return None


def geocode_all_stations():
    # Only geocode stations that are not yet geocoded
    stations = FuelStation.objects.filter(is_geocoded=False)
    total    = stations.count()
    print(f"Geocoding {total} stations...")

    updated = 0
    failed  = 0

    for i, station in enumerate(stations, 1):
        coords = geocode_city_state(station.city, station.state)

        if coords:
            station.latitude    = coords[0]
            station.longitude   = coords[1]
            station.is_geocoded = True
            station.save(update_fields=['latitude', 'longitude', 'is_geocoded'])
            updated += 1
        else:
            failed += 1

        # Progress every 50 stations
        if i % 50 == 0:
            print(f"  Progress: {i}/{total} |  {updated} geocoded | ❌ {failed} failed")

        # Respect Nominatim rate limit (1 request/sec)
        time.sleep(1)

    print(f"\n Geocoding complete!")
    print(f"   Geocoded : {updated}")
    print(f"   Failed   : {failed}")
    print(f"   Total    : {total}")


if __name__ == '__main__':
    geocode_all_stations()