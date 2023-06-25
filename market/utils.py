import re
from typing import Union


async def convert_comma_to_int(string: str) -> Union[int, None]:
    if string is None:
        return None

    string = string.replace(',', '')

    return int(string)


async def extract_price(price: str) -> Union[float, None]:
    if price is None:
        return None

    list_of_numbers = re.findall('\d+', price)
    price_without_currency = '.'.join(list_of_numbers).strip()

    return float(price_without_currency)


async def dict_none_filter(dictionary: dict) -> dict:
    return dict(filter(lambda x: x[1] is not None, dictionary.items()))
