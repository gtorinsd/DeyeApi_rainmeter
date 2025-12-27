
import logging
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

    def auth(self) -> bool:
        credentials = {
            'email': self.userLogin,
            'password': self.userPwd,
            'appSecret': self.app_secret
        }
        self.logger.debug(f'Login to Deye api portal')
        r = requests.post(self.baseUrL + '/account/token', json=credentials, params={'appId': self.appId})
        if r.status_code == 200:
            self.logger.debug(f'OK')
            self.bearer_token = r.json()['accessToken']
            return True
        self.logger.debug(f'{r.status_code}, {r.json()}')
        return False

    def get_device_info(self, station):
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'  # Often needed, but check API documentation
        }

        params = {
                    "deviceList": [station]
        }

        r = requests.post(self.baseUrL + '/device/latest', headers=headers, json=params)
        if r.status_code == 200:
            return r.json()
        return None

