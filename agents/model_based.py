from agents.base import BaseAgent
from aqi_calculator import compute_aqi

class ModelBasedAgent(BaseAgent):
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.history     = []

    def perceive(self, sensor_data):
        return {k: v for k, v in sensor_data.items() if not k.startswith("_")}

    def _update_model(self, percept, result):
        self.history.append({"percept": percept, "result": result})
        if len(self.history) > self.window_size:
            self.history.pop(0)

    def _trend(self):
        if len(self.history) < 2:
            return "stable"
        values = [h["result"]["aqi"] for h in self.history if h["result"]["aqi"] is not None]
        if len(values) < 2:
            return "stable"
        delta = values[-1] - values[0]
        if delta > 30:
            return "worsening"
        if delta < -30:
            return "improving"
        return "stable"

    def act(self, percept):
        result = compute_aqi(percept)
        if result is None:
            return {
                "aqi": None, "category": "Unknown",
                "advisory": "Insufficient sensor data.",
                "dominant": None, "sub_indices": {}, "trend": "unknown",
            }
        self._update_model(percept, result)
        trend   = self._trend()
        history = [h["result"]["aqi"] for h in self.history]
        return {
            "aqi":         result["aqi"],
            "category":    result["category"],
            "advisory":    self._advisory(result["aqi"], trend),
            "dominant":    result["dominant"],
            "sub_indices": result["sub_indices"],
            "trend":       trend,
            "history":     history,
        }

    def _advisory(self, aqi, trend):
        suffix = ""
        if trend == "worsening":
            suffix = " Trend is worsening — consider precautionary action."
        elif trend == "improving":
            suffix = " Trend is improving."
        base_rules = [
            (lambda v: v <= 50,  "Air quality is satisfactory."),
            (lambda v: v <= 100, "Acceptable. Sensitive groups limit outdoor exertion."),
            (lambda v: v <= 200, "Unhealthy for sensitive groups."),
            (lambda v: v <= 300, "Health effects for all. Limit outdoor activity."),
            (lambda v: v <= 400, "Health alert. Avoid outdoors."),
            (lambda v: v >  400, "Emergency. Stay indoors."),
        ]
        base = next((msg for cond, msg in base_rules if cond(aqi)), "")
        return base + suffix
