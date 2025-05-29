import json
import requests
from flask import Flask, render_template, jsonify
import urllib3 # Import urllib3 to disable SSL warnings

# Disable InsecureRequestWarning: CERTIFICATE_VERIFY_FAILED
# This is often needed when verify=False is used with requests.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Using Sydney Observatory Hill as an example, as it's generally reliable.
# The original URL you were trying (IDN60801.94576.json) seems correct.
BOM_URL = "https://reg.bom.gov.au/fwo/IDN60801/IDN60801.94576.json"
# If you specifically need Archerfield: "https://reg.bom.gov.au/fwo/IDQ60801/IDQ60801.94569.json"
# Ensure the station ID is correct and the JSON is available.

def fetch_weather_data():
    """Fetches and processes weather data from BOM."""
    try:
        # MODIFICATION: Added verify=False to bypass SSL certificate verification.
        # This is a workaround for SSL errors like 'CERTIFICATE_VERIFY_FAILED'.
        # Use with caution and understand the security implications.
        response = requests.get(BOM_URL, timeout=10, verify=False)
        
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        data = response.json()

        observations_data = data.get('observations', {}).get('data', [])
        
        if not observations_data:
            return None, "No observation data found in the JSON response."

        station_name = observations_data[0].get('name', 'Unknown Location')
        
        processed_observations = []
        # Get up to the latest 5 observations
        for obs in observations_data[:5]: 
            processed_observations.append({
                'local_time': obs.get('local_date_time_full', 'N/A'),
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
        
        header_info = data.get('observations', {}).get('header', [{}])[0]
        last_updated_product = header_info.get('product_issue_time_utc', 'N/A')
        
        return {
            'station_name': station_name,
            'last_updated_product': last_updated_product,
            'observations': processed_observations
        }, None

    except requests.exceptions.SSLError as e:
        print(f"SSL Error encountered: {e}")
        return None, f"SSL Error: {e}. Could not verify the server's SSL certificate. If this persists, your system's CA certificates might be outdated or there might be network interference."
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None, f"Error fetching data: {e}"
    except json.JSONDecodeError:
        print("Error decoding JSON data.")
        return None, "Error decoding JSON data from BOM. The data might not be in the expected format."
    except KeyError as e:
        print(f"Unexpected data structure: Missing key {e}")
        return None, f"Unexpected data structure from BOM: Missing key {e}"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, f"An unexpected error occurred: {e}"

@app.route('/')
def home():
    """Serves the main HTML page with weather data."""
    weather_info, error_message = fetch_weather_data()
    if error_message:
        return render_template('index.html', error=error_message)
    return render_template('index.html', weather=weather_info)

@app.route('/api/weather')
def api_weather():
    """Provides the weather data as JSON."""
    weather_info, error_message = fetch_weather_data()
    if error_message:
        return jsonify({'error': error_message}), 500
    if not weather_info:
        return jsonify({'error': 'No weather data available'}), 404
    return jsonify(weather_info)

if __name__ == '__main__':
    app.run(debug=True)