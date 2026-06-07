import json
import logging
from time import sleep

import requests


class ApiClient:
    def __init__(self, base_url, email, passw, app_secret, app_id, bearer_token=None):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.user_login = email
        self.user_passw = passw
        self.base_url = base_url
        self.app_secret = app_secret
        self.appId = app_id
        self.bearer_token = bearer_token
        self.TOKEN_FILE_PATH = 'token.json'

    @staticmethod
    def _safe_body(r):
        try:
            return r.json()
        except ValueError:
            return r.text[:200]

    def auth(self, login: bool = False) -> bool:
        json_auth = {}
        if not login:
            # Read token from file
            try:
                with open(self.TOKEN_FILE_PATH, 'r') as file:
                    json_auth = json.load(file)
                self.logger.info('Get token from file')
                self.bearer_token = json_auth[self.user_login]
                return True
            except FileNotFoundError:
                self.logger.warning(f'File not found: {self.TOKEN_FILE_PATH}')
            except Exception as ex:
                self.logger.warning(ex)

        credentials = {
            'email': self.user_login,
            'password': self.user_passw,
            'appSecret': self.app_secret
        }
        self.logger.info('Login to Deye api portal')
        r = requests.post(
            self.base_url + '/account/token',
            json=credentials,
            params={'appId': self.appId},
            timeout=10,
        )
        if r.status_code == 200:
            # Save token to file
            self.logger.info('OK')
            self.bearer_token = r.json()['accessToken']

            json_auth[self.user_login] = self.bearer_token
            with open(self.TOKEN_FILE_PATH, 'w') as f:
                json.dump(json_auth, f)
            return True

        self.logger.warning(f'{r.status_code}, {self._safe_body(r)}')
        return False

    def _get_device_info(self, station):
        self.logger.info(f'Get device info for station {station}')
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'  # Often needed, but check API documentation
        }

        params = {
                    "deviceList": [station]
        }
        r = requests.post(self.base_url + '/device/latest', headers=headers, json=params, timeout=10)
        self.logger.info(f'{r.status_code}')
        return r

    def get_device_info(self, station):
        r = self._get_device_info(station=station)
        if r.status_code == 500:
            self.logger.info('One more try')
            sleep(5)
            r = self._get_device_info(station=station)
        if r.status_code == 200:
            res = r.json()
            if not res['success'] and res['msg'] == 'auth invalid token':
                self.logger.warning(res['msg'])
                # Get new token
                sleep(5)
                self.auth(login=True)
                r = self._get_device_info(station=station)
                if r.status_code == 200:
                    return r.json()
                self.logger.warning(f'{r.status_code}, {self._safe_body(r)}')
                return None
            self.logger.info('OK')
            return res
        self.logger.warning(f'{r.status_code}, {self._safe_body(r)}')
        return None
