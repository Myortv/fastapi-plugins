from setuptools import setup

setup(
    name='fastapiplugins',
    version='0.3.1',
    description='Fork from Rolefr plugins. Provide some useful plugins for fastapi (database, queues, jwt tokens, etc)',
    url='https://github.com/Myortv/fastapi-plugins',
    author='myortv',
    author_email='myortv@proton.me',
    license='MIT',
    pakages=['fastapiplugins'],
    install_requires=[
        'fastapi',
        'pydantic',
        'ujson',
        'PyJWT',
    ],
    extras_require={
        'async': ['aio-pika', 'aiohttp', 'asyncpg'],
        'sync': ['pika', 'requests', 'psycopg2-binary'],
    },
    classifiers=[
        '???'
    ]
)
