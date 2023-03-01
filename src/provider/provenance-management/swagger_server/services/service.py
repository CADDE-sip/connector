# -*- coding: utf-8 -*-
import json
import requests
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

# 送信履歴登録のcdleventtypeの値
__CDL_EVENT_TYPE_SENT = 'Sent'

# 接続先URL (仮の値)
__URL_HISTORY_EVENT_WITH_HASH = '/eventwithhash'

# 送信履歴登録のレスポンスの識別情報のキー
__EVENTWITHHASH_RESPONSE_EVENT_ID_KEY = 'cdleventid'

# コンフィグ情報
__CONFIG_PROVENANCE_FILE_PATH = '/usr/src/app/swagger_server/configs/provenance.json'
__CONFIG_PROVENANCE_MANAGEMENT_URL = 'provenance_management_api_url'

# データ証憑通知(送信)URL
__ACCESS_POINT_URL_CONTRACT_MANAGEMENT_SERVICET_CALL_VOUCHER_SENT = '/cadde/api/v4/voucher/sent'


def sent_history_registration(
        provider_id: str,
        consumer_id: str,
        resource_id_for_provenance: str,
        authorization: str,
        internal_interface: InternalInterface,
        external_interface: ExternalInterface) -> str:
    """
    来歴管理I/Fに送信履歴登録を依頼する

    Args:
        provider_id str: CADDEユーザID（提供者）
        consumer_id str: CADDEユーザID（利用者）
        resource_id_for_provenance str:  交換実績記録用リソースID
        authorization: str:  認証トークン
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : 外部にリクエストを行うインタフェース

    Returns:
        str : 識別情報

    Raises:
        Cadde_excption : コンフィグファイルからprovenance_management_api_urlを取得できない場合  エラーコード : 010301002E
        Cadde_excption : 来歴管理に登録できなかった場合                                         エラーコード : 010301003E

    """

    # コンフィグファイルからURL取得
    try:
        config = internal_interface.config_read(
            __CONFIG_PROVENANCE_FILE_PATH)
        server_url = config[__CONFIG_PROVENANCE_MANAGEMENT_URL]
    except Exception:
        raise CaddeException(
            message_id='010301002E',
            replace_str_list=[__CONFIG_PROVENANCE_MANAGEMENT_URL])

    if server_url.endswith('/'):
        server_url = server_url[:-1]

    body = {
        'cdldatamodelversion': '2.0',
        'cdleventtype': __CDL_EVENT_TYPE_SENT,
        'dataprovider': provider_id,
        'datauser': consumer_id,
        'cdlpreviousevents': [resource_id_for_provenance]
    }

    body_data = json.dumps(body, indent=2).encode()

    headers = {
        # HTTP header `Accept`
        'Accept': 'application/json'  # noqa: E501
    }
    if authorization is not None:
        headers['Authorization'] = authorization[7:]  # noqa: E501

    upfile = {'request': ('', body_data, 'application/json')}

    response = requests.post(
        server_url + __URL_HISTORY_EVENT_WITH_HASH, headers=headers, files=upfile)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='010301003E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)

    if 'cdleventid' not in response_text_dict or not response_text_dict['cdleventid']:
        raise CaddeException(message_id='010301004E')

    identification_information = response_text_dict['cdleventid']

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

    if contract_management_service_url.endswith('/'):
        contract_management_service_url = contract_management_service_url[:-1]

    access_url = contract_management_service_url + \
        __ACCESS_POINT_URL_CONTRACT_MANAGEMENT_SERVICET_CALL_VOUCHER_SENT
    response = external_interface.http_post(
        access_url, voucher_sent_headers, voucher_sent_body, False)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='010302002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    return response
