import json
import logging
from time import sleep

import requests


class ApiClient:
    cookies = None

    def __init__(self, base_url, email, passw, app_secret, app_id, bearer_token = None):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.userLogin = email
        self.userPwd = passw
        self.baseUrL = base_url
        self.app_secret = app_secret
        self.appId = app_id
        self.bearer_token = bearer_token
        self.TOKEN_FILE_PATH = 'token.json'

        self.headers = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36" # Chrome
        }


    @staticmethod
    def _get_result(r):
        data = None
        if r.status_code in [200, 201]:
            data = r.json()
            return r.status_code, data['response']
        elif r.status_code == 404:
            return r.status_code, r.json()
        else:
            return r.status_code, data

    def _request(self, method: str, path, params=None, data=None):
        url = self.baseUrL + path if path[0] == '/' else f'{self.baseUrL}/{path}'

        method = method.lower()
        r = None
        if method == 'get':
            r = requests.get(url, params=params, data=data, cookies=self.__class__.cookies)
        elif method == 'put':
            r = requests.put(url, data=data, cookies=self.__class__.cookies)
        elif method == 'post':
            r = requests.post(url, data=data, cookies=self.__class__.cookies)
        elif method == 'delete':
            r = requests.delete(url, data=data, cookies=self.__class__.cookies)
        return self._get_result(r)

    def auth(self, login:bool=False) -> bool:
        json_auth = {}
        if not login:
            # Read token from file
            try:
                with open(self.TOKEN_FILE_PATH, 'r') as file:
                    # Use json.load() to parse the file contents
                    json_auth = json.load(file)
                self.logger.info(f'Get token from file')
                self.bearer_token = json_auth[self.userLogin]
                return True
            except FileNotFoundError as ex:
                self.logger.warning(f'File not found: {self.TOKEN_FILE_PATH}')
            except Exception as ex:
                self.logger.warning(ex)

        credentials = {
            'email': self.userLogin,
            'password': self.userPwd,
            'appSecret': self.app_secret
        }
        self.logger.info(f'Login to Deye api portal')
        r = requests.post(self.baseUrL + '/account/token', json=credentials, params={'appId': self.appId})
        if r.status_code == 200:
            # Save token to file
            self.logger.info(f'OK')
            self.bearer_token = r.json()['accessToken']

            json_auth[self.userLogin] = self.bearer_token
            with open(self.TOKEN_FILE_PATH, 'w') as f:
                json.dump(json_auth, f)
            return True

        self.logger.warning(f'{r.status_code}, {r.json()}')
        return False

    def get_device_info(self, station):
        self.logger.info(f'Get device info for station {station}')
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'  # Often needed, but check API documentation
        }

        params = {
                    "deviceList": [station]
        }

        r = requests.post(self.baseUrL + '/device/latest', headers=headers, json=params)
        if r.status_code == 200:
            res = r.json()
            if not res['success']:
                self.logger.warning(res['msg'])
                # Get new token
                sleep(5)
                self.auth(login=True)
                return self.get_device_info(station=station)
            self.logger.info(f'OK')
            return res
        self.logger.warning(f'{r.status_code}, {r.json()}')
        return None

