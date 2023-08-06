import logging

from datetime import datetime

from typing import Callable

import jwt


class TokenManager:
    def __init__(
        self,
        privat_key: str,
        public_key: str,
        algorithm: str,
        custom_validator: Callable = None,
    ):
        self.privat_key = str(privat_key)
        self.public_key = str(public_key)
        self.algorithm = algorithm
        self.custom_validator = custom_validator

    def encode(self, data: dict) -> str:
        to_encode = data.copy()
        encoded_jwt = jwt.encode(
            to_encode,
            self.privat_key,
            algorithm=self.algorithm,
        )
        return encoded_jwt

    def decode(self, token: str) -> dict:
        try:
            decoded_token = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm]
            )
            return decoded_token
        except jwt.ExpiredSignatureError:
            return None
        except Exception as e:
            logging.exception(e)

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
            raise Exception("Token can not be decoded")
