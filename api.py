import requests
import random
import re

base = 'https://api.roblox.com'
auth = 'https://auth.roblox.com/v1/account/pin/unlock'
account = 'https://accountinformation.roblox.com/v1'
messages = 'https://privatemessages.roblox.com/v1'
user = 'https://users.roblox.com/v1'
games = 'https://games.roblox.com/v1'
groups = 'https://groups.roblox.com/v1'
friends = 'https://friends.roblox.com/v1'
presence = 'https://presence.roblox.com/v1/presence/users'
economy = 'https://economy.roblox.com/v1/assets'
inventory = 'https://inventory.roblox.com'


class BaseAuth:
    """Base Authentication class to derive from."""
    def __init__(self, cookie: str = None, **data):
        """
        Creates a session with which objects can interact to access authenticated endpoints.

        :param cookie: Optional: The cookie to create the session with.
        :key cookies: Optional: List of cookies to use with a proxy.
        :key proxies: Optional: List of proxies to use with a single cookie or several cookies.
        :key proxy_type: Optional: Type (http|https) of the given proxies. Required if using proxies, otherwise optional.
        """
        self.__session = requests.session()
        if data:
            self.__cookies, self.__proxies, self.__proxy_type = data['data'].get('cookies', None), data['data'].get('proxies', None), data['data'].get('proxy_type', None)
        else:
            self.__cookies, self.__proxies, self.__proxy_type = None, None, None
        if self.__cookies:
            if isinstance(self.__cookies, list):
                pass
            else:
                raise UserWarning('Cookies must be in a list')
        if self.__proxies:
            if isinstance(self.__proxies, list):
                pass
            else:
                raise UserWarning('Proxies must be in a list')
            if self.__proxy_type:
                if self.__proxy_type == 'http' or self.__proxy_type == 'https':
                    pass
                else:
                    raise UserWarning('Proxy type must be http or https')
            else:
                raise UserWarning('Proxy type must be provided if using proxies')
        self.__re = re.compile('https|http')
        if cookie:
            self.__session.cookies['.ROBLOSECURITY'] = cookie
            self.__session.headers['X-CSRF-TOKEN'] = self.__session.post('https://catalog.roblox.com/v1/catalog/items/details').headers['X-CSRF-TOKEN']
            self.__validate_cookie()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        del self

    def __validate_cookie(self):
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
        if self.__cookies:
            choice = random.choice(self.__cookies)
            self.__session.cookies['.ROBLOSECURITY'] = choice
            self.__session.headers['X-CSRF-TOKEN'] = self.__session.post('https://catalog.roblox.com/v1/catalog/items/details').headers['X-CSRF-TOKEN']
            self.__validate_cookie()
        if self.__proxies:
            self.__session.proxies.update({self.__proxy_type: random.choice(self.__proxies)})
        return self.__session

    @session.setter
    def session(self, cookie: str):
        """
        Sets the cookie for the current session.

        :param cookie: The cookie to set with this session.
        :return: requests.session
        """
        self.__session.cookies['.ROBLOSECURITY'] = cookie
        self.__session.headers['X-CSRF-TOKEN'] = self.__session.post('https://catalog.roblox.com/v1/catalog/items/details').headers['X-CSRF-TOKEN']
        self.__validate_cookie()
