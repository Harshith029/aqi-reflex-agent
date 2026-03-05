class BasePlugin:
    name = "base"

    def process(self, sensor_data, action):
        raise NotImplementedError
