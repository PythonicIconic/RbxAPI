from typing import NamedTuple


class UserPresence(NamedTuple):
    presence_type: str
    last_location: str
    place_id: int
    root_place_id: int
    game_id: str
    universe_id: int
    userid: int
    last_online: str
