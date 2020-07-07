# RbxAPI
RbxAPI is a Pythonic and efficient Roblox API wrapper. With many quality of life adjustments made during its first iterations, it aims to give you the simplest way of accessing Roblox's API endpoints!

## Getting Started
All you need to do to start using this wrapper is to pip install it and the requests library!

`pip install requests rbxapi`

After that you're good to go!

## Usage
The majority of this library revolves around the `User` and `Group` types. With these, you can get information about each and perform POST requests on authentication-required endpoints.

Getting user's RAP
```py
import RbxAPI

with RbxAPI.User(156) as user:
    print(user.rap)
```

You can also get a user by username
```py
import RbxAPI

user = RbxAPI.User.by_username('builderman')
```

For authentication related endpoints it's just as easy!
```py
import RbxAPI

cookie = open('cookie.txt').readline()
# Providing a valid cookie for the given user will create an authenticated session
with RbxAPI.User(1234567, cookie) as user:
    print(user.presence)
```
## Notes
Both the `User` and `Group` objects have attributes assigned from the API responses and are generally set to lowercase.

For example, a `User`'s attributes are assigned based on the `https://api.roblox.com/users/{userid}` json response and you can access each normally.
```py
import RbxAPI

with RbxAPI.User(156) as user:
    print(user.id, user.username, user.avataruri, user.avatarfinal, user.isonline)
```
