**Weather Agent**

- **Purpose:** Flask-based agent that accepts GPS (`lat`, `lon`) via POST `/weather`, executes local weather script with automatic fallback to external APIs, and upserts a `WeatherObserved` entity to Orion Context Broker.

**Features:**
- Local script execution (primary) with automatic fallback
- Multiple weather provider support (OpenWeatherMap, Open-Meteo as fallback)
- Automatic fallback when one provider fails
- Configurable API chain for redundancy
- Traces which provider was used in the Orion entity (`data_provider`)

**Current Configuration:**
1. **Primary:** Local script (`/opt/scripts/weather-data.sh`) - generates simulated weather data
2. **Fallback 1:** OpenWeatherMap API
3. **Fallback 2:** Open-Meteo API (free, no key needed)

Deployment files:
- `k8s/base/weather-agent/configmap.yaml` - contains `weather_agent.py`, `weather_providers.py`, and `weather-data.sh` scripts
- `k8s/base/weather-agent/deployment.yaml` - Deployment using `python:3.11-slim` with local script priority
- `k8s/base/weather-agent/service.yaml` - ClusterIP service on port `8888`
- `k8s/base/weather-agent/virtualservice.yaml` - Istio VirtualService to route `/weather` through ingress

Quick deploy:
```bash
kubectl apply -f k8s/base/weather-agent/configmap.yaml
kubectl apply -f k8s/base/weather-agent/deployment.yaml
kubectl apply -f k8s/base/weather-agent/service.yaml
kubectl apply -f k8s/base/weather-agent/virtualservice.yaml
```

Customizing Weather Providers:

**Current Setup (Script-First with Fallback):**
```yaml
WEATHER_APIS_CONFIG: '[
  {"type": "script", "name": "LocalScript-Primary", "path": "/opt/scripts/weather-data.sh"},
  {"type": "openweathermap", "name": "OpenWeatherMap-Fallback", "key": "YOUR_KEY"},
  {"type": "openmeteo", "name": "OpenMeteo-Fallback"}
]'
```

To update the configuration:
```bash
kubectl set env deployment/weather-agent -n fiware-platform \
  WEATHER_APIS_CONFIG='[
    {"type": "script", "name": "MyScript", "path": "/opt/scripts/my-weather.sh"},
    {"type": "openweathermap", "name": "OWM", "key": "YOUR_OWM_KEY"},
    {"type": "openmeteo", "name": "OpenMeteo"}
  ]'
```

**Supported Providers:**
- `script` - Local script execution (no requirements, primary in current setup)
- `openweathermap` - OpenWeatherMap API (requires API key)
- `openmeteo` - Open-Meteo API (free, no key needed)
- `custom` - Custom HTTP endpoint (requires URL)

Testing locally (port-forward):
```bash
kubectl port-forward svc/weather-agent 8888:8888
curl -X POST http://localhost:8888/weather -H 'Content-Type: application/json' \
  -d '{"lat":48.8566, "lon":2.3522, "entity_id":"Weather:Paris"}'
```

Testing via ingress (replace HOST with your ingress host):
```bash
curl -X POST "http://HOST/weather" -H 'Content-Type: application/json' \
  -d '{"lat":48.8566, "lon":2.3522, "entity_id":"Weather:Paris"}'
```

Notes:
- The local script generates realistic simulated weather data and is always available (no external dependencies)
- The agent uses `ORION_URL` environment variable (default `http://orion:1026/v2/entities`)
- The `data_provider` field in Orion indicates which provider was used
- If all providers in the chain fail, returns error 502 with failure details
- The local script is mounted from ConfigMap and provides realistic temperature, humidity, wind, pressure, and cloud coverage
- Script output format must be valid JSON with keys: `temp`, `humidity`, `wind_speed`, `pressure`, `description`
