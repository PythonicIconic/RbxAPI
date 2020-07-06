from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union
import requests

from RbxAPI import conversion
from RbxAPI import utils
from RbxAPI import api


class User(api.BaseAuth):
    def __init__(self, userid: int, cookie: str = None):
        super().__init__(cookie)
        data = {k.lower(): v for k, v in requests.get(f'{api.base}/users/{userid}').json().items()}
        data.update(requests.get(f'{api.user}/users/{userid}').json())
        if data.get('errors', ''):
            raise UserWarning('Invalid UserID or Roblox API down')
        else:
            del data['name'], data['displayName']
            self.__dict__.update(data)
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
    def friends(self):
        if not self.__friends:
            data = requests.get(f'{api.base}/users/{self.id}/friends').json()
            if not data:
                raise UserWarning('Invalid UserID, unauthorized to view friends or Roblox API down')
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
                raise UserWarning('Invalid UserID or Roblox API down')
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
                raise UserWarning('Invalid UserID or not authorized to view inventory')
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
                    raise UserWarning('Authentication required for this endpoint, session must be set')
                else:
                    self.__presence = conversion.UserPresence._make(data['userPresences'][0].values())
            else:
                raise UserWarning('Authentication required for this endpoint, session must be set')
        return self.__presence

    @classmethod
    def by_username(cls, username: str):
        data = requests.post(f'{api.user}/usernames/users', data={'usernames': [username], 'excludeBannedUsers': False}).json()
        return cls(data['data'][0]['id'])


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
            raise UserWarning('Invalid GroupID or Roblox API down')
        else:
            self.__dict__.update({k.lower(): v for k, v in data.items()})
            self.owner = User(self.owner['Id'])
            self.__enemies = None
            self.__allies = None
            self.__roles = None

    def __repr__(self):
        return f'Group(id={self.id} name={self.name} owner={self.owner})'

    def update_role(self, user: Union[User, int], role_id: int):
        _id = user.id if isinstance(user, User) else user
        data = self.session.patch(f'{api.groups}/groups/{self.id}/users/{_id}', data={'roleId': role_id})
        if data.get('errors', ''):
            raise UserWarning('User not in Group, role does not exist or Roblox API down')
        else:
            return

    @property
    def roles(self):
        if not self.__roles:
            data = requests.get(f'{api.groups}/groups/{self.id}/roles').json()['roles']
            self.__roles = sorted([Role(role) for role in data], key=lambda role: role.rank)
        return self.__roles

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
