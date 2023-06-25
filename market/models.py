from pydantic import BaseModel, Field
import enum


class MarketItemPrice(BaseModel):
    success: bool
    lowest_price: str = Field(default=None)
    volume: str = Field(default=None)
    median_price: str = Field(default=None)
    currency: str = Field(default=None)
    currency_num: int = Field(default=None)


class MarketItem(BaseModel):
    appid: int
    classid: str
    instanceid: str
    tradable: int
    name: str
    market_name: str
    market_hash_name: str
    type: str
    commodity: int
    sell_price_text: str
    sell_listings: int


class MarketCategory(enum.IntEnum):
    STEAM = 753,
    DOTA2 = 570,
    CSGO = 730,
    TF2 = 440,
    PUBG = 578080,
    RUST = 252490,
    ETS2 = 227300,
    PAYDAY2 = 218620,
    KF2 = 232090


class ItemClass(enum.StrEnum):
    Card = 'tag_item_class_2'
    Emotion = 'tag_item_class_4'
    Background = 'tag_item_class_3'
    Booster = 'tag_item_class_5'
    SaleItem = 'tag_item_class_10'
    Consumable = 'tag_item_class_6'


class CardBorder(enum.StrEnum):
    Normal = 'tag_cardborder_0'
    Foil = 'tag_cardborder_1'


class DropRate(enum.StrEnum):
    Common = 'tag_droprate_0'
    Uncommon = 'tag_droprate_1'
    Rare = 'tag_droprate_2'
    Extraordinary = 'tag_droprate_3'


class Currency(enum.IntEnum):
    USD = 1
    GBP = 2
    EURO = 3
    CHF = 4
    RUB = 5
    PLN = 6
    BRL = 7
    JPY = 8
    NOK = 9
    IDR = 10
    MYR = 11
    PHP = 12
    SGD = 13
    THB = 14
    VND = 15
    KRW = 16
    TRY = 17
    UAH = 18
    MXN = 19
    CAD = 20
    AUD = 21
    NZD = 22
    CNY = 23
    INR = 24
    CLP = 25
    PEN = 26
    COP = 27
    ZAR = 28

