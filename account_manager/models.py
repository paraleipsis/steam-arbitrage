from pydantic import BaseModel, Field


class Account(BaseModel):
    login: str
    password: str = Field(default=None, compare=False, hash=False, repr=False)
    apps_path: str = Field(default=None, compare=False, hash=False, repr=False)
    steam_id: str = Field(default=None, compare=False, hash=False, repr=False)
    api_key: str = Field(default=None, compare=False, hash=False, repr=False)
    shared_secret: str = Field(default=None, compare=False, hash=False, repr=False)
    currency: str = Field(default=None, compare=False, hash=False, repr=False)

    def dict(self, **kwargs) -> dict:
        return {
            self.login: {
                "steam_id": self.steam_id,
                "api_key": self.api_key,
                "shared_secret": self.shared_secret,
                "apps_path": self.apps_path,
                "currency": self.currency
            }
        }
