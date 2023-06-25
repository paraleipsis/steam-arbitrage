from functools import wraps
from asyncio.exceptions import CancelledError
from conf.settings import LOGS
from os import listdir
from os.path import isfile, join, abspath


def catch_exception(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception:
        return None


def graceful_shutdown(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            await func(self, *args, **kwargs)
        except (KeyboardInterrupt, CancelledError):
            await self.db.write()
            LOGS['stdout_info'].info('Shutdown ...')
        except Exception:
            await self.db.write()
            LOGS['stdout_info'].info('Shutdown ...')
            raise

    return wrapper


def deep_search(key, mapping):
    if isinstance(mapping, dict):
        if key in mapping:
            return mapping[key]
        for k, v in mapping.items():
            item = deep_search(key, mapping[k])
            if item is not None:
                return item
    elif isinstance(mapping, list):
        for element in mapping:
            item = deep_search(key, element)
            if item is not None:
                return item
    return None


def deep_delete(key, mapping):
    if isinstance(mapping, dict):
        if key in mapping:
            del mapping[key]
            return True
        for k, v in mapping.items():
            item = deep_delete(key, mapping[k])
            if item is not None:
                return item
    elif isinstance(mapping, list):
        for element in mapping:
            item = deep_delete(key, element)
            if item is not None:
                return item
    return None


def list_json_files(json_files_dir) -> dict:
    json_files = {f: abspath(join(json_files_dir, f)) for f in listdir(json_files_dir)
                  if isfile(join(json_files_dir, f)) and f.endswith(".json")}

    return json_files
