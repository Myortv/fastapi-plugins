from typing import Callable, Optional
import logging
import asyncio

import ujson

import aio_pika
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool
from aio_pika import Channel, ExchangeType, Message, Queue


from fastapiplugins.base import AbstractPlugin


async def autodelete_queue_builder(
    channel: Channel
) -> Queue:
    return await channel.declare_queue(auto_delete=True)


class RabbitManager(AbstractPlugin):
    class Config:
        CONNECTION_POOL: Pool
        CHANNEL_POOL: Pool
        SUBSCRIBERS: dict = dict()
        dumps: Callable = ujson.dumps
        loads: Callable = ujson.loads

    @staticmethod
    async def get_connection(
        host: str,
        port: int,
        user: str,
        password: str,
    ) -> AbstractRobustConnection:
        return await aio_pika.connect_robust(
            host=host,
            port=port,
            login=user,
            password=password
        )

    @classmethod
    async def get_channel(cls) -> Channel:
        async with cls.Config.CONNECTION_POOL.acquire() as connection:
            return await connection.channel()

    @classmethod
    async def start(
        cls,
        host: str,
        port: int,
        user: str,
        password: str,
        max_connections: int = 2,
        max_channels: int = 10,
    ) -> None:
        """ start connection and channel pools """
        loop = asyncio.get_event_loop()

        cls.Config.CONNECTION_POOL = Pool(
            cls.get_connection,
            host,
            port,
            user,
            password,
            max_size=max_connections,
            loop=loop,
        )
        logging.info(
            'Rabbit Manager created Connections '
            f'Pool on {cls.Config.CONNECTION_POOL}'
        )

        cls.Config.CHANNEL_POOL = Pool(
            cls.get_channel,
            max_size=max_channels,
            loop=loop,
        )
        logging.info(
            'Rabbit Manager created Channel Pool'
            f' on {cls.Config.CHANNEL_POOL}'
        )

    @classmethod
    async def start_consuming(
        cls,
        queue_builder: Optional[Callable] = autodelete_queue_builder,
    ) -> None:
        """
            Start consuming messages. Should be called
            on project startup after RabbitManager.start()
            in case RabbitManager needs consuming.

            Creates and binds queues for subscibed functions
            (see RabbitManager.subscribe()). This method should
            be called after functions-subscribers added to
            RabbitManager.Config.SUBSCRIBERS. You can achieve
            this with importing module with functions-subscribers
            before starting RabbitManager

            Use logging.getLogger().setLevel(logging.DEBUG)
            to enable output of subscribing process
        """
        async with cls.Config.CHANNEL_POOL.acquire() as channel:
            for exchange, message_key in cls.Config.SUBSCRIBERS.keys():
                queue = await queue_builder(channel)
                exchange_obj = await channel.declare_exchange(
                    exchange,
                    ExchangeType.DIRECT,
                )
                await queue.bind(exchange_obj, routing_key=message_key)

                async def callback(message: Message):
                    async with message.process():
                        info = message.info()
                        func = cls.Config.SUBSCRIBERS[
                            (info.get('exchange'), info.get('routing_key'))
                        ]
                        await func(
                            cls.Config.loads(message.body.decode())
                        )

                await queue.consume(callback)
                logging.debug(
                    "Fuction "
                    f"{cls.Config.SUBSCRIBERS[(exchange, message_key)]} "
                    "starts consuming"
                )

    @classmethod
    async def stop(cls,) -> None:
        """ stop channel and connection pools """
        if cls.Config.CHANNEL_POOL:
            if not cls.Config.CHANNEL_POOL.is_closed:
                await asyncio.ensure_future(cls.Config.CHANNEL_POOL.close())
        if cls.Config.CONNECTION_POOL:
            if not cls.Config.CONNECTION_POOL.is_closed:
                await asyncio.ensure_future(cls.Config.CONNECTION_POOL.close())

    @classmethod
    def acquire_channel(
        cls,
        exchange_name: str,
        exchange_type: ExchangeType,
    ):
        """
            Wrapper returing channel. Used for publishing.

            Wrapped function must accept 'channel' and 'exchange' arguments
            provided by decorator.
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                if kwargs.get('channel', None):
                    return await func(*args, **kwargs)
                else:
                    async with cls.Config.CHANNEL_POOL.acquire() as ch:
                        exchange = await ch.declare_exchange(
                            exchange_name,
                            exchange_type,
                        )
                        kwargs['channel'] = ch
                        kwargs['exchange'] = exchange
                        result = await func(
                            *args,
                            **kwargs,
                        )
                return result
            return wrapper
        return decorator

    @classmethod
    def subscribe(cls, exchange, message_key):
        def decorator(func):

            cls.Config.SUBSCRIBERS[(exchange, message_key)] = func
            logging.debug(
                f'Function "{func}" subscribed as {(exchange, message_key)}'
            )

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
