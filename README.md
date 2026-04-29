# Fuel Route API 🚛

A Django REST API that calculates the optimal fuel stops along a US road trip route, minimizing fuel costs based on real truck stop prices.

## Features
- Finds cheapest fuel stations along any US route
- Respects 500-mile vehicle range limit
- Calculates total fuel cost at 10 MPG
- Returns Google Maps URL with all waypoints
- Single ORS API call for fast response

## Tech Stack
- Python 3.13 + Django 5.0.6
- Django REST Framework
- OpenRouteService API (routing)
- Nominatim/OSM (geocoding)
- SQLite (dev) / PostgreSQL (prod)
- 6967 real US truck stop fuel prices

## Setup Instructions

### 1. Clone & Virtual Environment
```bash
git clone <your-repo-url>
cd fuel_route_api
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install pandas --only-binary=:all:
```

### 3. Environment Variables
Create a `.env` file:

### 4. Database Setup
```bash
python manage.py migrate
python scripts/load_fuel_data.py
python scripts/geocode_stations.py
```

### 5. Run Server
```bash
python manage.py runserver
```

## API Usage
### Request
```json
{
    "start": "New York, NY",
    "end": "Los Angeles, CA"
}
```

### Response
```json
{
    "route": {
        "start": "New York, NY",
        "end": "Los Angeles, CA",
        "distance_miles": 2793.62,
        "duration_mins": 2692.0,
        "map_url": "https://www.google.com/maps/dir/..."
    },
    "vehicle": {
        "max_range_miles": 500,
        "mpg": 10
    },
    "fuel_stops": [...],
    "total_stops": 6,
    "total_fuel_cost": "$1593.07"
}
```

## Algorithm
1. Geocode start/end locations (Nominatim)
2. Fetch full route geometry (single ORS API call)
3. Sample route coordinates every ~20 points
4. At each point — if tank below 20% — find cheapest station within 50 miles
5. Calculate total fuel cost based on gallons used × price

## API Calls Made Per Request
- Nominatim: 2 calls (start + end geocoding)
- ORS: 1 call (full route)
- Total: 3 calls maximum ✅

### Endpoint