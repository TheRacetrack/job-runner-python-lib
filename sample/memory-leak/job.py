class Job:
    def __init__(self):
        self.cache = {}

    def perform(self):
        """Allocate more needless memory"""
        self.cache[len(self.cache)] = [1] * 1_000_000
        return len(self.cache)
