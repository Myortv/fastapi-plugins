import logging
import pika

from plugins.base import AbstractPlugin


class RabbitManager(AbstractPlugin):
    class Config:
        CONNECTION: pika.connection.Connection
        CHANNEL: pika.channel.Channel
        SUBSCRIBERS: dict = dict()

    @staticmethod
    def get_connection(
        host: str,
        port: int,
        user: str,
        password: str,
        max_channels: int,
    ) -> pika.connection.Connection:
        credentials = pika.PlainCredentials(user, password)
        connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=credentials,
            channel_max=max_channels,
        )
        return pika.BlockingConnection(connection_params)

    @classmethod
    def get_channel(cls) -> pika.channel.Channel:
        return cls.Config.CONNECTION.channel()

    @classmethod
    def start(
        cls,
        host: str,
        port: int,
        user: str,
        password: str,
        max_connections: int = 2,
        max_channels: int = 10,
    ) -> None:
        """ Start connection and channel pools """
        cls.Config.CONNECTION = cls.get_connection(
            host,
            port,
            user,
            password,
            max_channels,
        )
        logging.info('Rabbit Manager created connection on {cls.Config.CONNECTION}')

        cls.Config.CHANNEL = cls.Config.CONNECTION.channel()
        logging.info('Rabbit Manager created channel on {cls.Config.CHANNEL}')

    @classmethod
    def start_consuming(cls) -> None:
        """
        Start consuming messages. Should be called on project startup after RabbitManager.start()
        in case RabbitManager needs consuming.

        Creates and binds queues for subscribed functions (see RabbitManager.subscribe()). This method should
        be called after functions-subscribers added to RabbitManager.Config.SUBSCRIBERS.
        """
        for exchange, message_key in cls.Config.SUBSCRIBERS.keys():
            queue_name = exchange + ':' + message_key
            cls.Config.CHANNEL.queue_declare(queue=queue_name)
            cls.Config.CHANNEL.exchange_declare(exchange=exchange, exchange_type='direct')
            cls.Config.CHANNEL.queue_bind(exchange=exchange, queue=queue_name, routing_key=message_key)

            def callback(ch, method, properties, body):
                func = cls.Config.SUBSCRIBERS[(exchange, message_key)]
                func(body.decode())

            cls.Config.CHANNEL.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            logging.debug(f'Function "{cls.Config.SUBSCRIBERS[(exchange, message_key)]}" starts consuming')

    @classmethod
    def stop(cls,) -> None:
        """ Stop channel and connection pools """
        if cls.Config.CHANNEL:
            cls.Config.CHANNEL.close()
        if cls.Config.CONNECTION:
            cls.Config.CONNECTION.close()

    @classmethod
    def acquire_channel(cls, exchange_name: str, exchange_type: str):
        """
        Wrapper returning channel. Used for publishing.

        Wrapped function must accept 'channel' and 'exchange' arguments provided by decorator.
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    if kwargs.get('channel', None):
                        return func(*args, **kwargs)
                    else:
                        exchange = cls.Config.CHANNEL.exchange_declare(
                            exchange=exchange_name,
                            exchange_type=exchange_type,
                        )
                        kwargs['channel'] = cls.Config.CHANNEL
                        # kwargs['exchange'] = exchange
                        result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    logging.exception(e)
            return wrapper
        return decorator

    @classmethod
    def subscribe(cls, exchange, message_key):
        def decorator(func):

            cls.Config.SUBSCRIBERS[(exchange, message_key)] = func
            logging.debug(
                f'\n\nFunction "{func}" subscribed as {(exchange, message_key)}'
            )

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
