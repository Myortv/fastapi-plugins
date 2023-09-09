from pydantic import ValidationError

from fastapi import HTTPException

import asyncpg
from asyncpg.pool import Pool

from plugins.utils import raise_exception
from plugins.base import AbstractPlugin

import logging


class DatabaseManager(AbstractPlugin):
    class Config:
        POOL: Pool = None
        PSQL_DATABASE: str = None
        PSQL_USER: str = None
        PSQL_PASSWORD: str = None
        PSQL_HOST: str = None

    @classmethod
    async def start(
        cls,
        database: str,
        user: str,
        password: str,
        host: str,
    ) -> None:
        cls.Config.POOL = await asyncpg.create_pool(
            database=database,
            user=user,
            password=password,
            host=host
        )
        logging.info(
            f'DatabaseManager create postgres pool on:{cls.Config.POOL}',
        )

    @classmethod
    def acqure_connection(cls):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                try:
                    if kwargs.get('conn', None):
                        return await func(*args, **kwargs)
                    else:
                        async with cls.Config.POOL.acquire() as conn:
                            result = await func(*args, conn=conn, **kwargs)
                    return result
                except ValidationError as e:
                    logging.exception(e)
                    raise_exception(e)
                except HTTPException as e:
                    logging.exception(e)
                    raise_exception(e)
                except Exception as e:
                    logging.exception(e)
            return wrapper
        return decorator


def insert_q(data, datatable):
    fields, values = unpack_data(data)
    query = (
        f'INSERT INTO '
        f'    {datatable} '
        f'    ({", ".join(fields)}) '
        f'VALUES '
        f'    ({", ".join( [ f"${i+1}" for i in range(0, len(values)) ])}) '
        f'RETURNING *'
    )
    return query, *values


def delete_q(datatable, **data):
    conditions, values = generate_placeholder(data)
    query = (
        f'DELETE FROM '
        f'    {datatable} '
        f'WHERE '
        f'    ({" AND ".join(conditions)}) '
        f'RETURNING * '
    )
    return query, *values


def update_q(data, datatable, **conditions):
    placeholder, values = generate_placeholder(data)
    condition, cond_values = generate_placeholder(conditions, len(values))
    query = (
        f'UPDATE '
        f'{datatable} '
        f'set {", ".join(placeholder)} '
        f'where {" AND ".join(condition)} '
        f'returning *')
    return query, *values, *cond_values


def select_q(datatable, **data):
    conditions, values = generate_placeholder(data)
    query = (
        f'SELECT * '
        f'FROM '
        f'    {datatable} '
        f'WHERE '
        f'    {" and ".join(conditions)} '
    )
    return query, *values


def select_q_detailed(datatable, model, **data):
    conditions, values = generate_placeholder(data)
    fields = get_fields(model)
    query = (
        f'SELECT '
            f'{", ".join(fields)} '
        f'FROM '
        f'    {datatable} '
        f'WHERE '
        f'    {" and ".join(conditions)} '
    )
    return query, *values


def unpack_data(data):
    if isinstance(data, dict):
        fields = list(data.keys())
        values = list(data.values())
        return fields, values
    fields = list(data.__dict__.keys())
    values = list(data.__dict__.values())
    assert len(fields) == len(values)
    return fields, values


def generate_placeholder(data, i=0):
    fields, values = unpack_data(data)
    pair = []
    for field in fields:
        i += 1
        pair.append(f'{field} = ${i}')
    return pair, values


def validate(func):
    async def wrapper(*args, **kwargs):
        try:
            await args[0].validate_()
        except AttributeError:
            raise Exception(
                f'{func}:{args[0]} has no validate_ function to call',
            )
        except Exception as e:
            raise HTTPException(
                422,
                f'Error during validation:\n {e.__str__()}',
            )
        return await func(*args, **kwargs)
    return wrapper


def get_fields(model):
    return model.__fields__.keys()
