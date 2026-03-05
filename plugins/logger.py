import os
import csv
from datetime import datetime
from plugins.base import BasePlugin

class LoggerPlugin(BasePlugin):
    name = "logger"

    def __init__(self, log_file="output/aqi_log.csv"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self._write_header()

    def _write_header(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "city", "date", "aqi", "category", "dominant"])

    def process(self, sensor_data, action):
        meta = sensor_data.get("_meta", {})
        with open(self.log_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                meta.get("City", ""),
                meta.get("Date", ""),
                action.get("aqi"),
                action.get("category"),
                action.get("dominant"),
            ])
        return action
