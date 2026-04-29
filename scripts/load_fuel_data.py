import os
import sys
import django
import pandas as pd

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuel_route.settings')
django.setup()

from stations.models import FuelStation


def load_fuel_data():
    from django.conf import settings

    csv_path = settings.FUEL_DATA_PATH
    print(f"Loading data from: {csv_path}")

    # Read CSV
    df = pd.read_csv(csv_path)

    # Clean column names
    df.columns = [col.strip() for col in df.columns]

    # Rename columns
    df = df.rename(columns={
        'OPIS Truckstop ID' : 'opis_id',
        'Truckstop Name'    : 'name',
        'Address'           : 'address',
        'City'              : 'city',
        'State'             : 'state',
        'Rack ID'           : 'rack_id',
        'Retail Price'      : 'retail_price',
    })

    # Clean data
    df['city']  = df['city'].str.strip()
    df['state'] = df['state'].str.strip()
    df['name']  = df['name'].str.strip()

    # Drop duplicates
    df = df.drop_duplicates(subset=['opis_id', 'name', 'city', 'state'])

    # Clear existing data
    FuelStation.objects.all().delete()
    print("Cleared existing stations...")

    # Bulk create
    stations = []
    for _, row in df.iterrows():
        stations.append(FuelStation(
            opis_id      = int(row['opis_id']),
            name         = row['name'],
            address      = row['address'],
            city         = row['city'],
            state        = row['state'],
            rack_id      = int(row['rack_id']),
            retail_price = float(row['retail_price']),
        ))

    FuelStation.objects.bulk_create(stations, batch_size=500)
    print(f" Successfully loaded {len(stations)} fuel stations!")


if __name__ == '__main__':
    load_fuel_data()