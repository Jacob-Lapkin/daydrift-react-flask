import requests 
from dotenv import load_dotenv
import os

load_dotenv()

apikey = os.getenv("MAPS_KEY")


def get_location(lat, lng):
    """
    Takes in coordinates and returns address

    Args:
    lat: float -> the latitude of the users current location or desired location
    lng: float -> the longitude of the users current location or desired location

    Return:
    address: str -> the full address of that is produced from google maps geocoding
    """
    url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={apikey}'

    response = requests.get(url)
    data = response.json()

    if data['status'] == 'OK':
        address = data['results'][0]['formatted_address']
        return address
    else:
        return None