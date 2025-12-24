import itertools


class Stream:
    def __init__(self, iterable):
        self.iterable = iterable

    def map(self, func):
        return Stream(map(func, self.iterable))

    def filter(self, predicate):
        return Stream(filter(predicate, self.iterable))

    def flatMap(self, func):
        return Stream(itertools.chain.from_iterable(map(func, self.iterable)))

    def to_list(self):
        return list(self.iterable)
