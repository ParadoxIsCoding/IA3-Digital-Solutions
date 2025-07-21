import json
import requests
from flask import Flask, render_template, jsonify, request
import urllib3
from datetime import datetime

# Disable InsecureRequestWarning: CERTIFICATE_VERIFY_FAILED
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- Configuration for Weather Stations ---

STATIONS = {
    'station1': {
        'name': 'Ecowitt Station 1',
        'api_url': 'https://api.ecowitt.net/api/v3/device/real_time?application_key=2A514E07593482820CACAAB8FD0C73B2&api_key=17a5de25-fa25-4a18-9c86-78e93184c44c&mac=D8:BC:38:AA:96:AF&call_back=all'
    },
    'station2': {
        'name': 'Ecowitt Station 2',
        'api_url': 'https://api.ecowitt.net/api/v3/device/real_time?application_key=2A514E07593482820CACAAB8FD0C73B2&api_key=17a5de25-fa25-4a18-9c86-78e93184c44c&mac=D8:BC:38:AA:EF:E1&call_back=all'
    },
    'bom': {
        'name': 'BOM Brisbane',
        'api_url': 'https://reg.bom.gov.au/fwo/IDQ60901/IDQ60901.94575.json'
    }
}

# --- Data Fetching and Processing ---

def format_ecowitt_time(utc_timestamp):
    """Formats a UTC timestamp from the Ecowitt API to a local time dictionary."""
    if not utc_timestamp or not isinstance(utc_timestamp, int):
        return {'date': 'N/A', 'time': 'N/A', 'original': utc_timestamp}
    try:
        # Convert from seconds to a datetime object
        dt_object = datetime.fromtimestamp(utc_timestamp)
        return {
            'date': dt_object.strftime('%d/%m/%Y'),
            'time': dt_object.strftime('%H:%M:%S'),
            'original': utc_timestamp
        }
    except Exception:
        return {'date': 'N/A', 'time': 'N/A', 'original': utc_timestamp, 'malformed': True}


def fetch_ecowitt_data(api_url, station_name):
    """Fetches and processes weather data from the Ecowitt API."""
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json().get('data', {})
        
        # Extract the weather data dictionary
        weather_data = data.get('outdoor', {})
        
        # The 'last_update' timestamp is in the main data object
        last_update_timestamp = data.get('time')
        formatted_time_obj = format_ecowitt_time(last_update_timestamp)

        processed_observation = {
            'local_time_obj': formatted_time_obj,
            'air_temp': weather_data.get('temperature', {}).get('value'),
            'apparent_temp': 'N/A', # Ecowitt doesn't provide this directly
            'humidity': weather_data.get('humidity', {}).get('value'),
            'wind_dir': 'N/A', # Not in this part of the API response
            'wind_spd_kmh': data.get('wind', {}).get('wind_speed', {}).get('value'),
            'gust_kmh': data.get('wind', {}).get('wind_gust', {}).get('value'),
            'pressure_hpa': data.get('pressure', {}).get('absolute', {}).get('value'),
            'rain_since_9am': data.get('rainfall', {}).get('daily', {}).get('value')
        }

        return {
            'station_name': station_name,
            'last_updated_product': f"Last updated: {formatted_time_obj['date']} {formatted_time_obj['time']}",
            'observations': [processed_observation] # Return as a list to match template structure
        }, None

    except requests.exceptions.RequestException as e:
        return None, f"Error fetching Ecowitt data: {e}"
    except (json.JSONDecodeError, KeyError) as e:
        return None, f"Error processing Ecowitt data response: {e}"


@app.route('/')
def home():
    station_id = request.args.get('station', 'station1') # Default to station1
    station_info = STATIONS.get(station_id)

    if not station_info:
        return render_template('index.html', error=f"Station '{station_id}' not found.")

    if 'ecowitt' in station_info['name'].lower():
        weather_info, error_message = fetch_ecowitt_data(station_info['api_url'], station_info['name'])
    else:
        # Placeholder for your BOM fetching logic if you want to keep it
        weather_info, error_message = None, "BOM data fetching is not implemented in this version."

    if error_message:
        return render_template('index.html', error=error_message, current_station=station_id, stations=STATIONS)
        
    return render_template('index.html', weather=weather_info, current_station=station_id, stations=STATIONS)


@app.route('/api/weather')
def api_weather():
    station_id = request.args.get('station', 'station1')
    station_info = STATIONS.get(station_id)

    if not station_info:
        return jsonify({'error': f"Station '{station_id}' not found."}), 404

    if 'ecowitt' in station_info['name'].lower():
        weather_info, error_message = fetch_ecowitt_data(station_info['api_url'], station_info['name'])
    else:
        weather_info, error_message = None, "BOM data fetching not implemented."

    if error_message:
        return jsonify({'error': error_message}), 500
    if not weather_info:
        return jsonify({'error': 'No weather data available'}), 404
        
    return jsonify(weather_info)

if __name__ == '__main__':
    app.run(debug=True)