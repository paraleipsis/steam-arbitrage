from request_handler.requests_handler import RequestHandler
from conf.settings import WORKERS_AMOUNT, TIMEOUT_MARKET, MARKET_PRICE_OVERVIEW_URL, MARKET_SEARCH_URL
from market.models import MarketCategory, MarketItemPrice, Currency, MarketItem, ItemClass, CardBorder, DropRate
from market.utils import extract_price, convert_comma_to_int, dict_none_filter
from typing import List, Union


class MarketHandler:
    def __init__(self):
        self.proxy = None
        self.workers_amount = None
        self.timeout = None
        self.db = None
        self.requests_handler = None
        self.client_session = None
        self.apps_db = None
        self.apps_amount = None
        self.apps = None

    @classmethod
    async def create(cls, workers_amount: int = WORKERS_AMOUNT,
                     timeout: int = TIMEOUT_MARKET, proxy: bool = False,
                     requests_handler: RequestHandler = None):
        self = cls()

        self.proxy = proxy
        self.workers_amount = workers_amount
        self.timeout = timeout

        if requests_handler is None:
            self.requests_handler = await RequestHandler.create(
                proxy=self.proxy,
                workers_amount=self.workers_amount,
                timeout=self.timeout
            )
        else:
            self.requests_handler = requests_handler

        return self

    async def get_price_overview(
            self,
            market_hash_name: str,
            market_game: MarketCategory = MarketCategory.STEAM,
            currency: Currency = Currency.USD,
            client_session: callable = None
    ) -> MarketItemPrice:

        if client_session is None:
            client_session = await self.requests_handler.create_session()

        params = {
            'currency': currency.value,
            'appid': market_game.value,
            'market_hash_name': market_hash_name
        }

        response_market = await self.requests_handler.request_handler(
            session=client_session,
            url=MARKET_PRICE_OVERVIEW_URL,
            params=params
        )

        for i in ('lowest_price', 'volume', 'median_price'):
            if i not in response_market:
                response_market[i] = '0'

        market_item = MarketItemPrice(
            success=response_market['success'],
            lowest_price=await extract_price(response_market['lowest_price']),
            volume=await convert_comma_to_int(response_market['volume']),
            median_price=await extract_price(response_market['median_price']),
            currency=Currency(currency.value).name,
            currency_num=currency.value
        )

        return market_item

    async def market_search(
            self,
            category: MarketCategory = MarketCategory.STEAM,
            start: int = 0,
            count: int = 100,
            no_render: int = 1,
            sort_column: str = None,
            tag_app: str = None,
            tag_item_class: ItemClass = None,
            tag_cardborder: CardBorder = None,
            tag_droprate: DropRate = None,
            sort_dir: str = 'asc',
            search_descriptions: int = 0,
            query: str = None,
            client_session: callable = None
    ) -> Union[None, List[MarketItem]]:
        if client_session is None:
            client_session = await self.requests_handler.create_session()

        params = {
            'start': start,
            'count': count,
            'norender': no_render,
            'appid': category.value,
            'sort_column': sort_column,
            'sort_dir': sort_dir,
            'search_descriptions': search_descriptions,
            'category_753_Game[]': f'tag_app_{tag_app}' if tag_app else None,
            'category_753_item_class[]': tag_item_class.value if tag_item_class else None,
            'category_753_cardborder[]': tag_cardborder.value if tag_cardborder else None,
            'category_753_droprate[]': tag_droprate.value if tag_droprate else None,
            'query': query
        }

        response_market = await self.requests_handler.request_handler(
            session=client_session,
            url=MARKET_SEARCH_URL,
            params=await dict_none_filter(params)
        )

        results = []
        if response_market['results']:
            for item in response_market['results']:
                market_item = MarketItem(
                    appid=item['asset_description']['appid'],
                    classid=item['asset_description']['classid'],
                    instanceid=item['asset_description']['instanceid'],
                    tradable=item['asset_description']['tradable'],
                    name=item['asset_description']['name'],
                    market_name=item['asset_description']['market_name'],
                    market_hash_name=item['asset_description']['market_hash_name'],
                    type=item['asset_description']['type'],
                    commodity=item['asset_description']['commodity'],
                    sell_price_text=item['sell_price_text'],
                    sell_listings=item['sell_listings'],
                )
                results.append(market_item)

            return results

        return None

    async def create_buy_order(self):
        pass

    async def create_sell_order(self):
        pass

    async def buy_listing(self):
        pass

    async def confirm_sell_order(self):
        pass
