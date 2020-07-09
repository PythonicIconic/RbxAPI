from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union, List
import requests

from RbxAPI import conversion
from RbxAPI import utils
from RbxAPI import api


class CookieInfo:
    """Class that handles information provided by the settings/json response."""
    def __init__(self, data):
        self.__dict__.update(data)

    def __repr__(self):
        return f'CookieInfo(UserId={self.UserId} Name={self.Name} IsEmailOnFile={self.IsEmailOnFile} ' \
               f'IsEmailVerified={self.IsEmailVerified})'


class User(api.BaseAuth):
    """Class that handles interactions with Roblox users."""
    def __init__(self, userid: int, cookie: str = None, **kwargs):
        """
        Creates an object that provides Roblox user information and endpoint interactions.

        :param userid: The id of the user to create an object of.
        :param cookie: Optional: The user's cookie to use for authentication. This will be required for certain,
        but not all interactions.
        :key cookies: Optional: List of cookies to use with a proxy.
        :key proxies: Optional: List of proxies to use with a single cookie or several cookies.
        """
        super().__init__(cookie, data=kwargs)
        if kwargs.get('proxies', ''):
            requests = self.session
        else:
            import requests
        data = {k.lower(): v for k, v in requests.get(f'{api.base}/users/{userid}').json().items()}
        data.update(requests.get(f'{api.user}/users/{userid}').json())
        if data.get('errors', ''):
            utils.handle_code(data['errors'][0]['code'])
        else:
            del data['name'], data['displayName']
            self.__dict__.update(data)
            self.__cookie_info = None
            self.__presence = None
            self.__friends = None
            self.__status = None
            self.__groups = None
            self.__rap = None

    def __repr__(self):
        return f'User(id={self.id} username={self.username} created={self.created} isonline={self.isonline} ' \
               f'isbanned={self.isBanned})'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self

    @property
    def cookie_info(self) -> CookieInfo:
        """
        Contains account information about the current cookie being used.

        :return: CookieInfo
        """
        if self.session:
            data = self.session.get(f'https://www.roblox.com/my/settings/json').json()
            self.__cookie_info = CookieInfo(data)
        else:
            raise UserWarning('Authentication required for this endpoint, session must be set')
        return self.__cookie_info

    @property
    def status(self) -> str:
        """
        Contains information about the current user's status.

        :return: str
        """
        if not self.__status:
            data = requests.get(f'{api.user}/users/{self.id}/status').json()
            self.__status = data['status']
        return self.__status

    @status.setter
    def status(self, status: str):
        """
        Sets the current user's status.

        :param status: New status to set.
        """
        if self.session:
            data = self.session.patch(f'{api.user}/users/{self.id}/status', data={'status': status}).json()
            if data.get('errors', ''):
                utils.handle_code(data['errors'][0]['code'])
            else:
                self.__status = data['status']
        else:
            raise UserWarning('Authentication required for this endpoint, session must be set')

    @property
    def friends(self) -> List['User']:
        """
        Contains a list of User objects representing the current user's friends.

        :return: List[User]
        """
        if not self.__friends:
            data = requests.get(f'{api.base}/users/{self.id}/friends').json()
            if not data:
                utils.handle_code(data['errors'][0]['code'])
            else:
                page = 2
                results = [*data]
                while data:
                    data = requests.get(f'{api.base}/users/{self.id}/friends?page={page}').json()
                    results += data
                    page += 1
                with ThreadPoolExecutor() as exe:
                    tasks = [exe.submit(User, friend['Id']) for friend in results]
                    self.__friends = [t.result() for t in as_completed(tasks)]
        return self.__friends

    @property
    def groups(self) -> List['Group']:
        """
        Contains a list of Group objects representing the groups the current user is in.

        :return: List[Group]
        """
        if not self.__groups:
            data = requests.get(f'{api.base}/users/{self.id}/groups').json()
            if type(data) == dict and data.get('errors', ''):
                utils.handle_code(data['errors'][0]['code'])
            elif not data:
                raise UserWarning('User not in any groups')
            else:
                with ThreadPoolExecutor() as exe:
                    tasks = [exe.submit(Group, d['Id']) for d in data]
                    self.__groups = [t.result() for t in as_completed(tasks)]
        return self.__groups

    @property
    def rap(self) -> int:
        """
        Contains the total RAP of the current user.

        :return: int
        """
        if not self.__rap:
            data = requests.get(f'{api.inventory}/{self.id}/assets/collectibles?sortOrder=Asc&limit=100').json()
            if data.get('errors', ''):
                utils.handle_code(data['errors'][0]['code'])
            else:
                results = [data['data']]
                while data['nextPageCursor']:
                    data = requests.get(f'{api.inventory}/{self.id}/assets/collectibles?sortOrder=Asc&limit=100&cursor={data["nextPageCursor"]}').json()
                    results.append(data['data'])
                self.__rap = utils.reduce(utils.add, [utils.map_reduce_rap(page) for page in results])
        return self.__rap

    @property
    def presence(self) -> conversion.UserPresence:
        """
        Contains a UserPresence object representing the current user's presence.

        :return: UserPresence
        """
        if not self.__presence:
            if self.session:
                data = self.session.post(api.presence, data={'userids': [self.id]}).json()
                if data.get('errors', ''):
                    utils.handle_code(data['errors'][0]['code'])
                else:
                    self.__presence = conversion.UserPresence._make(data['userPresences'][0].values())
            else:
                raise UserWarning('Authentication required for this endpoint, session must be set')
        return self.__presence

    def change_description(self, description: str, pin: str = None):
        """
        Sets a new description for the current user.

        :param description: New description to set.
        :param pin: Optional: Account PIN to unlock settings if applicable.
        """
        if self.session:
            if pin:
                self.session.post(api.auth, data={'pin': pin})
            data = self.session.post(f'{api.account}/description', data={'description': description}).json()
            if data.get('errors', ''):
                utils.handle_code(data['errors'][0]['code'])
            else:
                self.description = self.session.get(f'{api.account}/description').json()['description']
        else:
            raise UserWarning('Authentication required for this endpoint, session must be set')

    def message(self, subject: str, body: str, recipient: Union['User', int] = None):
        """
        Sends a message to the current user or the given recipient.

        :param subject: The subject to use for the message.
        :param body: The message itself to send.
        :param recipient: Optional: Recipient to send the message to in the form of a User object or the userid.
        """
        if self.session:
            if recipient:
                _id = recipient if isinstance(recipient, int) else recipient.id
            else:
                _id = self.id
            data = self.session.post(f'{api.messages}/messages/send', data={
                'userId': self.by_cookie(self.session.cookies['.ROBLOSECURITY']).id, 'subject': subject, 'body': body,
                'recipientId': _id}).json()
            if data.get('errors', ''):
                utils.handle_code(data['errors'][0]['code'])
            elif not data.get('success', ''):
                raise UserWarning('Error occurred sending message')
        else:
            raise UserWarning('Authentication required for this endpoint, session must be set')

    @classmethod
    def by_username(cls, username: str) -> 'User':
        """
        Class method that returns a User object based on the given username rather than id.

        :param username: The name of the user to create an object of.
        :return: User
        """
        data = requests.post(f'{api.user}/usernames/users', data={'usernames': [username], 'excludeBannedUsers': False}).json()
        if data.get('errors', ''):
            utils.handle_code(data['errors'][0]['code'])
        elif not data['data']:
            raise UserWarning('Invalid User was given')
        return cls(data['data'][0]['id'])

    @classmethod
    def by_cookie(cls, cookie: str, proxies: List[str] = None) -> 'User':
        """
        Class method that returns a User object based on the given cookie rather than username or id.

        :param cookie: The cookie of the user to create an object of.
        :param proxies: Optional: List of proxies to use with a single cookie or several cookies.
        :return: User
        """
        sess = requests.session()
        sess.cookies['.ROBLOSECURITY'] = cookie
        sess.headers['X-CSRF-TOKEN'] = sess.post('https://www.roblox.com/api/item.ashx?').headers['X-CSRF-TOKEN']
        data = sess.get('https://www.roblox.com/mobileapi/userinfo')
        try:
            data = data.json()
        except:
            raise UserWarning('Invalid cookie')
        else:
            if proxies:
                return cls(data['UserID'], cookie, proxies=proxies)
            else:
                return cls(data['UserID'], cookie)


class Shout:
    """Class that handles information provided by the group API response."""
    def __init__(self, data):
        self.__dict__.update(data)
        self.poster = User(self.poster['userId'])

    def __repr__(self):
        return f'Shout(poster={self.poster} created={self.created} update={self.updated})'


class Role:
    """Class that handles information provided by the group API response."""
    def __init__(self, data):
        self.__dict__.update({k.lower(): v for k, v in data.items()})
        self.__member_count = None

    def __repr__(self):
        return f'Role(id={self.id} name={self.name} rank={self.rank})'


class Group(api.BaseAuth):
    """Class that handles interactions with Roblox groups."""
    def __init__(self, groupid: int, cookie: str = None, **kwargs):
        """
        Creates an object that provides Roblox group information and endpoint interactions.

        :param groupid: The id of the group to create an object of.
        :param cookie: Optional: The user's cookie to use for authentication. This will be required for certain,
        but not all interactions.
        :key cookies: Optional: List of cookies to use with a proxy.
        :key proxies: Optional: List of proxies to use with a single cookie or several cookies.
        """
        super().__init__(cookie, data=kwargs)
        if kwargs.get('proxies', ''):
            requests = self.session
        else:
            import requests
        data = requests.get(f'{api.base}/groups/{groupid}').json()
        if data.get('errors', ''):
            utils.handle_code(data['errors'][0]['code'])
        else:
            self.__dict__.update({k.lower(): v for k, v in data.items()})
            self.owner = User(self.owner['Id'])
            self.__description = self.__dict__.pop('description')
            self.__membercount = None
            self.__enemies = None
            self.__allies = None
            self.__roles = None
            self.__shout = None

    def __repr__(self):
        return f'Group(id={self.id} name={self.name} owner={self.owner})'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self

    def update_user_role(self, user: Union[User, int], role: Union[Role, int]) -> str:
        """
        Updates the given user's group role to the given role.

        :param user: Either a User object or the userid of the user to alter.
        :param role: Either a Role object or the roleid of the role to assign.
        :return: 'Success'
        """
        _id = user.id if isinstance(user, User) else user
        _role_id = role.id if isinstance(role, Role) else role
        data = self.session.patch(f'{api.groups}/groups/{self.id}/users/{_id}', data={'roleId': _role_id}).json()
        if data.get('errors', ''):
            utils.handle_code(data['errors'][0]['code'])
        return 'Success'

    @property
    def roles(self) -> List[Role]:
        """
        Contains a list of Role objects representing the current group's roles.

        :return: List[Role]
        """
        if not self.__roles:
            data = requests.get(f'{api.groups}/groups/{self.id}/roles').json()['roles']
            self.__roles = sorted([Role(role) for role in data], key=lambda role: role.rank)
        return self.__roles

    @property
    def description(self) -> str:
        """
        Contains the description of the current group.

        :return: str
        """
        return self.__description

    @description.setter
    def description(self, description: str):
        """
        Sets the description of the current group.

        :param description: The description to set for the current group.
        """
        data = self.session.patch(f'{api.groups}/groups/{self.id}/description', data={'description': description}).json()
        if data.get('errors', ''):
            utils.handle_code(data['errors'][0]['code'])
        self.__description = data['newDescription']

    @property
    def membercount(self) -> int:
        """
        Contains the member count of the current group.

        :return: int
        """
        if not self.__membercount:
            data = {k.lower(): v for k, v in requests.get(f'{api.groups}/groups/{self.id}').json().items()}
            if data.get('shout', '') and not self.__shout:
                self.__shout = Shout(data['shout'])
            self.__membercount = data['membercount']
        return self.__membercount

    @property
    def shout(self) -> Shout:
        """
        Contains the shout data of the current group in the form of the Shout class.

        :return: Shout
        """
        if not self.__shout:
            data = {k.lower(): v for k, v in requests.get(f'{api.groups}/groups/{self.id}').json().items()}
            if data.get('shout', ''):
                self.__shout = Shout(data['shout'])
            elif not self.__membercount:
                self.__membercount = data['membercount']
        return self.__shout

    @shout.setter
    def shout(self, message: str):
        """
        Sets the shout of the current group.

        :param message: The message for the shout to set.
        """
        data = self.session.patch(f'{api.groups}/groups/{self.id}/status', data={'message': message}).json()
        if data.get('errors', ''):
            utils.handle_code(data['errors'][0]['code'])
        self.__shout = Shout(data)

    @property
    def allies(self) -> List['Group'] or str:
        """
        Contains a list of Group objects representing the current group's allies.

        :return: List[Group] or 'Group has no allies'
        """
        if type(self.__allies) is not list:
            ally_data = requests.get(f'{api.base}/groups/{self.id}/allies').json()['Groups']
            self.__allies = [Group(group['Id']) for group in ally_data]
        if self.__allies:
            return self.__allies
        else:
            return 'Group has no allies'

    @property
    def enemies(self) -> List['Group'] or str:
        """
        Contains a list of Group objects representing the current group's enemies.

        :return: List[Group] or 'Group has no enemies'
        """
        if type(self.__allies) is not list:
            enemy_data = requests.get(f'{api.base}/groups/{self.id}/enemies').json()['Groups']
            self.__enemies = [Group(group['Id']) for group in enemy_data]
        if self.__enemies:
            return self.__enemies
        else:
            return 'Group has no enemies'


class Server:
    """Class that handles information provided by the game servers API response."""
    def __init__(self, data):
        self.__dict__.update(data)

    def __repr__(self):
        return f'Server(id={self.id} maxPlayers={self.maxPlayers} playing={self.playing} fps={self.fps} ping={self.ping})'


class Game(api.BaseAuth):
    """Class that handles interactions with Roblox games."""
    def __init__(self, gameid: int, cookie: str, **kwargs):
        """
        Creates an object that provides Roblox game information and endpoint interactions.

        :param gameid: The id of the game to create an object of.
        :param cookie: Optional: The user's cookie to use for authentication. This will be required for certain,
        but not all interactions.
        :key cookies: Optional: List of cookies to use with a proxy.
        :key proxies: Optional: List of proxies to use with a single cookie or several cookies.
        """
        super().__init__(cookie, data=kwargs)
        if kwargs.get('proxies', ''):
            requests = self.session
        else:
            import requests
        resp = self.session.get(f'{api.games}/games/multiget-place-details?placeIds={gameid}').json()
        if isinstance(resp, dict) and resp.get('errors', ''):
            utils.handle_code(resp['errors'][0]['code'])
        elif not resp:
            raise UserWarning('Invalid Game was given')
        else:
            resp = requests.get(f'{api.games}/games?universeIds={resp[0]["universeId"]}').json()['data'][0]
            data = {k.lower(): v for k, v in resp.items()}
            self.__dict__.update(data)
            self.creator = User(self.creator.get('id')) if self.creator.get('type') == 'User' else Group(self.creator.get('id'))
            self.__favorites = None
            self.__servers = None
            self.__votes = None

    def __repr__(self):
        return f'Game(rootplaceid={self.rootplaceid} name={self.name} creator={self.creator})'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self

    @property
    def favorites(self) -> int:
        """
        Contains the current game's favorites count.

        :return: int
        """
        if not self.__favorites:
            data = requests.get(f'{api.games}/games/{self.id}/favorites/count').json()
            self.__favorites = data['favoritesCount']
        return self.__favorites

    @property
    def servers(self) -> List[Server]:
        """
        Contains a list of Server objects representing the current game's top 100 servers.

        :return: List[Server]
        """
        if not self.__servers:
            data = requests.get(f'{api.games}/games/{self.rootplaceid}/servers/Public?limit=100').json()
            self.__servers = [Server(server) for server in data['data']]
        return self.__servers

    @property
    def votes(self) -> conversion.GameVotes:
        """
        Contains the current game's upvotes and downvotes in the form of a GameVotes object.

        :return: GameVotes
        """
        if not self.__votes:
            data = requests.get(f'{api.games}/games/votes?universeIds={self.id}').json()['data'][0]
            self.__votes = conversion.GameVotes(data['upVotes'], data['downVotes'])
        return self.__votes
