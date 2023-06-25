from pathlib import Path
from conf.logs.logs_configs import load_config
from decouple import config

BASE_DIR = Path(__file__).resolve().parent

LOGS = load_config()

ALL_APPS_URL = config('ALL_APPS_URL')
OWNED_APPS_URL = config('OWNED_APPS_URL')
APP_DETAILS_URL = config('APP_DETAILS_URL')
RSA_DATA_URL = config('RSA_DATA_URL')
LOGIN_URL = config('LOGIN_URL')
MARKET_PRICE_OVERVIEW_URL = config('MARKET_PRICE_OVERVIEW_URL')
MARKET_SEARCH_URL = config('MARKET_SEARCH_URL')

TIMEOUT = int(config('TIMEOUT'))
TIMEOUT_MARKET = int(config('TIMEOUT_MARKET'))
WORKERS_AMOUNT = int(config('WORKERS_AMOUNT'))

ALL_APPS_JSON_FILE = BASE_DIR.parent / Path(config('ALL_APPS_JSON_FILE'))
PREDEFINED_APPS_JSON_FILE = BASE_DIR.parent / Path(config('PREDEFINED_APPS_JSON_FILE'))
BOOSTER_PACKS_JSON_FILE = BASE_DIR.parent / Path(config('BOOSTER_PACKS_JSON_FILE'))
OWNED_APPS_JSON_FOLDER = BASE_DIR.parent / Path(config('OWNED_APPS_JSON_FOLDER'))
PROXIES = BASE_DIR.parent / Path(config('PROXIES'))
USER_AGENTS = BASE_DIR.parent / Path(config('USER_AGENTS'))
ACCOUNTS = BASE_DIR.parent / Path(config('ACCOUNTS'))
