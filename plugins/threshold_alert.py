from plugins.base import BasePlugin

class ThresholdAlertPlugin(BasePlugin):
    name = "threshold_alert"

    def __init__(self, threshold=200):
        self.threshold = threshold
        self.alerts    = []

    def process(self, sensor_data, action):
        aqi  = action.get("aqi")
        meta = sensor_data.get("_meta", {})
        if aqi is not None and aqi > self.threshold:
            alert = {
                "city":     meta.get("City", "Unknown"),
                "date":     meta.get("Date", ""),
                "aqi":      aqi,
                "category": action.get("category"),
            }
            self.alerts.append(alert)
            action["alert"] = f"ALERT: AQI {aqi:.1f} exceeds threshold of {self.threshold}"
        return action
