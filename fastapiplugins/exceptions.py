from typing import Optional
from functools import partial

from pydantic import BaseModel

from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException

import logging


global touched_ids
touched_ids = list()


class ExceptionMessage(BaseModel):
    id: str  # unique exception id to connect with frotend
    status: int  # http status
    title: Optional[str] = None  # exception title
    short: Optional[str] = None  # short exception overview
    detailed: Optional[str] = None  # detailed exception overwiew


class HandlableException(Exception):
    """
        Handlable exception to be catched and send
        proper response to user

        THIS EXCEPTION PRIVENTS FROM DOUBLE LOGGING,
        SO IF YOU NEED TO LOG YOUR EXCEPTION,
        DO IT IN YOUR CODE WHERE YOU CALL THIS EXCEPTION
    """

    def __init__(
        self,
        unique_exception_id: str,
        http_status: int,
        *args,
        title: Optional[str] = None,
        short: Optional[str] = None,  # short exception overview
        detailed: Optional[str] = None,  # detailed exception overwiew
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if not title:
            title = map_status_to_name.get(http_status, 'NOTITLE')
        self.handable_message = ExceptionMessage(
            id=unique_exception_id,
            status=http_status,
            title=title,
            short=short,
            detailed=detailed,
        )
        self.status = http_status
        self.message = detailed if detailed else short if short else title


map_status_to_name = {
    404: "Item not exsist",
    403: "Item not accecable",
    422: "Bad Request",
    500: "Server error",
}


def get_exception_id(
    origin: str,
    exception_id: str,
) -> str:
    """
        how exception id is created:
        'ORIGINWITHCAPSNOSPACES-uniqueidlowercasewithnospaces'
        it's consists of 2 parts -- origin and id
        origin is from where exception is raised
        and id -- unque id
        for example:
            PLUGINSCONTROLLERS-unique
            PLCO_1-unique
            X1-100
            A-46451
            1-1
    """
    return f"{origin}-{exception_id}"


def translate_http_exception(
    request: Request,
    raised_exception: HTTPException,
) -> JSONResponse:
    return JSONResponse(
        ExceptionMessage(
            id=f'UNIFIED_HTTP_EXCEPTION-{raised_exception.status_code}',
            status=raised_exception.status_code,
            title=raised_exception.detail
            if raised_exception.detail
            else map_status_to_name.get(raised_exception.status_code, 'NOTITLE'),
            detailed="This is unifed HTTPException."
        ).dict(),
        status_code=raised_exception.status_code

    )


def handle_wrapped_exception(
    request: Request,
    raised_exception: HandlableException,
) -> JSONResponse:
    return JSONResponse(
        raised_exception.handable_message.dict(),
        raised_exception.status,
    )


def prepare_exceptions(*args) -> dict:
    handlable_exceptions = {
        HandlableException: handle_wrapped_exception,
        HTTPException: translate_http_exception,
    }
    for exception_dict in args:
        check_for_unique_id(exception_dict)
        handlable_exceptions.update(
            prepare_data(exception_dict)
        )
    return handlable_exceptions


def check_for_unique_id(
    exception_dict: dict[Exception, ExceptionMessage],
) -> None:
    for exception_message in exception_dict.values():
        global touched_ids
        if exception_message.id in touched_ids:
            raise ValueError("This exception id is already exsists!")
        touched_ids.append(exception_message.id)


def prepare_data(
    exception_dict: dict[Exception, ExceptionMessage],
) -> dict:
    return {
        key: partial(wrap_exception, key, message)
        for key, message
        in exception_dict.items()
    }


def wrap_exception(
    exception: Exception,  # exception type
    message: ExceptionMessage,
    request: Request,
    raised_exception: Exception,  # actual raised exception
) -> JSONResponse:
    logging.exception(raised_exception)
    return JSONResponse(
        message.dict(),
        message.status,
    )
