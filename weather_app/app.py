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
    }
}

# --- Data Fetching and Processing ---

def convert_temperature(temp_c, target_unit):
    """Converts temperature from Celsius to Fahrenheit if requested."""
    if temp_c is None or not isinstance(temp_c, (int, float)):
        return None  # Return None if input is invalid
    if target_unit.lower() == 'f':
        # Formula: F = C * 9/5 + 32
        return round((temp_c * 9 / 5) + 32, 1)
    return temp_c  # Return Celsius by default

def format_ecowitt_time(utc_timestamp):
    """Formats a UTC timestamp from the Ecowitt API to a local time dictionary."""
    if not utc_timestamp or not isinstance(utc_timestamp, int):
        return {'date': 'N/A', 'time': 'N/A', 'original': utc_timestamp}
    try:
        dt_object = datetime.fromtimestamp(utc_timestamp)
        return {
            'date': dt_object.strftime('%d/%m/%Y'),
            'time': dt_object.strftime('%H:%M:%S'),
            'original': utc_timestamp
        }
    except Exception:
        return {'date': 'N/A', 'time': 'N/A', 'original': utc_timestamp, 'malformed': True}

def fetch_ecowitt_data(api_url, station_name, units='c'):
    """Fetches and processes weather data from the Ecowitt API."""
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json().get('data', {})
        
        weather_data = data.get('outdoor', {})
        last_update_timestamp = data.get('time')
        formatted_time_obj = format_ecowitt_time(last_update_timestamp)

        # Get original temperature in Celsius
        temp_c = weather_data.get('temperature', {}).get('value')

        processed_observation = {
            'local_time_obj': formatted_time_obj,
            'air_temp': convert_temperature(temp_c, units),
            'apparent_temp': 'N/A',
            'humidity': weather_data.get('humidity', {}).get('value'),
            'wind_dir': 'N/A',
            'wind_spd_kmh': data.get('wind', {}).get('wind_speed', {}).get('value'),
            'gust_kmh': data.get('wind', {}).get('wind_gust', {}).get('value'),
            'pressure_hpa': data.get('pressure', {}).get('absolute', {}).get('value'),
            'rain_since_9am': data.get('rainfall', {}).get('daily', {}).get('value')
        }

        return {
            'station_name': station_name,
            'last_updated_product': f"Last updated: {formatted_time_obj['date']} {formatted_time_obj['time']}",
            'observations': [processed_observation]
        }, None

    except requests.exceptions.RequestException as e:
        return None, f"Error fetching Ecowitt data: {e}"
    except (json.JSONDecodeError, KeyError) as e:
        return None, f"Error processing Ecowitt data response: {e}"

@app.route('/')
def home():
    station_id = request.args.get('station', 'station1')
    units = request.args.get('units', 'c')  # Get units, default to 'c'
    station_info = STATIONS.get(station_id)

    if not station_info:
        return render_template('index.html', error=f"Station '{station_id}' not found.")

    weather_info, error_message = fetch_ecowitt_data(station_info['api_url'], station_info['name'], units)

    if error_message:
        return render_template('index.html', error=error_message, current_station=station_id, stations=STATIONS, current_units=units)
        
    return render_template('index.html', weather=weather_info, current_station=station_id, stations=STATIONS, current_units=units)

@app.route('/api/weather')
def api_weather():
    station_id = request.args.get('station', 'station1')
    units = request.args.get('units', 'c')
    station_info = STATIONS.get(station_id)

    if not station_info:
        return jsonify({'error': f"Station '{station_id}' not found."}), 404

    weather_info, error_message = fetch_ecowitt_data(station_info['api_url'], station_info['name'], units)

    if error_message:
        return jsonify({'error': error_message}), 500
    if not weather_info:
        return jsonify({'error': 'No weather data available'}), 404
        
    # Add the current unit to the API response
    weather_info['units'] = units.upper()
    return jsonify(weather_info)

if __name__ == '__main__':
    app.run(debug=True)