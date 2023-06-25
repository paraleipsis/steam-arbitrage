import base64
import hmac
import rsa

from time import time
from base64 import b64decode
from hashlib import sha1
from struct import pack, unpack

from request_handler.requests_handler import RequestHandler
from conf.settings import RSA_DATA_URL, LOGIN_URL


class SteamLoginHandler:
    def __init__(self):
        self.requests_handler = None
        self.client_session = None
        self.username = None
        self.password = None
        self.shared_secret = None
        self.session = None

    @classmethod
    async def create(cls, username, password, shared_secret):
        self = cls()

        self.username = username
        self.password = password
        self.shared_secret = shared_secret

        self.requests_handler = await RequestHandler.create()

        self.client_session = await self.requests_handler.create_session()

        return self

    async def login(self):
        login_data = await self.create_login_data()

        auth_response = await self.requests_handler.request_handler_post(
            session=self.client_session,
            url=LOGIN_URL,
            post_data=login_data
        )

        return auth_response

    async def get_rsa_params(self):
        params = {
            'username': self.username,
        }

        rsa_response = await self.requests_handler.request_handler(
            session=self.client_session,
            url=RSA_DATA_URL,
            params=params
        )

        rsa_response['publickey_mod'] = int(rsa_response['publickey_mod'], 16)
        rsa_response['publickey_exp'] = int(rsa_response['publickey_exp'], 16)

        return rsa_response

    async def encrypt_password(self, rsa_public_key) -> str:
        encrypted_password = base64.b64encode(rsa.encrypt(self.password.encode('utf-8'), rsa_public_key))
        return encrypted_password.decode("utf-8")

    # https://github.com/ValvePython/steam/blob/master/steam/guard.py
    async def generate_twofactor_code(self) -> str:
        timestamp = int(time())
        secret = b64decode(self.shared_secret)
        big_endian = pack('>Q', timestamp // 30)
        time_hmac = hmac.new(secret, big_endian, sha1).digest()

        start = ord(time_hmac[19:20]) & 0xF
        code_int = unpack('>I', time_hmac[start:start + 4])[0] & 0x7fffffff

        charset = '23456789BCDFGHJKMNPQRTVWXY'
        code = ''

        for _ in range(5):
            code_int, i = divmod(code_int, len(charset))
            code += charset[i]

        return code

    async def create_login_data(self) -> dict:
        rsa_params = await self.get_rsa_params()
        rsa_public_key = rsa.PublicKey(rsa_params['publickey_mod'], rsa_params['publickey_exp'])
        password = await self.encrypt_password(rsa_public_key)
        rsatimestamp = rsa_params['timestamp']
        guard_code = await self.generate_twofactor_code()

        login_data = {
            'password': password,
            'username': self.username,
            'twofactorcode': guard_code,
            'emailauth': '',
            'loginfriendlyname': '',
            'captchagid': '-1',
            'captcha_text': '',
            'emailsteamid': '',
            'rsatimestamp': rsatimestamp,
            'remember_login': True,
        }

        return login_data
