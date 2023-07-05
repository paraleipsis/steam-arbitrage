# Steam Arbitrage
Async library for finding Steam booster packs arbitrage, sorting Steam apps into categories, managing accounts and interacting with the Steam Market.

## Installation
- Install Python 3.11+
- Clone this repository
- Install requirements:

```bash
pip install -r requirements.txt
```
  
## Usage
To collect information about Steam applications and sort them by category, you can use `CollectAppsHandler`:
- blacklist - request to detail the application returned nothing or the success key returned false (the application was removed from Steam or not available in the region), and also if the application type was on the block list. Those applications that are guaranteed not to have and will never have cards, therefore they can be skipped without making extra requests;
- no_cards - a request to the market items for this application returned an empty list - it means there are no cards. Applications can be used for re-sorting, as cards may be added to some applications after some time;
- whitelist - a request to the market items for this application returned NOT an empty list - there are cards. Applications can be used to check the profit from converting gems into boosters and selling them.

```python
import asyncio
from market_arbitrage.apps_collector import CollectAppsHandler

async def get_data():
    # you can change proxy in /database/data/requests/proxy.json

    # the more worker the faster the check will be

    # get and sort all Steam apps
    collect_all_apps = await CollectAppsHandler.init_all_apps(
        workers_amount=1, 
        proxy=False
    )

    # get and sort only owned Steam apps
    collect_owned_apps = await CollectAppsHandler.init_owned_apps(
        workers_amount=1, 
        proxy=False, 
        login='login'
    )

    # run collectors
    await collect_all_apps.collect_apps()
    await collect_owned_apps.collect_apps()

    # re-sort file with all Steam apps
    await collect_apps_handler.check_prepared_list()

    return None


asyncio.run(get_data())
```

To check booster packs and trading cards you can use `BoosterChecker`.

```python
import asyncio
from market_arbitrage.booster_checker import BoosterChecker

async def find_arbitrage():
    # use_predefined_apps_db argument will check apps from /database/data/apps/predefined_apps.json

    # without arguments all Steam applications in the all_apps.json file will be checked
    set_all_checker = await BoosterChecker.init_apps(
        use_predefined_apps_db=True, 
        workers_amount=1
    )

    set_owned_checker = await BoosterChecker.init_owned_apps(
        login='login', 
        workers_amount=1
    )

    all_checker = await set_all_checker.check_boosters_profit(
        check_booster_pack=True, 
        check_volume=False
    )
    owned_checker = await set_owned_checker.check_boosters_profit(
        check_booster_pack=True, 
        check_volume=False
    )

    # you can find results in /database/data/profit/booster_packs.json

    return {
        "all_checker": all_checker,
        "owned_checker": owned_checker
    }


asyncio.run(find_arbitrage())
```

To get the collected information from the db about Steam applications and booster packs you can use the `DataHandler`.

```python
import asyncio
from market_arbitrage.data_handler import DataHandler

async def get_collected_data():
    # owned apps on account
    owned_apps = await DataHandler.init_user_apps(login='login')
    owned_apps_data = await owned_apps.get_data()
    print(owned_apps_data)

    # all Steam apps and predefined apps
    all_apps = await DataHandler.init_apps(predefined_apps=True)
    all_apps_data = await all_apps.get_data()
    print(all_apps_data)

    # checked booster packs
    boosters = await DataHandler.init_boosters()
    boosters_data = await boosters.get_data()
    print(boosters_data)

    return None


asyncio.run(get_collected_data())
```

For accounts management you can use the `AccountManager`.

```python
import asyncio
from account_manager.account_manager import AccountManager

async def manage_account():
    manager = await AccountManager.create()

    # add an account to the local db and create a JSON file with the applications on it
    await manager.add_account(
        login='login',
        steam_id='steam_id',
        api_key='api_key',
        shared_secret='shared_secret'
    )

    # delete account and file with applications
    await manager.del_account(login='login')

    # update some info
    await manager.update_account(login='login', shared_secret=None)


asyncio.run(manage_account())
```

To get information about Steam applications without writing to the local database you can use `AppsHandler`.

```python
import asyncio
from apps.apps_handler import AppsHandler

async def get_steam_apps():
    apps = await AppsHandler.create()

    owned_apps = await apps.get_owned_apps(steam_id='steam_id', api_key='api_key')
    all_steam_apps = await apps.get_apps_list()
    app_details = await apps.get_app_details(app_id='app_id')

    return {
        "owned_apps": owned_apps,
        "all_steam_apps": all_steam_apps,
        "some_app_details": app_details
    }


asyncio.run(get_steam_apps())
```

To interact with Steam market you can use `MarketHandler`.

```python
import asyncio
from market.market_handler import MarketHandler

async def market_handler():
    market = await MarketHandler.create()

    item_price_overview = await market.get_price_overview(
        market_game=MarketCategory.STEAM,
        market_hash_name='753-Sack of Gems',
        currency=Currency.USD
    )

    # get information about application trading cards
    market_search = await market.market_search(
        tag_app='7520',
        tag_item_class=ItemClass.Card,
        tag_cardborder=CardBorder.Normal
    )

    return {
        "sack_of_gems_price": item_price_overview,
        "cards_of_7520": market_search
    }

asyncio.run(market_handler())
```
