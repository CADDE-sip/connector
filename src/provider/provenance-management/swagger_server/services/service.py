# -*- coding: utf-8 -*-
import openapi_client
from openapi_client.api import register_event_api
from openapi_client.model.cdl_event import CDLEvent
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

# 送信履歴登録のcdleventtypeの値
__CDL_EVENT_TYPE_SENT = 'Sent'

# 送信履歴登録のレスポンスの識別情報のキー
__EVENTWITHHASH_RESPONSE_EVENT_ID_KEY = 'cdleventid'

# コンフィグ情報
__CONFIG_PROVENANCE_FILE_PATH = '/usr/src/app/swagger_server/configs/provenance.json'
__CONFIG_PROVENANCE_MANAGEMENT_URL = 'provenance_management_api_url'


def sent_history_registration(
        provider_id: str,
        consumer_id: str,
        cadde_resource_id_for_provenance: str,
        authorization: str,
        internal_interface: InternalInterface,
        external_interface: ExternalInterface) -> str:
    """
    来歴管理I/Fに送信履歴登録を依頼する

    Args:
        provider_id str: CADDEユーザID（提供者）
        consumer_id str: CADDEユーザID（利用者）
        cadde_resource_id_for_provenance str:  交換実績記録用リソースID
        authorization: str:  認証トークン
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : 外部にリクエストを行うインタフェース

    Returns:
        str : 識別情報

    Raises:
        Cadde_excption : コンフィグファイルからprovenance_management_api_urlを取得できない場合  エラーコード : 010301002E
        Cadde_excption : 来歴管理に登録できなかった場合                                         エラーコード : 010301003E

    """
    cdlpreviousevents = [cadde_resource_id_for_provenance]

    # コンフィグファイルからURL取得
    try:
        config = internal_interface.config_read(
            __CONFIG_PROVENANCE_FILE_PATH)
        server_url = config[__CONFIG_PROVENANCE_MANAGEMENT_URL]
    except Exception:
        raise CaddeException(
            message_id='010301002E',
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
        except Exception as e:
            raise CaddeException(message_id='010301003E',
                                 replace_str_list=[str(e)])

        if 'cdleventid' not in response:
            raise CaddeException(message_id='010301004E')

        identification_information = response['cdleventid']
    return identification_information, server_url


def voucher_sent_call(
        provider_id: str,
        consumer_id: str,
        contract_id: str,
        hash_get_data: str,
        contract_management_service_url: str,
        authorization: str,
        external_interface: ExternalInterface) -> str:
    """
    データ証憑通知（受信）を行う。

    Args:
       provider_id str : CADDEユーザID（提供者）
       consumer_id str : CADDEユーザID（利用者）
       contract_id str : 取引ID
       hash_get_data str : ハッシュ値
       contract_management_service_url str : 契約管理サービスURL
       authorization str : 認証トークン
       external_interface ExternalInterface : 外部にリクエストを行うインタフェース

    Returns:
        Response : 来歴管理I/Fのレスポンス

    Raises:
        Cadde_excption : エラーが発生している場合は エラーコード : 010302002E

    """

    voucher_sent_headers = {
        'Authorization': authorization
    }
    voucher_sent_body = {
        'consumer_id': consumer_id,
        'provider_id': provider_id,
        'contract_id': contract_id,
        'hash': hash_get_data
    }
    response = external_interface.http_post(
        contract_management_service_url, voucher_sent_headers, voucher_sent_body, False)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='010302002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    return response
