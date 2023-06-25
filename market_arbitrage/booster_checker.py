import asyncio
from request_handler.requests_handler import RequestHandler
from conf.settings import WORKERS_AMOUNT, TIMEOUT_MARKET, OWNED_APPS_JSON_FOLDER, BOOSTER_PACKS_JSON_FILE, \
    ALL_APPS_JSON_FILE, PREDEFINED_APPS_JSON_FILE, LOGS
from market.models import MarketCategory, Currency, ItemClass, CardBorder, MarketItem
from utils import one_gem_price, convert_dict_to_list_of_AppInfo, high_variance_filter, \
    fee_eval, probability_of_list_part, arithmetic_mean, booster_pack_craft_cost
from market.utils import extract_price
from database.utils import graceful_shutdown
from market.market_handler import MarketHandler
from database.database import Database
from market_arbitrage.models import AppInfo, Booster
from typing import List, Union
from random import choice


class BoosterChecker:
    def __init__(self):
        self.db = None
        self.requests_handler = None
        self.apps_amount = None
        self.apps = None
        self.cookies = None
        self.market_handler = None
        self.gems_price = None

    @classmethod
    async def init_apps(cls, workers_amount: int = WORKERS_AMOUNT, timeout_market: int = TIMEOUT_MARKET,
                        proxy: bool = False, truncate_boosters_db: bool = False, use_predefined_apps_db: bool = False):
        self = cls()

        async with asyncio.TaskGroup() as tg:
            db = tg.create_task(
                Database.connect(location=str(BOOSTER_PACKS_JSON_FILE))
            )

            if use_predefined_apps_db:
                apps_db = tg.create_task(
                    Database.connect(location=PREDEFINED_APPS_JSON_FILE, read_only=True)
                )
            else:
                apps_db = tg.create_task(
                    Database.connect(location=ALL_APPS_JSON_FILE, read_only=True)
                )

            requests_handler = tg.create_task(RequestHandler.create(
                    proxy=proxy,
                    workers_amount=workers_amount,
                    timeout=timeout_market
                )
            )

        self.db = db.result()
        apps_db = apps_db.result()
        self.requests_handler = requests_handler.result()

        self.market_handler = await MarketHandler.create(
            proxy=proxy,
            timeout=timeout_market,
            requests_handler=self.requests_handler
        )

        self.gems_price = await self.mean_gems_price()

        if truncate_boosters_db:
            self.db.data.clear()

        self.apps = await convert_dict_to_list_of_AppInfo(apps_db.data['whitelist'])
        self.apps_amount = len(self.apps)

        return self

    @classmethod
    async def init_owned_apps(cls, login: str, workers_amount: int = WORKERS_AMOUNT,
                              timeout_market: int = TIMEOUT_MARKET, proxy: bool = False,
                              truncate_boosters_db: bool = False):
        self = cls()

        async with asyncio.TaskGroup() as tg:
            db = tg.create_task(
                Database.connect(location=str(BOOSTER_PACKS_JSON_FILE))
            )

            apps_db = tg.create_task(Database.connect(
                    location=str(OWNED_APPS_JSON_FOLDER / f'{login}_apps.json'),
                    read_only=True
                )
            )

            requests_handler = tg.create_task(RequestHandler.create(
                    proxy=proxy,
                    workers_amount=workers_amount,
                    timeout=timeout_market
                )
            )

        self.db = db.result()
        apps_db = apps_db.result()
        self.requests_handler = requests_handler.result()

        self.market_handler = await MarketHandler.create(
            proxy=proxy,
            timeout=timeout_market,
            requests_handler=self.requests_handler
        )

        self.gems_price = await self.mean_gems_price()

        if truncate_boosters_db:
            self.db.data.clear()

        self.apps = await convert_dict_to_list_of_AppInfo(apps_db.data['whitelist'])
        self.apps_amount = len(self.apps)

        return self

    async def mean_gems_price(self) -> float:
        sack_of_gems = await self.market_handler.get_price_overview(
            market_game=MarketCategory.STEAM,
            market_hash_name='753-Sack of Gems',
            currency=Currency.USD
        )

        one_gem_mean_price = await one_gem_price(float(sack_of_gems.lowest_price))

        return one_gem_mean_price

    async def eval_booster_cards_profit(self, cards_prices: List[Union[int, float]],
                                        booster_pack_gems_cost: int) -> float:
        mean_cards_price = await arithmetic_mean(cards_prices)
        card_fee = await fee_eval(mean_cards_price)
        sell_price = mean_cards_price - card_fee if mean_cards_price > 0 else 0
        booster_cards_sell_price = sell_price * 3

        booster_craft_currency_cost = booster_pack_gems_cost * self.gems_price

        booster_cards_profit = booster_cards_sell_price - booster_craft_currency_cost

        return round(booster_cards_profit, 3)

    async def eval_booster_pack_profit(self, booster_pack_price: float,
                                       booster_pack_gems_cost: int) -> float:
        booster_fee = await fee_eval(booster_pack_price)
        sell_price = booster_pack_price - booster_fee

        booster_craft_currency_cost = booster_pack_gems_cost * self.gems_price

        booster_pack_profit = sell_price - booster_craft_currency_cost

        return round(booster_pack_profit, 3)

    @staticmethod
    async def relatively_expensive_cards_handler(cards_prices: List[Union[int, float]]) -> Union[tuple, None]:
        expensive_cards = await high_variance_filter(cards_prices)
        if expensive_cards:
            probability = await probability_of_list_part(cards_prices, expensive_cards)
            return expensive_cards, probability

        return None, None

    async def check_cards_volume(self, cards: List[MarketItem], session) -> int:
        random_card = choice(cards)
        card_market_details = await self.market_handler.get_price_overview(
            market_hash_name=random_card.market_hash_name,
            client_session=session
        )
        cards_volume = card_market_details.volume
        return int(cards_volume)

    async def boosters_scraper(self, session: callable, app: AppInfo,
                               check_volume: bool = False, check_booster_pack: bool = True):
        app_id = app.app_id
        app_name = app.app_name

        async with asyncio.TaskGroup() as tg:
            market_cards = tg.create_task(
                self.market_handler.market_search(
                    tag_app=app_id,
                    tag_item_class=ItemClass.Card,
                    tag_cardborder=CardBorder.Normal,
                    client_session=session
                )
            )
            if check_booster_pack:
                market_booster = tg.create_task(
                    self.market_handler.get_price_overview(
                        market_hash_name=f'{app_id}-{app_name} Booster Pack',
                        client_session=session
                    )
                )
        market_cards = market_cards.result()
        market_booster = market_booster.result() if check_booster_pack else None

        cards_prices = [await extract_price(i.sell_price_text) for i in market_cards]

        booster_pack_gems_cost = await booster_pack_craft_cost(cards_prices)

        async with asyncio.TaskGroup() as tg:
            booster_cards_profit = tg.create_task(
                self.eval_booster_cards_profit(cards_prices, booster_pack_gems_cost)
            )
            high_variance_cards = tg.create_task(
                self.relatively_expensive_cards_handler(cards_prices)
            )

            if check_volume:
                cards_volume = tg.create_task(
                    self.check_cards_volume(cards=market_cards, session=session)
                )

            if check_booster_pack:
                booster_pack_profit = tg.create_task(
                    self.eval_booster_pack_profit(float(market_booster.lowest_price), booster_pack_gems_cost)
                )

        expensive_cards, probability = high_variance_cards.result()
        booster_cards_profit = booster_cards_profit.result()
        cards_volume = cards_volume.result() if check_volume else None
        booster_pack_profit = booster_pack_profit.result() if check_booster_pack else None
        booster_pack_volume = int(market_booster.volume) if check_booster_pack else None
        expensive_cards = len(expensive_cards) if expensive_cards is not None else None

        LOGS['stdout_info'].info(
            f'APPID: {app_id} - '
            f'GEMS PRICE: {self.gems_price} - '
            f'CARDS PROFIT: {booster_cards_profit} - '
            f'CARDS VOLUME: {cards_volume} - '
            f'BOOSTER PROFIT: {booster_pack_profit} - '
            f'BOOSTER VOLUME: {booster_pack_volume} - '
            f'EXPENSIVE CARDS: {expensive_cards} - '
            f'EXPENSIVE CARDS PROBABILITY {probability}'
        )

        booster_model = Booster(
            app_id=app_id,
            app_name=app_name,
            gems_price=str(self.gems_price),
            cards_profit=booster_cards_profit,
            cards_volume=cards_volume,
            booster_profit=booster_pack_profit,
            booster_volume=booster_pack_volume,
            expensive_cards=expensive_cards,
            expensive_cards_probability=str(probability),
        )

        await self.db.displace_object(object_id=app_id, model=booster_model)

    @graceful_shutdown
    async def check_boosters_profit(self, **kwargs):
        await self.requests_handler.create_workers(
            queue_items=self.apps,
            db=self.db,
            func=self.boosters_scraper,
            **kwargs
        )
