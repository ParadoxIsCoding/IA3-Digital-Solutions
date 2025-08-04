import json
import requests
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import urllib3
from datetime import datetime
from functools import wraps

# Disable InsecureRequestWarning: CERTIFICATE_VERIFY_FAILED
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session management

# --- Configuration for Weather Stations ---

STATIONS = {
    'station1': {
        'name': 'G Block',
        'api_url': 'https://api.ecowitt.net/api/v3/device/real_time?application_key=2A514E07593482820CACAAB8FD0C73B2&api_key=17a5de25-fa25-4a18-9c86-78e93184c44c&mac=D8:BC:38:AA:96:AF&call_back=all'
    },
    'station2': {
        'name': 'Art Block',
        'api_url': 'https://api.ecowitt.net/api/v3/device/real_time?application_key=2A514E07593482820CACAAB8FD0C73B2&api_key=17a5de25-fa25-4a18-9c86-78e93184c44c&mac=D8:BC:38:AA:EF:E1&call_back=all'
    }
}

# --- Utility Functions ---

def safe_float(value):
    """Safely converts a value to a float, handling None or non-numeric strings."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def to_celsius(temp, unit_str):
    """Converts a temperature value to Celsius if it's in Fahrenheit."""
    temp_val = safe_float(temp)
    if temp_val is None:
        return None
    if unit_str and 'f' in unit_str.lower():
        # Formula: C = (F - 32) * 5/9
        return (temp_val - 32) * 5 / 9
    return temp_val  # Assume Celsius if not Fahrenheit

def convert_display_temperature(temp_c, target_unit):
    """Converts a Celsius temperature to the target display unit (e.g., Fahrenheit)."""
    if temp_c is None:
        return None
    if target_unit.lower() == 'f':
        # Formula: F = C * 9/5 + 32
        return round((temp_c * 9 / 5) + 32, 1)
    return round(temp_c, 1) # Return Celsius by default, rounded

def format_ecowitt_time(utc_timestamp_str):
    """Formats a UTC timestamp string from the Ecowitt API safely."""
    ts = safe_float(utc_timestamp_str)
    if ts is None:
        return {'date': 'N/A', 'time': 'N/A', 'original': utc_timestamp_str}
    try:
        dt_object = datetime.fromtimestamp(ts)
        return {
            'date': dt_object.strftime('%d/%m/%Y'),
            'time': dt_object.strftime('%H:%M:%S'),
            'original': utc_timestamp_str
        }
    except (ValueError, TypeError):
        return {'date': 'N/A', 'time': 'N/A', 'original': utc_timestamp_str, 'malformed': True}

# --- Data Fetching Logic ---

def fetch_ecowitt_data(api_url, station_name, display_units='c'):
    """Fetches and processes weather data from the Ecowitt API."""
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        api_data = response.json().get('data', {})

        if not api_data:
            return None, "Received empty data payload from API."

        # --- Extract Main Sections ---
        outdoor_data = api_data.get('outdoor', {})
        feels_like_data = api_data.get('feels_like', {})
        pressure_data = api_data.get('pressure', {}).get('absolute', {})
        wind_data = api_data.get('wind', {})
        rainfall_data = api_data.get('rainfall', {})
        
        # --- Time ---
        formatted_time_obj = format_ecowitt_time(api_data.get('time'))

        # --- Temperature (Unit-aware) ---
        temp_from_api = outdoor_data.get('temperature', {})
        temp_c = to_celsius(temp_from_api.get('value'), temp_from_api.get('unit'))
        
        # --- Feels Like (Unit-aware) ---
        feels_like_from_api = feels_like_data.get('temperature', {})
        feels_like_c = to_celsius(feels_like_from_api.get('value'), feels_like_from_api.get('unit'))

        processed_observation = {
            'local_time_obj': formatted_time_obj,
            'air_temp': convert_display_temperature(temp_c, display_units),
            'apparent_temp': convert_display_temperature(feels_like_c, display_units),
            'humidity': safe_float(outdoor_data.get('humidity', {}).get('value')),
            'wind_spd_kmh': safe_float(wind_data.get('wind_speed', {}).get('value')),
            'gust_kmh': safe_float(wind_data.get('wind_gust', {}).get('value')),
            'pressure_val': safe_float(pressure_data.get('value')),
            'pressure_unit': pressure_data.get('unit', 'hPa'),
            'rain_since_9am': safe_float(rainfall_data.get('daily', {}).get('value'))
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

# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Flask Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = 'Invalid credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    station_id = request.args.get('station', 'station1')
    units = request.args.get('units', 'c')
    station_info = STATIONS.get(station_id)

    if not station_info:
        return render_template('index.html', error=f"Station '{station_id}' not found.", stations=STATIONS, current_station=station_id, current_units=units)

    weather_info, error_message = fetch_ecowitt_data(station_info['api_url'], station_info['name'], units)

    if error_message:
        return render_template('index.html', error=error_message, current_station=station_id, stations=STATIONS, current_units=units)
        
    return render_template('index.html', weather=weather_info, current_station=station_id, stations=STATIONS, current_units=units)


@app.route('/api/weather')
@login_required
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
        
    weather_info['units'] = units.upper()
    return jsonify(weather_info)

if __name__ == '__main__':
    app.run(debug=True)