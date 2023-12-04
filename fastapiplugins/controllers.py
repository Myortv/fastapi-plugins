from typing import Callable, Any, Tuple, Optional, List

from pydantic import BaseModel

# from fastapi import HTTPException

import asyncpg
from asyncpg.pool import Pool

# from fastapiplugins.utils import raise_exception
from fastapiplugins.base import AbstractPlugin
from fastapiplugins.exceptions import (
    get_exception_id,
    ExceptionMessage,
)


import logging


ORIGIN = 'PLUGINSCONTROLLERS'


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
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                if kwargs.get('conn', None):
                    return await func(*args, **kwargs)
                async with cls.Config.POOL.acquire() as conn:
                    result = await func(*args, conn=conn, **kwargs)
                return result
            return wrapper
        return decorator


def insert_q(
    data: dict | BaseModel,
    datatable: str,
) -> Tuple[str, Any]:
    fields, values = unpack_data(data)
    query = (
        f'INSERT INTO \n'
        f'\t{datatable} \n'
        f'\t({", ".join(fields)}) \n'
        f'VALUES \n'
        f'\t({", ".join( [ f"${i+1}" for i in range(0, len(values)) ])}) \n'
        f'RETURNING *\n'
    )
    return query, *values


def delete_q(
    datatable: str,
    **data: dict[Any],
) -> Tuple[str, Any]:
    conditions, values = generate_placeholder(
        data,
    )
    query = (
        f'DELETE FROM\n'
        f'\t{datatable}\n'
        f'WHERE\n'
        f'\t({" AND ".join(conditions)})\n'
        f'RETURNING *\n'
    )
    return query, *values


def update_q(
    data: dict | BaseModel,
    datatable: str,
    **conditions: dict[Any],
) -> Tuple[str, Any]:
    placeholder, values = generate_placeholder(data)
    condition, condition_values = generate_placeholder(
        conditions,
        len(values),
    )
    query = (
        f'UPDATE\n'
        f'\t{datatable}\n'
        f'set\n\t{", ".join(placeholder)}\n'
        f'where\n\t{" AND ".join(condition)}\n'
        f'returning *\n')
    return query, *values, *condition_values


def select_q(
    datatable: str,
    ordering: List[str] = None,
    **data: dict[Any],
) -> Tuple[str, Any]:
    conditions, values = generate_placeholder(data)
    ordering_str = ""
    if ordering:
        ordering_str = f"ORDER BY\n\t{', '.join(ordering)}"
    query = (
        f'SELECT *\n'
        f'FROM\n'
        f'\t{datatable}\n'
        f'WHERE\n'
        f'\t{" AND ".join(conditions)}\n'
        f'{ordering_str}\n'
    )
    return query, *values


def select_q_detailed(
    datatable: str,
    model: dict | BaseModel,
    ordering: List[str] = None,
    **data: dict[Any],
) -> Tuple[str, Any]:
    conditions, values = generate_placeholder(data)
    fields = get_fields(model)
    ordering_str = ""
    if ordering:
        ordering_str = f"ORDER BY\n\t{', '.join(ordering)}"
    query = (
        f'SELECT\n'
        f'\t{", ".join(fields)}\n'
        f'FROM\n'
        f'\t{datatable}\n'
        f'WHERE\n'
        f'\t{" and ".join(conditions)}\n'
        f'{ordering_str}\n'
    )
    return query, *values


def unpack_data(data: dict | BaseModel) -> tuple[list]:
    if isinstance(data, BaseModel):
        data = data.model_dump()
    # if isinstance(data, dict):
    fields = list(data.keys())
    values = list(data.values())
        # return fields, values
        # fields = list(data.)
        # values = list(data.__dict__.values())
    assert len(fields) == len(values)
    return fields, values


def generate_placeholder(data: dict | BaseModel, i: int = 0) -> tuple[list]:
    """
        returns pairs like 'field_name = $1'
        and values
    """
    fields, values = unpack_data(data)
    pair = []
    for field in fields:
        i += 1
        pair.append(f'{field} = ${i}')
    return pair, values


def validate(func):
    async def wrapper(*args, **kwargs):
        await args[0].validate_()
        return await func(*args, **kwargs)
    return wrapper


def get_fields(model):
    return model.__fields__.keys()


class NoDataException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


exceptions = {
    NoDataException:
        ExceptionMessage(
            id=get_exception_id(f"{ORIGIN}_GENERIC", 'noqueryresult'),
            status=404,
            title='controllers: No result from sql query'
        ),
    asyncpg.exceptions.UniqueViolationError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'uniqueviolationerror'),
            status=422,
            title="postgres: UniqueViolationError",
        ),
    asyncpg.exceptions.ForeignKeyViolationError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'foreignkeyviolationerror'),
            status=422,
            title="postgres: ForeignKeyViolationError",
        ),
    asyncpg.exceptions.NotNullViolationError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'notnullviolationerror'),
            status=422,
            title="postgres: NotNullViolationError",
        ),
    asyncpg.exceptions.CheckViolationError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'checkviolationerror'),
            status=422,
            title="postgres: CheckViolationError",
        ),
    asyncpg.exceptions.RestrictViolationError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'restrictviolationerror'),
            status=422,
            title="postgres: RestrictViolationError",
        ),
    asyncpg.exceptions.ExclusionViolationError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'exclusionviolationerror'),
            status=422,
            title="postgres: ExclusionViolationError",
        ),
    asyncpg.exceptions.InvalidForeignKeyError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'invalidforeignkeyerror'),
            status=422,
            title="postgres: InvalidForeignKeyError",
        ),
    asyncpg.exceptions.NameTooLongError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'nametoolongerror'),
            status=422,
            title="postgres: NameTooLongError",
        ),
    asyncpg.exceptions.DuplicateColumnError:
        ExceptionMessage(
            id=get_exception_id(ORIGIN, 'duplicatecolumnerroror'),
            status=422,
            title="postgres: DuplicateColumnErroror",
        ),
}
