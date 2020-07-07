import requests

base = 'https://api.roblox.com'
user = 'https://users.roblox.com/v1'
games = 'https://games.roblox.com/v1'
groups = 'https://groups.roblox.com/v1'
presence = 'https://presence.roblox.com/v1/presence/users'
inventory = 'https://inventory.roblox.com/v1/users'


class BaseAuth:
    """Base Authentication class to derive from."""
    def __init__(self, cookie: str = None):
        """
        Creates a session with which objects can interact to access authenticated endpoints.

        :param cookie: The cookie to create the session with.
        """
        self.__session = requests.session()
        if cookie:
            self.__session.cookies['.ROBLOSECURITY'] = cookie
            self.__session.headers['X-CSRF-TOKEN'] = self.__session.post('https://www.roblox.com/api/item.ashx?').headers['X-CSRF-TOKEN']
            data = self.__session.get('https://www.roblox.com/mobileapi/userinfo')
            try:
                data.json()
            except:
                raise UserWarning('Invalid cookie')

    @property
    def session(self) -> requests.session:
        """
        Session for handling authentication with API endpoints.

        :return: requests.session
        """
        return self.__session

    @session.setter
    def session(self, cookie: str):
        """
        Sets the cookie for the current session.

        :param cookie: The cookie to set with this session.
        :return: requests.session
        """
        self.__session.cookies['.ROBLOSECURITY'] = cookie
        self.__session.headers['X-CSRF-TOKEN'] = self.__session.post('https://www.roblox.com/api/item.ashx?').headers['X-CSRF-TOKEN']
        data = self.__session.get('https://www.roblox.com/mobileapi/userinfo')
        try:
            data.json()
        except:
            raise UserWarning('Invalid cookie')

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        del self
