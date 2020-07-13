from functools import reduce
from operator import add

codes = {
    0: 'Unauthorized to perform this request, is your cookie set correctly?',
    1: 'Invalid Group was given',
    2: 'Invalid Role was given',
    3: 'Invalid User was given',
    4: 'Unauthorized to manage given User',
    5: 'Invalid Asset was given',
    6: 'Unauthorized to set status of given Group',
    23: 'Unable to alter self'
}


def map_reduce_rap(data):
    return reduce(add, filter(lambda x: x, map(lambda k: k.get('recentAveragePrice', 0), data)))


def handle_code(code: int):
    """Function that handles error codes provided by the Roblox API."""
    raise UserWarning(codes[code])
