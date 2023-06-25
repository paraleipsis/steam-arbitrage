import asyncio
import json
import aiofiles

from json.decoder import JSONDecodeError
from io import UnsupportedOperation
from os.path import basename
from database.utils import catch_exception, deep_search, deep_delete
from pydantic.utils import deep_update


class Connection:
    def __init__(self):
        self.connection = None
        self.read_only = None
        self.location = None
        self.data = None

    @classmethod
    async def connect(cls, location: str, read_only: bool = False):
        self = cls()
        self.location = location
        self.read_only = read_only
        self.connection = await self.open_db()
        self.data = await self.read()
        return self

    async def open_db(self):
        if self.read_only:
            fp = await aiofiles.open(self.location, mode='r', encoding='utf8')
        else:
            fp = await aiofiles.open(self.location, mode='r+', encoding='utf8')

        return fp

    async def disconnect(self):
        if self.connection is not None:
            await self.connection.close()
            self.connection = None

    async def read(self):
        file = await self.connection.read()

        try:
            data = json.loads(file)
        except JSONDecodeError:
            raise

        return data

    async def write(self):
        if self.read_only:
            raise UnsupportedOperation(f"{basename(self.location)} is not writable")

        await self.connection.seek(0)
        await self.connection.write(json.dumps(self.data))
        await self.connection.truncate()

        return True

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.disconnect())
            else:
                loop.run_until_complete(self.disconnect())
        except Exception:
            pass


class Database(Connection):
    def __init__(self):
        super().__init__()

    async def get(self, key: str, default=None):
        try:
            return self.data[key]
        except KeyError:
            return default

    async def get_many(self, keys: list) -> list:
        return [catch_exception(lambda: self.data[key]) for key in keys]

    async def get_all(self) -> dict:
        return self.data

    async def delete(self, key) -> bool:
        del self.data[key]
        await self.write()
        return True

    async def save(self, data) -> bool:
        self.data = deep_update(self.data, data)
        await self.write()
        return True

    async def is_cached(self, key: str, keys_to_check: tuple = None, return_value: bool = False):
        if keys_to_check is not None:
            for k in keys_to_check:
                search = deep_search(k, self.data)
                if search:
                    if key in search:
                        if return_value:
                            return {'key_to_check': k, 'value': {'search_key': key, 'search_key_value': search[key]}}
                        return True
                    continue
                else:
                    continue
            return False
        else:
            search = deep_search(key, self.data)
            if search:
                if return_value:
                    return search
                return True
            return False

    async def displace_object(self, object_id: str, model) -> bool:
        deep_delete(object_id, self.data)
        self.data = deep_update(self.data, model.dict())
        return True

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.disconnect())
            else:
                loop.run_until_complete(self.disconnect())
        except Exception:
            pass

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.location}")'
