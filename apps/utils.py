from functools import wraps
from models import AppDetails


def silence_event_loop_closed(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except RuntimeError as e:
            if str(e) != 'Event loop is closed':
                raise

    return wrapper


class Checker:
    @staticmethod
    async def check_response(response: AppDetails) -> bool:
        if response is None:
            return True

        return False

    @staticmethod
    async def check_success(response: AppDetails) -> bool:
        if response.success is False:
            return True

        return False

    @staticmethod
    async def check_type(app_type: str) -> bool:
        if app_type.lower() != 'game':
            return True

        return False

    @staticmethod
    async def check_market(app_market: dict) -> bool:
        if not app_market['results']:
            return True

        return False

    @staticmethod
    async def check_redirect(app_details_id: str, app_id: str) -> bool:
        if app_details_id != app_id:
            return True

        return False
