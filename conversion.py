from typing import NamedTuple


class UserPresence(NamedTuple):
    """NamedTuple derived class that handles a user's presence."""
    presence_type: str
    last_location: str
    place_id: int
    root_place_id: int
    game_id: str
    universe_id: int
    userid: int
    last_online: str


class GameVotes(NamedTuple):
    """NamedTuple derived class that handles a game's votes."""
    upvotes: int
    downvotes: int
