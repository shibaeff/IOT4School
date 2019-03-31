import numpy as np


def rate_rng(rng, value):
    scores = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    for i in range(len(scores)):
        if value < np.percentile(rng, (i * 100) / len(scores)):
            return i
    return 0


class Scorer():
    def __init__(self):
        self._rng = []

    def score(self, parameter):
        return rate_rng(self._rng, parameter)


class TempScorer(Scorer):
    def __init__(self):
        super().__init__()
        self._rng = np.linspace(20, 24)


class HumidityScorer(Scorer):
    def __init__(self):
        super().__init__()
        self._rng = np.linspace(25, 30, 50)


class LightScorer(Scorer):
    def __init__(self):
        super().__init__()
        self._rng = np.linspace(250, 750, 50)


class Co2Scorer(Scorer):
    def __init__(self):
        super().__init__()
        self._rng = np.linspace(300, 750, 50)


