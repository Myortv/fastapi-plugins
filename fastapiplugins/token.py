import logging

from datetime import datetime, timedelta

from typing import Callable

import jwt


from fastapiplugins.exceptions import ExceptionMessage, get_exception_id


ORIGIN = 'PLUGINSTOKENS'


class BadJwtException(Exception):
    pass


class TokenManager:
    def __init__(
        self,
        privat_key: str,
        public_key: str,
        algorithm: str,
        custom_validator: Callable = None,
    ):
        self.privat_key = privat_key
        self.public_key = public_key
        self.algorithm = algorithm
        self.custom_validator = custom_validator

    def encode(
        self,
        data: dict,
        expires_delta: timedelta = None,
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
            to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            self.privat_key,
            algorithm=self.algorithm,
        )
        return encoded_jwt

    def decode(self, token: str) -> dict:
        decoded_token = jwt.decode(
            token,
            self.public_key,
            algorithms=[self.algorithm],
        )
        return decoded_token

    def validate_exceptions(self, decoded_token: dict) -> bool:
        if expires_at := decoded_token.get('exp'):
            if datetime.now() >= datetime.fromtimestamp(expires_at):
                return Exception("Token expired")
        if self.custom_validator:
            if not self.custom_validator(decoded_token):
                return Exception("Token is not valid")

    def get_content(self, token: str):
        if decoded_token := self.decode(token):
            if exception := self.validate_exceptions(decoded_token):
                raise exception
            else:
                return decoded_token
        else:
            raise BadJwtException("Token can not be decoded")


exceptions = {
    jwt.exceptions.ExpiredSignatureError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'expiredsignatureerror'),
            status=401,
            title="jwt: expiredsignatureerror",
        ),
    jwt.exceptions.DecodeError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'decodeerror'),
            status=401,
            title="jwt: decodeerror",
        ),
}
