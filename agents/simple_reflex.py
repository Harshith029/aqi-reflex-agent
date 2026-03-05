from agents.base import BaseAgent
from aqi_calculator import compute_aqi

RULES = [
    (lambda aqi: aqi <= 50,  "Air quality is satisfactory. Safe for all outdoor activities."),
    (lambda aqi: aqi <= 100, "Acceptable air quality. Sensitive individuals should limit prolonged exertion outdoors."),
    (lambda aqi: aqi <= 200, "Unhealthy for sensitive groups. Reduce prolonged or heavy outdoor activity."),
    (lambda aqi: aqi <= 300, "Health effects possible for everyone. Limit outdoor activities and wear a mask."),
    (lambda aqi: aqi <= 400, "Health alert. Avoid outdoor activities. Keep windows closed and use an air purifier."),
    (lambda aqi: aqi >  400, "Emergency conditions. Stay indoors with air purification. Avoid all outdoor exposure."),
]

class SimpleReflexAgent(BaseAgent):
    def perceive(self, sensor_data):
        return {k: v for k, v in sensor_data.items() if not k.startswith("_")}

    def act(self, percept):
        result = compute_aqi(percept)
        if result is None:
            return {
                "aqi":         None,
                "category":    "Unknown",
                "advisory":    "Insufficient sensor data to determine air quality.",
                "dominant":    None,
                "sub_indices": {},
            }
        aqi     = result["aqi"]
        advisory = next((msg for condition, msg in RULES if condition(aqi)), "")
        return {
            "aqi":         aqi,
            "category":    result["category"],
            "advisory":    advisory,
            "dominant":    result["dominant"],
            "sub_indices": result["sub_indices"],
        }
