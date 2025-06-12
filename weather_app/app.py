from datetime import datetime
import json
import requests
from flask import Flask, render_template, jsonify
import urllib3

# Disable InsecureRequestWarning: CERTIFICATE_VERIFY_FAILED
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Endpoints for the Ecowitt devices
API_URLS = {
    "D8:BC:38:AA:EF:E1": "https://api.ecowitt.net/api/v3/device/real_time?application_key=2A514E07593482820CACAAB8FD0C73B2&api_key=17a5de25-fa25-4a18-9c86-78e93184c44c&mac=D8:BC:38:AA:EF:E1&call_back=all",
    "D8:BC:38:AA:96:AF": "https://api.ecowitt.net/api/v3/device/real_time?application_key=2A514E07593482820CACAAB8FD0C73B2&api_key=17a5de25-fa25-4a18-9c86-78e93184c44c&mac=%20D8:BC:38:AA:96:AF&call_back=all",
}


def fetch_weather_data():
    """Fetch the current temperature from each Ecowitt device."""
    observations = []
    try:
        for mac, url in API_URLS.items():
            resp = requests.get(url, timeout=10, verify=False)
            resp.raise_for_status()
            data = resp.json()
            temp_info = data.get("data", {}).get("outdoor", {}).get("temperature", {})
            epoch = int(temp_info.get("time", 0))
            temp_f = float(temp_info.get("value", 0))
            temp_c = round((temp_f - 32) * 5 / 9, 1)
            time_str = datetime.fromtimestamp(epoch).strftime("%H:%M:%S")
            observations.append({"mac": mac, "temp_c": temp_c, "time": time_str})
        return {"observations": observations}, None
    except requests.exceptions.SSLError as e:
        return None, f"SSL Error: {e}. Could not verify the server's SSL certificate."
    except requests.exceptions.RequestException as e:
        return None, f"Error fetching data: {e}"
    except (json.JSONDecodeError, ValueError) as e:
        return None, f"Error decoding data: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/weather')
def api_weather():
    weather_info, error_message = fetch_weather_data()
    if error_message:
        return jsonify({'error': error_message}), 500
    return jsonify(weather_info)


if __name__ == '__main__':
    app.run(debug=True)
