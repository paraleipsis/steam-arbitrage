import os.path

from database.database import Database, deep_update
from conf.settings import ACCOUNTS, Path, OWNED_APPS_JSON_FOLDER
from models import Account
from exceptions import AccountAlreadyExists, AccountDoesNotExist


class AccountManager:
    def __init__(self):
        self.db = None
        self.account_model = None

    @classmethod
    async def create(cls, account_model=Account):
        self = cls()
        self.db = await Database.connect(location=ACCOUNTS)
        self.account_model = account_model
        return self

    async def add_account(self, login, steam_id: str = None, api_key: str = None, shared_secret: str = None):
        if login in self.db.data:
            raise AccountAlreadyExists

        current_dir = Path(__file__).resolve().parent
        destination_dir = OWNED_APPS_JSON_FOLDER
        relative_path = os.path.relpath(destination_dir, start=current_dir)
        account_file = Path(relative_path) / f'{login}_apps.json'

        account = self.account_model(
            steam_id=steam_id,
            login=login,
            api_key=api_key,
            shared_secret=shared_secret,
            apps_path=str(account_file.as_posix())
        )

        account_file.touch()

        await self.db.save(account.dict())
        return account

    async def del_account(self, login) -> bool:
        if login not in self.db.data:
            raise AccountDoesNotExist

        account_data = await self.db.get(login)
        account = self.account_model(login=login, **account_data)
        await self.db.delete(account.login)
        Path(account.apps_path).unlink()
        return True

    async def update_account(self, login, **kwargs):
        if login not in self.db.data:
            raise AccountDoesNotExist

        account_data = await self.db.get(login)
        updated_dict = deep_update(account_data, kwargs)
        updated_account = self.account_model(login=login, **updated_dict)

        await self.db.save(updated_account.dict())

        return updated_account
