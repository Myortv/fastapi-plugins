from setuptools import setup

setup(
    name='fastapiplugins',
    version='0.1.2',
    description='Simplified version of plugins from Rolefr for fastapi',
    url='https://github.com/Myortv/fastapi-plugins',
    author='myortv',
    authpr_email='myortv@proton.me',
    license='MIT',
    pakages=['fastapi-plugins'],
    install_requires=[
        'asyncpg>=0.26.0',
        'aiohttp>=3.8.0',
        'fastapi',
        'pydantic',
        'pyignite',
        'ujson'
    ],
    classifiers=[
        '???'
    ]
)
