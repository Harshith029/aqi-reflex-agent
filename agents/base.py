class BaseAgent:
    def perceive(self, sensor_data):
        raise NotImplementedError

    def act(self, percept):
        raise NotImplementedError

    def run(self, sensor_data):
        return self.act(self.perceive(sensor_data))
