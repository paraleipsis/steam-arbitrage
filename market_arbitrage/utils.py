from functools import wraps
from apps.models import AppDetails
from market.models import MarketItem
from market_arbitrage.models import AppInfo
import statistics
from statistics import StatisticsError
from typing import List, Union, Mapping


async def booster_pack_craft_cost(data: List[Union[float, int]]) -> int:
    booster_craft_cost = 6000 / len(data)
    return int(booster_craft_cost)


async def fee_eval(sell_price: float) -> float:
    fee = max(0.01, 0.05 * sell_price) + max(0.01, 0.10 * sell_price)

    return fee


async def arithmetic_mean(data: List[Union[float, int]]) -> Union[float, int]:
    mean = sum(data) / len(data)
    return round(mean, 3)


async def weighted_average(data: List[float]) -> Union[float, int]:
    weights = [value / sum(data) for value in data]
    weighted_arithmetic_mean = sum(d * w for d, w in zip(data, weights)) / sum(weights)

    return weighted_arithmetic_mean


async def high_variance_filter(data: List[Union[int, float]], __maxed_values=None) -> list:
    maxed_values = __maxed_values or []

    if __maxed_values is None:
        data = data.copy()

    try:
        variance = statistics.variance(data)
    except StatisticsError:
        return maxed_values

    if variance > 0.05:
        max_value = data.pop(data.index(max(data)))
        maxed_values.append(max_value)
        return await high_variance_filter(data=data, __maxed_values=maxed_values)

    return maxed_values


async def probability_of_list_part(data: list, data_part: list) -> float:
    probability = len(data_part) / len(data)
    return round(probability, 2)


async def convert_dict_to_list_of_AppInfo(
        dict_of_dicts: Mapping[str, Mapping[str, Union[str, int, bool]]]) -> List[AppInfo]:
    lst = [AppInfo(app_id=item_k, **item_v) for item_k, item_v in dict_of_dicts.items()]
    return lst


async def one_gem_price(sack_of_gems_price: float) -> float:
    price = sack_of_gems_price / 1000
    rounded_price = round(price, 7)

    return rounded_price


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
    async def check_response(response: bool | None) -> bool:
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
    async def check_market(app_market: MarketItem) -> bool:
        if app_market is None:
            return True

        return False

    @staticmethod
    async def check_redirect(app_details_id: str, app_id: str) -> bool:
        if app_details_id != app_id:
            return True

        return False
