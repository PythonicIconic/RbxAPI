from functools import reduce
from operator import add


def map_reduce_rap(data):
    return reduce(add, filter(lambda x: x, map(lambda k: k.get('recentAveragePrice', 0), data)))
