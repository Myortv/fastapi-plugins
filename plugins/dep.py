from .requests import Request
from fastapi import Depends 
from fastapi.security import OAuth2PasswordBearer

class Config:
    OAUTH_SCHEME = OAuth2PasswordBearer(tokenUrl="http://api.testing.rolefr.com/auth/sign-in/")
    OAUTH_URL = 'http://api.testing.rolefr.com/auth/identity'
    USERS_TAGS_URL = 'http://api.testing.rolefr.com/account/users-tags'

async def identify_request(token: str = Depends(Config.OAUTH_SCHEME)):
    """
        use thise dependency only if you need user's identity
    
        if you want to check users authorization,
        use fastapi's oauth2passwordbearer (or others)
    """    
    return await Request.get_identity(token, auth_url = Config.OAUTH_URL)


async def users_tags(token: str = Depends(Config.OAUTH_SCHEME)):
    return await Request.get_tags(token, tags_url = Config.USERS_TAGS_URL)
