class Environment:
    def __init__(self, sensor, source, plugins=None):
        self.sensor  = sensor
        self.source  = source
        self.plugins = plugins or []

    def _apply_plugins(self, sensor_data, action):
        for plugin in self.plugins:
            action = plugin.process(sensor_data, action)
        return action

    def step(self, agent, row_index=-1):
        sensor_data = self.sensor.read(self.source, row_index=row_index)
        action      = agent.run(sensor_data)
        action      = self._apply_plugins(sensor_data, action)
        return sensor_data, action

    def run_all(self, agent):
        all_rows = self.sensor.read_all(self.source)
        results  = []
        for sensor_data in all_rows:
            action = agent.run(sensor_data)
            action = self._apply_plugins(sensor_data, action)
            results.append((sensor_data, action))
        return results

    def add_plugin(self, plugin):
        self.plugins.append(plugin)
        return self
