from pydantic import BaseModel, Field
from datetime import date


class Booster(BaseModel):
    app_id: str
    app_name: str
    added: str = Field(default=str(date.today()), compare=False, hash=False, repr=False)
    gems_price: str = Field(default=None, compare=False, hash=False, repr=False)
    cards_profit: str = Field(default=None, compare=False, hash=False, repr=False)
    cards_volume: int = Field(default=None, compare=False, hash=False, repr=False)
    booster_profit: str = Field(default=None, compare=False, hash=False, repr=False)
    booster_volume: int = Field(default=None, compare=False, hash=False, repr=False)
    expensive_cards: int = Field(default=None, compare=False, hash=False, repr=False)
    expensive_cards_probability: str = Field(default=None, compare=False, hash=False, repr=False)

    def dict(self, **kwargs) -> dict:
        return {
            self.app_id: {
                'app_name': self.app_name,
                'gems_price': self.gems_price,
                'cards_profit': self.cards_profit,
                'cards_volume': self.cards_volume,
                'booster_profit': self.booster_profit,
                'booster_volume': self.booster_volume,
                'expensive_cards': self.expensive_cards,
                'expensive_cards_probability': self.expensive_cards_probability,
                'added': self.added
            }
        }


class AppInfo(BaseModel):
    app_id: str
    app_name: str
    added: str = Field(default=str(date.today()), compare=False, hash=False, repr=False)
    response: bool = Field(default=None, compare=False, hash=False, repr=False)
    success: bool = Field(default=None, compare=False, hash=False, repr=False)
    redirect: str = Field(default=None, compare=False, hash=False, repr=False)
    app_type: str = Field(default=None, compare=False, hash=False, repr=False)


class AppsSet(BaseModel):
    apps_set: str
    app_id: str
    app_name: str
    added: str = Field(default=str(date.today()), compare=False, hash=False, repr=False)
    response: bool = Field(default=None, compare=False, hash=False, repr=False)
    success: bool = Field(default=None, compare=False, hash=False, repr=False)
    redirect: str = Field(default=None, compare=False, hash=False, repr=False)
    app_type: str = Field(default=None, compare=False, hash=False, repr=False)

    def dict(self, **kwargs) -> dict:
        return {
            self.apps_set: {
                self.app_id: {
                    'app_name': self.app_name,
                    'response': self.response,
                    'success': self.success,
                    'redirect': self.redirect,
                    'app_type': self.app_type,
                    'added': self.added
                }
            }
        }
