from request_handler.requests_handler import RequestHandler
from conf.settings import WORKERS_AMOUNT, TIMEOUT, ALL_APPS_URL, OWNED_APPS_URL, APP_DETAILS_URL
from apps.models import App, AppDetails, AppOwned
from typing import List, Union


class AppsHandler:
    def __init__(self):
        self.proxy = None
        self.workers_amount = None
        self.timeout = None
        self.requests_handler = None
        self.client_session = None

    @classmethod
    async def create(
            cls,
            workers_amount: int = WORKERS_AMOUNT,
            timeout: int = TIMEOUT,
            proxy: bool = False,
            requests_handler: RequestHandler = None,
    ):
        self = cls()

        self.workers_amount = workers_amount
        self.timeout = timeout
        self.proxy = proxy

        if requests_handler is None:
            self.requests_handler = await RequestHandler.create(
                proxy=self.proxy,
                workers_amount=self.workers_amount,
                timeout=self.timeout
            )
        else:
            self.requests_handler = requests_handler

        return self

    async def get_apps_list(self, client_session: callable = None) -> Union[None, List[App]]:
        if client_session is None:
            client_session = await self.requests_handler.create_session()

        response = await self.requests_handler.request_handler(
            session=client_session,
            url=ALL_APPS_URL,
        )

        if response['applist']['apps']:
            results = [App(**item) for item in response['applist']['apps']]

            return results

        return None

    async def get_owned_apps(self, api_key: str, steam_id: str, include_appinfo: bool = True,
                             include_played_free_games: bool = True,
                             client_session: callable = None) -> Union[None, List[AppOwned]]:
        if client_session is None:
            client_session = await self.requests_handler.create_session()

        params = {
            'key': api_key,
            'steamid': steam_id,
            'format': 'json',
            'include_appinfo': str(include_appinfo).lower(),
            'include_played_free_games': str(include_played_free_games).lower()
        }

        response = await self.requests_handler.request_handler(
            session=client_session,
            url=OWNED_APPS_URL,
            params=params
        )

        if response['response']['games']:
            results = [AppOwned(**item) for item in response['response']['games']]

            return results

        return None

    async def get_app_details(self, app_id: str, client_session: callable = None) -> AppDetails | None:
        if client_session is None:
            client_session = await self.requests_handler.create_session()

        params = {
            'appids': app_id
        }

        response = await self.requests_handler.request_handler(
            session=client_session,
            url=APP_DETAILS_URL,
            params=params
        )

        if response is not None:
            app = AppDetails(appid=app_id, response=True, **response[app_id])
            return app
        else:
            app = AppDetails(appid=app_id)
            return app
