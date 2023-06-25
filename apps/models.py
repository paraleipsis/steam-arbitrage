from pydantic import BaseModel, Field
from datetime import date


class App(BaseModel):
    appid: int
    name: str


class AppOwned(BaseModel):
    appid: int
    name: str
    playtime_forever: int = Field(default=None)
    has_community_visible_stats: bool = Field(default=None)
    playtime_windows_forever: int = Field(default=None)
    playtime_mac_forever: int = Field(default=None)
    playtime_linux_forever: int = Field(default=None)
    rtime_last_played: int = Field(default=None)


class AppDetails(BaseModel):
    appid: str
    response: bool = Field(default=None)
    success: bool = Field(default=False)
    data: dict = Field(default=None)


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
