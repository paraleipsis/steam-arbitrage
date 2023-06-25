import asyncio
from asyncio.proactor_events import _ProactorBasePipeTransport

from conf.settings import ALL_APPS_JSON_FILE, OWNED_APPS_JSON_FOLDER, PREDEFINED_APPS_JSON_FILE, BOOSTER_PACKS_JSON_FILE
from utils import silence_event_loop_closed
from database.database import Database

from models import Booster, AppInfo


class DataHandler:
    def __init__(self):
        self.login = None
        self.db = None
        self.data = None

    @classmethod
    async def init_apps(cls, predefined_apps: bool = False):
        self = cls()

        if predefined_apps:
            self.db = await Database.connect(location=PREDEFINED_APPS_JSON_FILE)
        else:
            self.db = await Database.connect(location=ALL_APPS_JSON_FILE)

        self.data = {
            outer_k: [
                AppInfo(app_id=inner_k, **inner_v)
                for inner_k, inner_v in outer_v.items()
            ]
            for outer_k, outer_v in self.db.data.items()
        }

        return self

    @classmethod
    async def init_user_apps(cls, login: str):
        self = cls()

        self.db = await Database.connect(location=str(OWNED_APPS_JSON_FOLDER / f'{login}_apps.json'))
        self.data = {
            outer_k: [
                AppInfo(app_id=inner_k, **inner_v)
                for inner_k, inner_v in outer_v.items()
            ]
            for outer_k, outer_v in self.db.data.items()
        }

        return self

    @classmethod
    async def init_boosters(cls):
        self = cls()

        self.db = await Database.connect(location=BOOSTER_PACKS_JSON_FILE)
        self.data = [Booster(app_id=k, **v) for k, v in self.db.data.items()]

        return self

    async def get_data(self) -> dict:
        return self.data
