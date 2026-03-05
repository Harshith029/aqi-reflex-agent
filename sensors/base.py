class BaseSensor:
    def read(self, source, **kwargs):
        raise NotImplementedError

    def read_all(self, source, **kwargs):
        raise NotImplementedError
