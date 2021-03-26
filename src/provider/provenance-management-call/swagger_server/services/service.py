# -*- coding: utf-8 -*-
import openapi_client
from openapi_client.api import register_event_api
from openapi_client.model.cdl_event import CDLEvent
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

# 送信履歴登録要求のcdleventtypeの値
__CDL_EVENT_TYPE_SENT = 'Sent'

# 送信履歴登録要求のレスポンスの識別情報のキー
__EVENTWITHHASH_RESPONSE_EVENT_ID_KEY = 'cdleventid'

# コンフィグ情報
__CONFIG_PROVENANCE_FILE_PATH = '/usr/src/app/swagger_server/configs/provenance.json'
__CONFIG_PROVENANCE_MANAGEMENT_URL = 'provenance_management_api_url'


def sent_history_registration(
        provider_id: str,
        consumer_id: str,
        caddec_resource_id_for_provenance: str,
        token: str,
        internal_interface: InternalInterface,
        external_interface: ExternalInterface) -> str:
    """
    来歴管理I/Fに送信履歴登録を依頼する

    Args:
        provider_id str: 提供者ID
        consumer_id str: 利用者ID
        caddec_resource_id_for_provenance str:  交換実績記録用リソースID
        token: str:  来歴管理者トークン(2021年3月版は未使用)
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : 外部にリクエストを行うインタフェース

    Returns:
        str : 識別情報

    Raises:
        Cadde_excption : コンフィグファイルからprovenance_management_api_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : 来歴管理に登録できなかった場合 エラーコード : 09002E
    """
    cdlpreviousevents = [caddec_resource_id_for_provenance]

    # コンフィグファイルからURL取得
    try:
        config = internal_interface.config_read(
            __CONFIG_PROVENANCE_FILE_PATH)
        server_url = config[__CONFIG_PROVENANCE_MANAGEMENT_URL]
    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[__CONFIG_PROVENANCE_MANAGEMENT_URL])

    configuration = openapi_client.Configuration(host=server_url)
    with openapi_client.ApiClient(configuration=configuration) as api_client:
        api_instance = register_event_api.RegisterEventApi(api_client)
        request = CDLEvent(
            cdldatamodelversion='2.0',
            cdleventtype=__CDL_EVENT_TYPE_SENT,
            cdlpreviousevents=cdlpreviousevents,
            datauser=consumer_id,
            dataprovider=provider_id)
        try:
            response = api_instance.eventwithhash(request=request)
            identification_information = response['cdleventid']
        except Exception as e:
            raise CaddeException(message_id='09002E',
                                 status_code=500,
                                 replace_str_list=[str(e)])

    return identification_information
