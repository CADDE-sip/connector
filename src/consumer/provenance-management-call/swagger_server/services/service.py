# -*- coding: utf-8 -*-
from flask import Response
import openapi_client
from openapi_client.api import register_event_api
from openapi_client.model.cdl_event import CDLEvent
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

# 接続先URL (仮の値)
__URL_HISTORY_LINEAGE = '/lineage/'
__URL_HISTORY_SEARCHEVENTS =  '/searchevents'

# コンフィグ情報
__CONFIG_PROVENANCE_FILE_PATH = '/usr/src/app/swagger_server/configs/provenance.json'
__CONFIG_PROVENANCE_MANAGEMENT_URL = 'provenance_management_api_url'

# 受信履歴登録要求のcdleventtypeの値
__CDL_EVENT_TYPE_RECEIVED = 'Received'

# 受信履歴登録要求のレスポンスの識別情報のキー
__EVENTWITHHASH_RESPONSE_EVENT_ID_KEY = 'cdleventid'

# 履歴取得方向の正常値リスト
__DIRECTION_NORMALITY_VALUES = ['BACKWARD', 'FORWARD', 'BOTH']

# 検索深度の最低値
__DEPTH_MIN_VALUE = -1


def received_history_registration(
        provider_id: str,
        consumer_id: str,
        caddec_resource_id_for_provenance: str,
        token: str,
        internal_interface: InternalInterface,
        external_interface: ExternalInterface) -> str:
    """
    来歴管理I/Fに受信履歴登録を依頼する

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
        Cadde_excption : 来歴管理に登録できなかった場合 エラーコード : 19002E
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
            cdleventtype=__CDL_EVENT_TYPE_RECEIVED,
            cdlpreviousevents=cdlpreviousevents,
            datauser=provider_id,
            dataprovider=consumer_id)
        try:
            response = api_instance.eventwithhash(request=request)
            identification_information = response['cdleventid']
        except Exception as e:
            raise CaddeException(message_id='19002E',
                                 status_code=500,
                                 replace_str_list=[str(e)])

    return identification_information


def history_confirmation_call(
        caddec_resource_id_for_provenance: str,
        direction: str,
        depth: int,
        internal_interface: InternalInterface,
        external_interface: ExternalInterface) -> Response:
    """
    来歴管理I/Fに来歴確認呼び出し処理を依頼する

    Args:
        caddec_resource_id_for_provenance str: 交換実績記録用リソースID
        direction str: 履歴取得方向
        depth int: 検索深度
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : 外部にリクエストを行うインタフェース

    Returns:
        Response : 来歴管理I/Fのレスポンス

    Raises:
        Cadde_excption : コンフィグファイルからprovenance_management_api_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1D002E
        Cadde_excption : レスポンスを正常に取得できなかった場合 エラーコード : 1D003E
        Cadde_excption : 履歴取得方向に不正な値が設定されている場合 エラーコード : 1D004E
        Cadde_excption : 検索深度に不正な値が設定されている場合 エラーコード : 1D005E

    """

    if direction is not None and direction not in __DIRECTION_NORMALITY_VALUES:
        raise CaddeException(message_id='1D004E')

    if depth is not None and bool(depth < __DEPTH_MIN_VALUE):
        raise CaddeException(message_id='1D005E')

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

    send_url = server_url + __URL_HISTORY_LINEAGE + caddec_resource_id_for_provenance + '?'

    if direction is not None:
        send_url = send_url + 'direction=' + direction

    if depth is not None:
        if direction is not None:
            send_url = send_url + '&'
        send_url = send_url + 'depth=' + str(depth)

    response = external_interface.http_get(send_url)
    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='1D002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    if not hasattr(response, 'text') or not response.text:
        raise CaddeException(message_id='1D003E')

    return response


def history_id_search_call(
        body: dict,
        internal_interface: InternalInterface,
        external_interface: ExternalInterface) -> Response:
    """
    来歴管理I/Fに履歴ID検索処理を依頼する

    Args:
        body dict: 履歴ID検索用文字列
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : 外部にリクエストを行うインタフェース

    Returns:
        Response : 来歴管理I/Fのレスポンス

    Raises:
        Cadde_excption : コンフィグファイルからprovenance_management_api_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1E002E
        Cadde_excption : レスポンスを正常に取得できなかった場合 エラーコード : 1E003E

    """
    header_dict = {'Content-Type': 'application/json'}

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

    response = external_interface.http_post(
        server_url + __URL_HISTORY_SEARCHEVENTS, header_dict, body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='1E002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    if not hasattr(response, 'text') or not response.text:
        raise CaddeException(message_id='1E003E')

    return response
