from typing import List

import os

from abc import ABC, abstractclassmethod


class AbstractPlugin(ABC):
    @abstractclassmethod
    async def start(cls):
        """
            start all syns and async jobs and connectins needed
            set params in Config class
        """
        pass

    @abstractclassmethod
    async def stop(cls):
        """
            stop all jobs and connections, stop instances connections
            if needed
        """
        pass

    @classmethod
    def loads_secrets(
        cls,
        **kwargs
    ) -> List[str]:
        """
            try load variables from envirement, then use arguments, 
            then use defaults.
            use argument key as key for cls.Config and as title of env. variable

            PSQL_DATABASE=database
            Will search for env. variable 'PSQL_DATABASE', then use argument.
            if argument is None, use default (cls.Cofig.PSQL_DATABASE)
        """
        args = []
        for var in kwargs:
            if os.environ.get(var):
                args.append(os.environ.get(var))
            elif kwargs[var] == None:
                args.append(getattr(cls.Config, var))
            else:
                args.append(kwargs[var])
        return args
