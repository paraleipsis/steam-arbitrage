from pydantic import BaseModel


class Proxy(BaseModel):
    proxies: str
    host: str
    login: str
    password: str

    def dict(self, **kwargs) -> dict:
        return {
            self.proxies: [
                {
                    "host": self.host,
                    "login": self.login,
                    "password": self.password
                }
            ]
        }