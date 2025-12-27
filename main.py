import logging
import hashlib
from handlers.ApiClient import ApiClient
from worker import Worker
from app_init import conf

# noinspection PyArgumentList
def init_log():
    log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s | %(name)-15s | %(funcName)-40s | %(levelname)-7s | %(message)s',
        handlers=[
            logging.FileHandler(filename='app.log', mode='w+'),
            # logging.StreamHandler(),
        ],
    )

def _encrypt_str(input_str: str) -> str:
    encoded_string = input_str.encode('utf-8')
    # Create a new sha256 hash object
    sha256_hash = hashlib.sha256()
    # Update the hash object with the encoded data
    sha256_hash.update(encoded_string)
    # Return the hexadecimal representation of the hash
    return sha256_hash.hexdigest()


if __name__ == '__main__':
    init_log()
    logging.info(f'App v 1.00')

    try:
        res = Worker(api=ApiClient(
                                base_url=conf['BASE_URL'],
                                email=conf['EMAIL'],
                                passw=_encrypt_str(conf['PASSW']),
                                app_id=conf['APPID'],
                                app_secret=conf['APPSECRET'],
                                bearer_token=conf['BEARER_TOKEN']
                            )
            ).work()
        for item in res:
            if type(res[item]) is dict:
                mess = f'{item}: {res[item]['value_str']}'
            else:
                mess = f'{item}: {res[item]}'
            logging.debug(mess)
            print(mess)
    finally:
        logging.info(f'Done')
