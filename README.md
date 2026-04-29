# Fuel Route Optimizer 🚛

A production-ready Django REST API that calculates the most cost-effective fuel stops along any US road trip route — using real truck stop fuel price data, geospatial filtering, and a greedy optimization algorithm.

---

## Features

- Accepts any two US cities as start and end locations
- Returns optimal fuel stops along the route based on real prices
- Respects 500-mile maximum vehicle range
- Calculates total fuel cost at 10 miles per gallon
- Returns a Google Maps URL sho wing the full route with all fuel stops
- Minimum external API calls — maximum performance
- 6,967 real US truck stop fuel stations in database
- Precomputed geolocation for fast query response

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| Framework | Django 5.0.6 |
| API Layer | Django REST Framework 3.15 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Routing | OpenRouteService API (free) |
| Geocoding | Nominatim / OpenStreetMap (free) |
| Map | Google Maps URL (no API key needed) |
| Data Processing | Pandas |
| Distance Formula | Haversine |

---

## Project Structure

```
fuel-route-optimizer/
│
├── fuel_route/              # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── stations/                # Fuel station model & services
│   ├── models.py
│   ├── services.py
│   └── admin.py
│
├── routing/                 # Core API — route + fuel logic
│   ├── views.py
│   ├── services.py
│   └── urls.py
│
├── scripts/
│   ├── load_fuel_data.py    # CSV → Database loader
│   └── geocode_stations.py  # One-time geocoding script
│
├── data/
│   └── fuel_prices.csv      # 6,967 US truck stop prices
│
├── manage.py
├── requirements.txt
└── .env.example
```

---

## Setup Instructions

### 1. Clone & Virtual Environment

```bash
git clone https://github.com/Nitin10cd/fuel-route-optimizer
cd fuel-route-optimizer

python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install pandas --only-binary=:all:
```

### 3. Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
ORS_API_KEY=your_openrouteservice_api_key_here
```

> Get a free ORS API key at: https://openrouteservice.org/dev/#/signup

### 4. Database Setup

```bash
python manage.py migrate
```

### 5. Load Fuel Station Data

```bash
python scripts/load_fuel_data.py
```

Expected output:
```
Loading data from: ...fuel_prices.csv
Cleared existing stations...
Successfully loaded 6967 fuel stations!
```

### 6. Geocode Stations (One-time)

```bash
python scripts/geocode_stations.py
```

> This adds latitude and longitude to each station. Run once — results are saved to the database permanently.

### 7. Run Server

```bash
python manage.py runserver
```

---

## API Usage

### Endpoint

```
POST /api/route/
```

### Request Body

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
        "start_coords": {
            "lat": 40.7127281,
            "lng": -74.0060152
        },
        "end_coords": {
            "lat": 34.0536909,
            "lng": -118.242766
        },
        "distance_miles": 2793.62,
        "duration_mins": 2692.0,
        "map_url": "https://www.google.com/maps/dir/40.7127281,-74.0060152/..."
    },
    "vehicle": {
        "max_range_miles": 500,
        "mpg": 10
    },
    "fuel_stops": [
        {
            "station_name": "PETRO STOPPING CENTER #319",
            "city": "Mc Calla",
            "state": "AL",
            "latitude": 40.8333582,
            "longitude": -80.5455322,
            "price_per_gal": 3.126,
            "gallons": 37.82,
            "stop_cost": 118.2,
            "miles_driven": 410.1
        },
        {
            "station_name": "K AND H TRUCK PLAZA",
            "city": "Gilman",
            "state": "IL",
            "latitude": 40.7667015,
            "longitude": -87.992262,
            "price_per_gal": 3.159,
            "gallons": 39.32,
            "stop_cost": 124.22,
            "miles_driven": 818.6
        },
        {
            "station_name": "UNDERWOOD TRUCK STOP I 80",
            "city": "Underwood",
            "state": "IA",
            "latitude": 41.3872477,
            "longitude": -95.678862,
            "price_per_gal": 3.001,
            "gallons": 39.94,
            "stop_cost": 119.86,
            "miles_driven": 1192.1
        },
        {
            "station_name": "BIG SPRINGS TRUCK AND TRAVEL",
            "city": "Big Springs",
            "state": "NE",
            "latitude": 41.061381,
            "longitude": -102.074349,
            "price_per_gal": 3.074,
            "gallons": 34.03,
            "stop_cost": 104.62,
            "miles_driven": 1588.0
        },
        {
            "station_name": "PWI #535",
            "city": "Palisade",
            "state": "CO",
            "latitude": 39.1102587,
            "longitude": -108.350919,
            "price_per_gal": 3.379,
            "gallons": 38.88,
            "stop_cost": 131.39,
            "miles_driven": 1921.9
        },
        {
            "station_name": "MOAPA PAIUTE TRAVEL CENTER",
            "city": "Moapa",
            "state": "NV",
            "latitude": 36.75295,
            "longitude": -114.648614,
            "price_per_gal": 3.332,
            "gallons": 38.19,
            "stop_cost": 127.27,
            "miles_driven": 2325.2
        }
    ],
    "total_stops": 6,
    "total_fuel_cost": "$1593.07"
}
```

---

## How It Works

### Algorithm — Step by Step

```
1. Geocode start and end locations
   Convert city names to lat/long using Nominatim (free OSM API)

2. Fetch full route geometry
   Single API call to OpenRouteService
   Returns thousands of road coordinates from start to end

3. Greedy fuel stop algorithm
   Traverse route coordinates step by step
   When tank drops below 20% — trigger station search
   Find all stations within 50 mile radius using bounding box + haversine
   Pick cheapest available station
   Fill tank — record cost — continue driving

4. Build final response
   Fuel stops list + total cost + Google Maps URL with all waypoints
```

### Geospatial Query Optimization

```
Step 1 — Bounding Box Filter (fast DB query)
   Filter stations by lat/lon range in database
   Eliminates 95%+ of irrelevant stations instantly

Step 2 — Haversine Formula (precise distance)
   Calculates exact distance in miles between two coordinates
   Accounts for Earth's curvature
   Filters only stations within exact 50 mile radius

Result — Fast and accurate nearby station lookup
```

---

## External API Calls Per Request

| API | Purpose | Calls |
|---|---|---|
| Nominatim (OSM) | Geocode start location | 1 |
| Nominatim (OSM) | Geocode end location | 1 |
| OpenRouteService | Full route geometry | 1 |
| Google Maps | Map URL — no API call needed | 0 |
| **Total** | | **3 calls maximum** |

---

## Example Routes

| Route | Distance | Stops | Total Cost |
|---|---|---|---|
| New York, NY → Los Angeles, CA | 2,793 miles | 6 stops | $1,593 |
| Chicago, IL → Houston, TX | 1,092 miles | 2 stops | ~$620 |
| Seattle, WA → Miami, FL | 3,300 miles | 7 stops | ~$1,900 |

---

## Data

- Source: Real US truck stop fuel price dataset
- Total stations: 6,967
- Coverage: All 50 US states
- Fields: Station name, address, city, state, price per gallon, latitude, longitude
- Geocoding: One-time pre-processing using Nominatim — stored in database

---

## Future Improvements

- Dynamic Programming algorithm for globally optimal route planning
- PostgreSQL + PostGIS for production-grade geospatial queries
- Redis caching for repeated route lookups
- Live fuel price updates via scheduled scraping
- Docker + Docker Compose for containerized deployment
- JWT authentication for API security
- API rate limiting and throttling
- Comprehensive unit and integration test suite
- GCP cloud deployment

---

## Requirements

```
Django==5.0.6
djangorestframework==3.15.2
django-cors-headers==4.4.0
django-environ==0.11.2
requests==2.32.3
geopy==2.4.1
pandas
gunicorn==22.0.0
pytest==8.2.2
pytest-django==4.8.0
```

---

## License

MIT License — free to use and modify.
