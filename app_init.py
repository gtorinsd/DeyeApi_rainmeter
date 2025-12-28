from handlers.Configs import Configs

# init configs
conf = Configs(
    default_configs={
        'DEBUG': 0,

        'BASE_URL': None,
        'EMAIL': None,
        'PASSW': None,
        'APPID': None,
        'APPSECRET': None,
    },

    config_file_path='config_local.ini'
).get_configs()


def get_bool_config_value(value):
    return True if str(value).lower() in ('1', 'yes', 'true') else False


for param in [x for x in ['DEBUG'] if x in conf]:
    conf[param] = get_bool_config_value(conf[param])
