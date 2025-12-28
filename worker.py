import datetime
import logging
from typing import List, Dict, Optional
from handlers.ApiClient import ApiClient


class Worker:
    def __init__(self, api: ApiClient):
        self.api_client = api
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _get_device_data_list_param(data_list, param_names: List) -> Dict:
        dict_values = {x['key']: x for x in data_list if x['key'] in param_names}
        return {x: {'value': dict_values[x]['value'], 'value_str': f"{dict_values[x]['value'].replace('℃', '°C')} {dict_values[x]['unit'].replace('℃', '°C')}"} for x in param_names}

    def work(self, station='2508271645') -> Optional[Dict]:
        if self.api_client.auth():
            r = self.api_client.get_device_info(station=station)
            device_info = r['deviceDataList'][0]['dataList']

            result = {
                'Station_id': station,
                'Updated at': datetime.datetime.strftime(datetime.datetime.fromtimestamp(r['deviceDataList'][0]['collectionTime']), '%#d-%#m-%#y %#H:%M:%S')
            }
            params = ['TotalGridPower', 'BatteryVoltage', 'DC Temperature', 'AC Temperature']
            # params = ['TotalGridPower', 'BatteryVoltage']
            result.update(self._get_device_data_list_param(data_list=device_info, param_names=params))

            if int(result['TotalGridPower']['value']) == 0:
                result['Source'] = 'BATTERY'
            else:
                result['Source'] = 'Grid'

            return result
        return None




