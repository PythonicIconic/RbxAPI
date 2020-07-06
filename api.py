import requests

base = 'https://api.roblox.com'
user = 'https://users.roblox.com/v1'
groups = 'https://groups.roblox.com/v1'
presence = 'https://presence.roblox.com/v1/presence/users'
inventory = 'https://inventory.roblox.com/v1/users'


class BaseAuth:
    def __init__(self, cookie: str = None):
        self.__session = requests.session()
        if cookie:
            self.__session.cookies['.ROBLOSECURITY'] = cookie
            self.__session.headers['X-CSRF-TOKEN'] = self.__session.post('https://www.roblox.com/api/item.ashx?').headers['X-CSRF-TOKEN']

    @property
    def session(self):
        return self.__session

    @session.setter
    def session(self, cookie: str):
        self.__session.cookies['.ROBLOSECURITY'] = cookie
        self.__session.headers['X-CSRF-TOKEN'] = self.__session.post('https://www.roblox.com/api/item.ashx?').headers['X-CSRF-TOKEN']

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        del self
