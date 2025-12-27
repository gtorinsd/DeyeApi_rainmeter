import configparser

__version__ = '0.6'


class Configs:
    def __init__(self, default_configs, config_file_path=None):
        self._config_file_path = config_file_path or 'config_local.ini'
        self._default_configs = default_configs

    def _get_ini_configs(self):
        ini_config = configparser.ConfigParser()
        ini_config.read(self._config_file_path)
        result = {}
        if 'settings' in ini_config.sections():
            for k, value in ini_config['settings'].items():
                key = k.upper()
                if key not in self._default_configs:
                    continue

                if isinstance(self._default_configs[key], bool):
                    result[key] = ini_config.getboolean('settings', key)
                else:
                    result[key] = value

        return result

    def _get_local_settings(self):
        # local mode
        ini_configs = self._get_ini_configs()
        if ini_configs:
            result = {}
            for name, value in self._default_configs.items():
                if name in ini_configs:
                    result[name] = ini_configs[name]
                else:
                    result[name] = value
            return result

        return self._default_configs

    def get_configs(self):
        return self._get_local_settings()

    @staticmethod
    def get_bool_value(value):
        return True if value and str(value).lower() in ('1', 'yes', 'true') else False
