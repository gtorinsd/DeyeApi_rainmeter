import datetime
import logging
from typing import List, Dict, Optional, Any
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
            updated_at = datetime.datetime.strftime(datetime.datetime.fromtimestamp(r['deviceDataList'][0]['collectionTime']), '%d.%m.%Y %H:%M:%S')
            self.logger.info(f'Updated at: {updated_at}')

            params = ['TotalGridPower', 'SOC', 'DC Temperature', 'AC Temperature', 'Temperature- Battery', 'InverterOutputPowerL1L2']
            result: Dict[str, Any] = {
                'Station_id': station,
                'Updated at': updated_at,
                **self._get_device_data_list_param(data_list=device_info, param_names=params),
            }

            if int(result['TotalGridPower']['value']) == 0:
                power_source = 'BATTERY'
            else:
                power_source = 'Grid'
                result['InverterOutputPowerL1L2']['value'] = 0
                result['InverterOutputPowerL1L2']['value_str'] = '0 W'

            self.logger.info(f'Power source: {power_source}')

            result['Source'] = power_source

            return result
        return None




