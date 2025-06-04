import json
import requests
from flask import Flask, render_template, jsonify
import urllib3 # Import urllib3 to disable SSL warnings

# Disable InsecureRequestWarning: CERTIFICATE_VERIFY_FAILED
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# User is using Brisbane URL which sometimes has local_date_time_full in YYYYMMDDHHMMSS format
BOM_URL = "https://reg.bom.gov.au/fwo/IDQ60901/IDQ60901.94575.json" # Brisbane
# Original Archerfield was: "https://reg.bom.gov.au/fwo/IDQ60801/IDQ60801.94569.json"
# Sydney (for DD/MM/YYYY HH:MM:SS testing): "https://reg.bom.gov.au/fwo/IDN60801/IDN60801.94576.json"

def format_bom_local_time(time_str):
    """
    Formats BOM's local_date_time_full string.
    Handles both "YYYYMMDDHHMMSS" and "DD/MM/YYYY HH:MM:SS" formats.
    Returns a dictionary {'date': 'DD/MM/YYYY', 'time': 'HH:MM:SS', 'original': time_str} 
    or {'date': 'N/A', 'time': 'N/A', 'original': time_str, 'malformed': True} on failure.
    """
    if not time_str or time_str == 'N/A':
        return {'date': 'N/A', 'time': 'N/A', 'original': time_str}

    try:
        # Attempt to parse YYYYMMDDHHMMSS format
        if len(time_str) == 14 and time_str.isdigit():
            year = time_str[0:4]
            month = time_str[4:6]
            day = time_str[6:8]
            hour = time_str[8:10]
            minute = time_str[10:12]
            second = time_str[12:14]
            return {
                'date': f"{day}/{month}/{year}",
                'time': f"{hour}:{minute}:{second}",
                'original': time_str
            }
        # Attempt to parse DD/MM/YYYY HH:MM:SS format
        elif '/' in time_str and ' ' in time_str and ':' in time_str:
            parts = time_str.split(' ', 1) # Split only on the first space
            if len(parts) == 2:
                date_part = parts[0]  # DD/MM/YYYY
                time_part = parts[1]  # HH:MM:SS
                
                # Validate date part (e.g., 3 components, all digits)
                date_elements = date_part.split('/')
                if len(date_elements) != 3 or not all(d.isdigit() for d in date_elements):
                    raise ValueError("Invalid date component in DD/MM/YYYY format")

                # Validate time part (e.g., 3 components, all digits)
                time_elements = time_part.split(':')
                if len(time_elements) != 3 or not all(t.isdigit() for t in time_elements):
                     raise ValueError("Invalid time component in HH:MM:SS format")

                return {
                    'date': date_part,
                    'time': time_part,
                    'original': time_str
                }
        # If neither format matches, mark as malformed
        raise ValueError("Unknown time string format")
    except Exception:
        # print(f"Debug: Could not parse time_str '{time_str}': {e}") # Optional debug
        return {'date': 'N/A', 'time': 'N/A', 'original': time_str, 'malformed': True}


def fetch_weather_data():
    """Fetches and processes weather data from BOM."""
    try:
        response = requests.get(BOM_URL, timeout=10, verify=False)
        response.raise_for_status()
        data = response.json()

        observations_data = data.get('observations', {}).get('data', [])
        
        if not observations_data:
            return None, "No observation data found in the JSON response."

        # Station name is usually consistent
        station_name = observations_data[0].get('name', 'Unknown Location')
        
        processed_observations = []
        for obs in observations_data[:5]: # Get the latest 5 observations
            raw_local_time = obs.get('local_date_time_full', 'N/A')
            formatted_time_obj = format_bom_local_time(raw_local_time)

            processed_observations.append({
                'local_time_obj': formatted_time_obj, # Pass the dictionary
                'aifstime_utc': obs.get('aifstime_utc', 'N/A'),
                'air_temp': obs.get('air_temp', 'N/A'),
                'apparent_temp': obs.get('apparent_t', 'N/A'),
                'humidity': obs.get('rel_hum', 'N/A'),
                'wind_dir': obs.get('wind_dir', 'N/A'),
                'wind_spd_kmh': obs.get('wind_spd_kmh', 'N/A'),
                'gust_kmh': obs.get('gust_kmh', 'N/A'),
                'pressure_hpa': obs.get('press_qnh', 'N/A'),
                'rain_since_9am': obs.get('rain_trace', 'N/A')
            })
        
        header_info_list = data.get('observations', {}).get('header', [])
        last_updated_product = 'N/A'
        if header_info_list and isinstance(header_info_list, list) and len(header_info_list) > 0:
            # BOM sometimes returns header as a list, sometimes not.
            # And sometimes product_issue_time_utc is missing.
             header_info = header_info_list[0] if isinstance(header_info_list, list) else header_info_list
             if isinstance(header_info, dict):
                last_updated_product = header_info.get('product_issue_time_utc', 'N/A')
                if last_updated_product == 'N/A': # Fallback for some stations like Brisbane
                    last_updated_product = header_info.get('refresh_message', 'N/A')


        return {
            'station_name': station_name,
            'last_updated_product': last_updated_product,
            'observations': processed_observations
        }, None

    except requests.exceptions.SSLError as e:
        return None, f"SSL Error: {e}. Could not verify the server's SSL certificate."
    except requests.exceptions.RequestException as e:
        return None, f"Error fetching data: {e}"
    except json.JSONDecodeError:
        return None, "Error decoding JSON data from BOM. The data might not be in the expected format."
    except KeyError as e:
        return None, f"Unexpected data structure from BOM: Missing key {e}"
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"

@app.route('/')
def home():
    weather_info, error_message = fetch_weather_data()
    if error_message:
        return render_template('index.html', error=error_message)
    return render_template('index.html', weather=weather_info)

@app.route('/api/weather')
def api_weather():
    weather_info, error_message = fetch_weather_data()
    if error_message:
        return jsonify({'error': error_message}), 500
    if not weather_info:
        return jsonify({'error': 'No weather data available'}), 404
    return jsonify(weather_info)

if __name__ == '__main__':
    app.run(debug=True)