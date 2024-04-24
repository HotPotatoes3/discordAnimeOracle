import requests
import os

TOKEN2 = os.environ['TOKEN2']


def makeMALCall(url):
    # Set your API client ID in the X-MAL-CLIENT-ID header
    headers = {
        'X-MAL-CLIENT-ID': TOKEN2
    }

    # Make the API request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code} - {response.text}")

