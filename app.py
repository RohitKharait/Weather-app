from flask import Flask, render_template_string, request
import urllib.request
import json

app = Flask(__name__)

API_KEY = "3d7e46b5d72c21d44b735c9bbaa8c970"

MAHARASHTRA_CITIES = [
    "Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad",
    "Solapur", "Kolhapur", "Amravati", "Nanded", "Thane"
]

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Maharashtra Weather</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial; background: #1a1a2e; color: white; padding: 30px; }
        h1 { text-align: center; margin-bottom: 30px; font-size: 2em; color: #e94560; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
        .card {
            background: #16213e;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid #0f3460;
            transition: transform 0.2s;
        }
        .card:hover { transform: scale(1.03); }
        .city { font-size: 1.3em; font-weight: bold; color: #e94560; }
        .temp { font-size: 2.5em; margin: 10px 0; }
        .info { color: #aaa; font-size: 0.9em; margin: 4px 0; }
        .desc { color: #4fc3f7; margin-top: 8px; text-transform: capitalize; }
        .error { color: red; text-align: center; }
        .refresh { 
            display: block; margin: 20px auto; padding: 12px 30px;
            background: #e94560; color: white; border: none;
            border-radius: 8px; cursor: pointer; font-size: 1em;
        }
    </style>
</head>
<body>
    <h1>🌤️ Maharashtra Live Weather</h1>
    <form method="POST">
        <button class="refresh" type="submit">🔄 Refresh Weather</button>
    </form>

    {% if weather_data %}
    <div class="grid">
        {% for w in weather_data %}
        <div class="card">
            <div class="city">📍 {{ w.city }}</div>
            <div class="temp">{{ w.temp }}°C</div>
            <div class="desc">{{ w.description }}</div>
            <div class="info">💧 Humidity: {{ w.humidity }}%</div>
            <div class="info">🌬️ Wind: {{ w.wind }} m/s</div>
            <div class="info">🌡️ Feels like: {{ w.feels_like }}°C</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if error %}
    <p class="error">{{ error }}</p>
    {% endif %}
</body>
</html>
"""

def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
        return {
            "city": city,
            "temp": round(data["main"]["temp"]),
            "feels_like": round(data["main"]["feels_like"]),
            "humidity": data["main"]["humidity"],
            "wind": data["wind"]["speed"],
            "description": data["weather"][0]["description"]
        }
    except Exception as e:
        print(f"Error for {city}: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = []
    error = None
    if request.method == "POST":
        for city in MAHARASHTRA_CITIES:
            w = get_weather(city)
            if w:
                weather_data.append(w)
        if not weather_data:
            error = "Could not fetch weather data. Check your API key!"
    return render_template_string(HTML, weather_data=weather_data, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)