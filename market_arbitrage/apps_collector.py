import asyncio
from asyncio.proactor_events import _ProactorBasePipeTransport

from conf.settings import ALL_APPS_JSON_FILE, WORKERS_AMOUNT, \
    TIMEOUT, LOGS, ACCOUNTS, TIMEOUT_MARKET, OWNED_APPS_JSON_FOLDER
from request_handler.requests_handler import RequestHandler
from utils import Checker, silence_event_loop_closed
from database.database import Database
from database.utils import graceful_shutdown
from market_arbitrage.models import AppsSet
from apps.models import App, AppDetails, AppOwned
from market.models import CardBorder, ItemClass
from apps.apps_handler import AppsHandler
from market.market_handler import MarketHandler


class CollectAppsHandler:
    def __init__(self):
        self.db = None
        self.owned_db = None
        self.all_db = None
        self.requests_handler = None
        self.apps = None
        self.apps_amount = None
        self.cache_check = None
        self.file_handler = None
        self.scraper_func = None
        self.apps_handler = None
        self.market_handler = None
        self.checker = Checker()

    @classmethod
    async def init_all_apps(cls,
                            cache_check: tuple = ('blacklist', 'whitelist', 'no_cards'),
                            workers_amount: int = WORKERS_AMOUNT,
                            timeout: int = TIMEOUT,
                            timeout_market: int = TIMEOUT_MARKET,
                            proxy: bool = False):

        self = cls()
        self.cache_check = cache_check

        self.requests_handler = await RequestHandler.create(
            proxy=proxy,
            workers_amount=workers_amount,
            timeout=timeout
        )

        async with asyncio.TaskGroup() as tg:
            db = tg.create_task(
                Database.connect(location=ALL_APPS_JSON_FILE)
            )

            apps_handler = tg.create_task(AppsHandler.create(
                    proxy=proxy,
                    timeout=timeout,
                    requests_handler=self.requests_handler
                )
            )

            market_handler = tg.create_task(MarketHandler.create(
                    proxy=proxy,
                    timeout=timeout_market,
                    requests_handler=self.requests_handler
                )
            )

        self.db = db.result()
        self.apps_handler = apps_handler.result()
        self.market_handler = market_handler.result()

        self.scraper_func = self.all_apps_scraper
        self.apps = await self.apps_handler.get_apps_list()
        self.apps_amount = len(self.apps)

        return self

    @classmethod
    async def init_owned_apps(cls,
                              login: str,
                              cache_check: tuple = ('whitelist', 'no_cards', 'blacklist'),
                              workers_amount: int = WORKERS_AMOUNT,
                              timeout: int = TIMEOUT,
                              timeout_market: int = TIMEOUT_MARKET,
                              proxy: bool = False):

        self = cls()

        self.cache_check = cache_check

        self.requests_handler = await RequestHandler.create(
            proxy=proxy,
            workers_amount=workers_amount,
            timeout=timeout
        )

        async with asyncio.TaskGroup() as tg:
            db = tg.create_task(
                Database.connect(location=str(OWNED_APPS_JSON_FOLDER / f'{login}_apps.json'))
            )

            users_db = tg.create_task(
                Database.connect(location=str(ACCOUNTS), read_only=True)
            )

            apps_handler = tg.create_task(AppsHandler.create(
                    proxy=proxy,
                    timeout=timeout,
                    requests_handler=self.requests_handler
                )
            )

            market_handler = tg.create_task(MarketHandler.create(
                    proxy=proxy,
                    timeout=timeout_market,
                    requests_handler=self.requests_handler
                )
            )

        self.db = db.result()
        self.users_db = users_db.result()
        self.apps_handler = apps_handler.result()
        self.market_handler = market_handler.result()

        self.scraper_func = self.owned_apps_scraper
        self.apps = await self.apps_handler.get_owned_apps(
            api_key=self.users_db.data[login]['api_key'],
            steam_id=self.users_db.data[login]['steam_id']
        )
        self.apps_amount = len(self.apps)

        return self

    async def distribute_apps(self, app_details: AppDetails, app_name: str, session: callable):
        if await self.checker.check_response(response=app_details.response):
            apps_set = AppsSet(app_id=app_details.appid, apps_set='blacklist', app_name=app_name)
            await self.db.displace_object(object_id=app_details.appid, model=apps_set)
            return apps_set

        if await self.checker.check_success(response=app_details):
            apps_set = AppsSet(app_id=app_details.appid, apps_set='blacklist',
                               app_name=app_name, success=False, response=True)
            await self.db.displace_object(object_id=app_details.appid, model=apps_set)
            return apps_set

        app_details_id = str(app_details.data['steam_appid'])
        app_details_name = str(app_details.data['name'])
        app_details_type = str(app_details.data['type'])

        if await self.checker.check_type(app_type=app_details_type):
            apps_set = AppsSet(app_id=app_details.appid, apps_set='blacklist',
                               app_name=app_details_name, success=True, response=True,
                               app_type=app_details_type, redirect=app_details_id)
            await self.db.displace_object(object_id=app_details.appid, model=apps_set)
            return apps_set

        app_market_details = await self.market_handler.market_search(
            client_session=session,
            tag_app=app_details.appid,
            tag_item_class=ItemClass.Card,
            tag_cardborder=CardBorder.Normal
        )

        if await self.checker.check_market(app_market=app_market_details):
            apps_set = AppsSet(app_id=app_details.appid, apps_set='no_cards',
                               app_name=app_details_name, success=True, response=True,
                               app_type=app_details_type, redirect=app_details_id)
            await self.db.displace_object(object_id=app_details.appid, model=apps_set)
            return apps_set

        if await self.checker.check_redirect(app_details_id=app_details_id, app_id=app_details.appid):
            apps_set = AppsSet(app_id=app_details.appid, apps_set='blacklist',
                               app_name=app_details_name, success=True, response=True,
                               app_type=app_details_type, redirect=app_details_id)
            await self.db.displace_object(object_id=app_details.appid, model=apps_set)

        apps_set = AppsSet(app_id=app_details_id, apps_set='whitelist',
                           app_name=app_details_name, success=True, response=True,
                           app_type=app_details_type, redirect=app_details_id)
        await self.db.displace_object(object_id=app_details_id, model=apps_set)

        return apps_set

    async def all_apps_scraper(self, session: callable, app: App):
        app_id = str(app.appid)
        app_name = app.name

        if await self.db.is_cached(app_id, keys_to_check=self.cache_check):
            return None

        app_details = await self.apps_handler.get_app_details(app_id=app_id, client_session=session)

        apps_set = await self.distribute_apps(
            app_name=app_name,
            session=session,
            app_details=app_details,
        )

        LOGS['stdout_info'].info(
            f'APPID: {apps_set.app_id} - '
            f'REDIRECT: {apps_set.redirect} - '
            f'COUNT: {sum(len(v) for k, v in self.db.data.items())} of {self.apps_amount} - '
            f'ADDED: {apps_set.apps_set} - '
            f'WHITELIST: {len(self.db.data.get("whitelist")) if "whitelist" in self.db.data else None}'
        )

        return None

    async def check_prepared_list(self) -> None:
        all_db = await Database.connect(location=str(ALL_APPS_JSON_FILE), read_only=True)
        for app in self.apps:
            cache = await all_db.is_cached(str(app.appid), return_value=True, keys_to_check=self.cache_check)
            if cache:
                apps_set = AppsSet(
                    app_id=cache['value']['search_key'],
                    apps_set=cache['key_to_check'],
                    **cache['value']['search_key_value']
                )
                await self.db.displace_object(object_id=cache['value']['search_key'], model=apps_set)

                LOGS['stdout_info'].info(
                    f'APPID: {apps_set.app_id} - '
                    f'REDIRECT: {apps_set.redirect} - '
                    f'COUNT: {sum(len(v) for k, v in self.db.data.items())} of {self.apps_amount} - '
                    f'ADDED: {apps_set.apps_set} - '
                    f'WHITELIST: {len(self.db.data.get("whitelist")) if "whitelist" in self.db.data else None}'
                )

        await self.db.write()

        return None

    async def owned_apps_scraper(self, session: callable, app: AppOwned):
        app_id = str(app.appid)
        app_name = app.name

        if await self.db.is_cached(app_id, keys_to_check=self.cache_check):
            return None

        app_market_details = await self.market_handler.market_search(
            client_session=session,
            tag_app=app_id,
            tag_item_class=ItemClass.Card,
            tag_cardborder=CardBorder.Normal
        )

        if await self.checker.check_market(app_market=app_market_details):
            apps_set = AppsSet(app_id=app_id, apps_set='no_cards',
                               app_name=app_name, success=True,
                               response=True, app_type='game')
            await self.db.displace_object(object_id=app_id, model=apps_set)

            LOGS['stdout_info'].info(
                f'APPID: {apps_set.app_id} - '
                f'REDIRECT: {apps_set.redirect} - '
                f'COUNT: {sum(len(v) for k, v in self.db.data.items())} of {self.apps_amount} - '
                f'ADDED: {apps_set.apps_set} - '
                f'WHITELIST: {len(self.db.data.get("whitelist")) if "whitelist" in self.db.data else None}'
            )

            return None

        apps_set = AppsSet(app_id=app_id, apps_set='whitelist',
                           app_name=app_name, success=True,
                           response=True, app_type='game')
        await self.db.displace_object(object_id=app_id, model=apps_set)

        LOGS['stdout_info'].info(
            f'APPID: {apps_set.app_id} - '
            f'REDIRECT: {apps_set.redirect} - '
            f'COUNT: {sum(len(v) for k, v in self.db.data.items())} of {self.apps_amount} - '
            f'ADDED: {apps_set.apps_set} - '
            f'WHITELIST: {len(self.db.data.get("whitelist")) if "whitelist" in self.db.data else None}'
        )

        return None

    @graceful_shutdown
    async def collect_apps(self):
        return await self.requests_handler.create_workers(queue_items=self.apps, db=self.db, func=self.scraper_func)
