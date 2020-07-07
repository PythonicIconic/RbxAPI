from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union
import requests

from RbxAPI import conversion
from RbxAPI import utils
from RbxAPI import api


class CookieInfo:
    def __init__(self, data):
        self.__dict__.update(data)

    def __repr__(self):
        return f'CookieInfo(UserId={self.UserId} Name={self.Name} IsEmailOnFile={self.IsEmailOnFile} ' \
               f'IsEmailVerified={self.IsEmailVerified})'


class User(api.BaseAuth):
    def __init__(self, userid: int, cookie: str = None):
        super().__init__(cookie)
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
    def cookie_info(self):
        if self.session:
            data = self.session.get(f'https://www.roblox.com/my/settings/json').json()
            self.__cookie_info = CookieInfo(data)
        else:
            raise UserWarning('Authentication required for this endpoint, session must be set')
        return self.__cookie_info

    @property
    def friends(self):
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
    def groups(self):
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
    def rap(self):
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
    def presence(self):
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

    @classmethod
    def by_username(cls, username: str):
        data = requests.post(f'{api.user}/usernames/users', data={'usernames': [username], 'excludeBannedUsers': False}).json()
        return cls(data['data'][0]['id'])

    @classmethod
    def by_cookie(cls, cookie: str):
        sess = requests.session()
        sess.cookies['.ROBLOSECURITY'] = cookie
        sess.headers['X-CSRF-TOKEN'] = sess.post('https://www.roblox.com/api/item.ashx?').headers['X-CSRF-TOKEN']
        data = sess.get('https://www.roblox.com/mobileapi/userinfo')
        try:
            data = data.json()
        except:
            raise UserWarning('Invalid cookie')
        else:
            return cls(data['UserID'], cookie)


class Shout:
    def __init__(self, data):
        self.__dict__.update(data)
        self.poster = User(self.poster['userId'])

    def __repr__(self):
        return f'Shout(poster={self.poster} created={self.created} update={self.updated})'


class Role:
    def __init__(self, data):
        self.__dict__.update({k.lower(): v for k, v in data.items()})
        self.__member_count = None

    def __repr__(self):
        return f'Role(id={self.id} name={self.name} rank={self.rank})'


class Group(api.BaseAuth):
    def __init__(self, groupid: int, cookie: str = None):
        super().__init__(cookie)
        data = requests.get(f'{api.base}/groups/{groupid}').json()
        if data.get('errors', ''):
            utils.handle_code(data['errors'][0]['code'])
        else:
            self.__dict__.update({k.lower(): v for k, v in data.items()})
            self.owner = User(self.owner['Id'])
            self.__description = self.__dict__.pop('description')
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

    def update_role(self, user: Union[User, int], role: Union[Role, int]):
        _id = user.id if isinstance(user, User) else user
        _role_id = role.id if isinstance(role, Role) else role
        data = self.session.patch(f'{api.groups}/groups/{self.id}/users/{_id}', data={'roleId': _role_id}).json()
        if data.get('errors', ''):
            utils.handle_code(data['errors'][0]['code'])
        return 'Success'

    @property
    def roles(self):
        if not self.__roles:
            data = requests.get(f'{api.groups}/groups/{self.id}/roles').json()['roles']
            self.__roles = sorted([Role(role) for role in data], key=lambda role: role.rank)
        return self.__roles

    @property
    def description(self):
        return self.__description

    @description.setter
    def description(self, description: str):
        data = self.session.patch(f'{api.groups}/groups/{self.id}/description', data={'description': description}).json()
        if data.get('errors', ''):
            utils.handle_code(data['errors'][0]['code'])
        self.__description = data['newDescription']

    @property
    def shout(self):
        if not self.__shout:
            data = requests.get(f'{api.groups}/groups/{self.id}').json()
            if data.get('shout', ''):
                self.__shout = Shout(data['shout'])
        return self.__shout

    @shout.setter
    def shout(self, message: str):
        data = self.session.patch(f'{api.groups}/groups/{self.id}/status', data={'message': message}).json()
        if data.get('errors', ''):
            utils.handle_code(data['errors'][0]['code'])
        self.__shout = Shout(data)

    @property
    def allies(self):
        if type(self.__allies) is not list:
            ally_data = requests.get(f'{api.base}/groups/{self.id}/allies').json()['Groups']
            self.__allies = [Group(group['Id']) for group in ally_data]
        if self.__allies:
            return self.__allies
        else:
            return 'Group has no allies'

    @property
    def enemies(self):
        if type(self.__allies) is not list:
            enemy_data = requests.get(f'{api.base}/groups/{self.id}/enemies').json()['Groups']
            self.__enemies = [Group(group['Id']) for group in enemy_data]
        if self.__enemies:
            return self.__enemies
        else:
            return 'Group has no enemies'


class Server:
    def __init__(self, data):
        self.__dict__.update(data)

    def __repr__(self):
        return f'Server(id={self.id} maxPlayers={self.maxPlayers} playing={self.playing} fps={self.fps} ping={self.ping})'


class Game(api.BaseAuth):
    def __init__(self, gameid: int, cookie: str):
        super().__init__(cookie)
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
    def favorites(self):
        if not self.__favorites:
            data = requests.get(f'{api.games}/games/{self.id}/favorites/count').json()
            self.__favorites = data['favoritesCount']
        return self.__favorites

    @property
    def servers(self):
        if not self.__servers:
            data = requests.get(f'{api.games}/games/{self.rootplaceid}/servers/Public?limit=100').json()
            self.__servers = [Server(server) for server in data['data']]
        return self.__servers

    @property
    def votes(self):
        if not self.__votes:
            data = requests.get(f'{api.games}/games/votes?universeIds={self.id}').json()['data'][0]
            self.__votes = conversion.GameVotes(data['upVotes'], data['downVotes'])
        return self.__votes
