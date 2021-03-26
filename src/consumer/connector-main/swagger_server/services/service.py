# -*- coding: utf-8 -*-
import datetime
import json
import logging
import urllib.parse

from io import BytesIO
from flask import Response

from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.services.provide_data_ngsi import provide_data_ngsi
from swagger_server.services.provide_data_ftp import provide_data_ftp
from swagger_server.services.provide_data_http import provide_data_http

logger = logging.getLogger(__name__)
internal_interface = InternalInterface()

__CONFIG_LOCATION_FILE_PATH = '/usr/src/app/swagger_server/configs/location.json'
__CONFIG_CONNECTOR_FILE_PATH = '/usr/src/app/swagger_server/configs/connector.json'
__CONFIG_CONNECTOR_LOCATION = 'connector_location'
__CONFIG_PROVIDER_DATA_EXCHANGE_URL = 'provider_connector_data_exchange_url'
__CONFIG_PROVIDER_CATALOG_SEARCH_URL = 'provider_connector_catalog_search_url'
__CONFIG_PROVIDER_CONNECTOR_ID = 'provider_connector_id'
__CONFIG_CONTRACT_MANAGEMENT_SERVICE_URL = 'contract_management_service_url'
__CONFIG_CONSUMER_CONNECTOR_ID = 'consumer_connector_id'
__CONFIG_CONSUMER_CONNECTOR_SECRET = 'consumer_connector_secret'
__CONFIG_HISTORY_MANAGEMENT_TOKEN = 'history_management_token'

__CADDEC_CONTRACT_REQUIRED = 'required'
__CADDEC_CONTRACT_NOT_REQUIRED = 'notRequired'

__ACCESS_POINT_URL_SEARCH = 'http://consumer_catalog_search:8080/api/3/action/package_search'
__ACCESS_POINT_URL_FILE = 'http://consumer_data_exchange:8080/cadde/api/v1/file'
__ACCESS_POINT_URL_CERTIFICATION_AUTHORIZATION = 'http://consumer_certification_authorization:8080/token_introspect'
__ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_RECEIVED = 'http://consumer_provenance_management_call:8080/eventwithhash/received'
__ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_LINEAGE = 'http://consumer_provenance_management_call:8080/cadde/api/v1/history/lineage/'
__ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_SEARCHEVENTS = 'http://consumer_provenance_management_call:8080/cadde/api/v1/history/searchevents'


# 履歴取得方向の正常値リスト
__DIRECTION_NORMALITY_VALUES = ['BACKWARD', 'FORWARD', 'BOTH']

# 検索深度の最低値
__DEPTH_MIN_VALUE = -1


def catalog_search(
        query_string: str,
        search: str,
        provider: str,
        authorization: str,
        external_interface: ExternalInterface = ExternalInterface()) -> Response:
    """
    カタログ検索I/Fに、カタログ検索要求を行い、検索結果を返す

    Args:
        query_string str : クエリストリング
        search str : 検索種別
        provider str: 提供者ID
        authorization str: 利用者トークン
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        Response : 取得した情報

    Raises:
        Cadde_excption: 検索種別がdetailかつ、コンフィグファイルからコネクタロケーションが取得できなかった場合 エラーコード: 00002E
        Cadde_excption: カタログ検索I/Fのカタログ検索要求処理の呼び出し時に、エラーが発生した場合 エラーコード: 12002E
        Cadde_excption: 検索種別がdetailかつ、コネクタロケーションから、提供者コネクタURLと契約管理サービスURLが取得できなかった場合 エラーコード: 14003E
        Cadde_excption: 検索種別がmetaもしくはdetailではない場合: 12004E

    """

    if search != 'meta' and search != 'detail':
        raise CaddeException('12004E')

    consumer_connector_id, consumer_connector_secret, history_management_token = __get_connector_config()

    if search == 'detail':

        data_exchange_url, catalog_search_url, provider_connector_id, contract_management_service_url = __get_location_config(
            provider)

        # 契約I/Fのトークンエクスチェンジ 2021年3月版では呼び出しを行わない。

    if search == 'meta':
        catalog_search_url = None

    if authorization is not None:
        token_introspect_headers = {
            'Authorization': authorization,
            'consumer-connector-id': consumer_connector_id,
            'consumer-connector-secret': consumer_connector_secret
        }
        token_introspect_response = external_interface.http_get(
            __ACCESS_POINT_URL_CERTIFICATION_AUTHORIZATION, token_introspect_headers)

        if token_introspect_response.status_code < 200 or 300 <= token_introspect_response.status_code:
            raise CaddeException(
                message_id='19002E',
                status_code=token_introspect_response.status_code,
                replace_str_list=[
                    token_introspect_response.text])

        consumer_id = token_introspect_response.headers['consumer-id']

    # 検索種別がdetailの場合はconnector.jsonからコンフィグ情報の取得と契約状態確認処理を行う。
    # 2021年3月版では上記は実施しない

    headers_dict = {
        'x-cadde-search': search,
        'x-cadde-provider-connector-url': catalog_search_url,
        'Authorization': authorization,
    }

    target_url = __ACCESS_POINT_URL_SEARCH + query_string

    response = external_interface.http_get(target_url, headers_dict)
    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            '12002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    ## ダッシュボードログ
    if authorization is not None:
        dt_now = datetime.datetime.now()
        provider_id = provider if provider is not None and 0 < len(provider) else ''
        log_message = {}
        log_message['log_type'] = 'search'
        log_message['timestamp'] = dt_now.isoformat(timespec='microseconds')
        log_message['consumer_id'] = consumer_id
        log_message['provider_id'] = provider_id
        words = ''
        if 'q=' in query_string:
            words = query_string.split('q=')[1]
            if '&' in words:
                words = words.split('&')[0]
            words = urllib.parse.unquote(words)
        log_message['search_words'] = words
        logger.info(json.dumps(log_message, ensure_ascii=False))

        for data in response.json()['result']['results']:
            fee = ''
            price_range = ''
            for extra in data['extras']:
                if extra['key'] == 'fee':
                    fee = extra['value']
                if extra['key'] == 'pricing_price_range':
                    price_range = extra['value']

            for resource in data['resources']:
                log_message = {}
                log_message['log_type'] = 'browsing'
                log_message['timestamp'] = dt_now.isoformat(timespec='microseconds')
                log_message['consumer_id'] = consumer_id
                log_message['provider_id'] = provider_id
                log_message['search_type'] = search
                log_message['package_id'] = data['id'] if 'id' in data else ''
                log_message['dataset_title'] = data['title'] if 'title' in data else ''
                log_message['resource_name'] = resource['name']
                log_message['resource_type'] = resource['caddec_resource_type'] if 'caddec_resource_type' in resource else ''
                log_message['fee'] = fee
                log_message['price_range'] = price_range
                logger.info(json.dumps(log_message, ensure_ascii=False))

    return response


def fetch_data(resource_url: str,
               resource_api_type: str,
               provider: str,
               contract: bool,
               authorization: str,
               options: dict,
               external_interface: ExternalInterface = ExternalInterface()) -> (BytesIO,
                                                                                dict):
    """
    データ交換I/Fからデータを取得する、もしくはデータ管理から直接データを取得する。

    Args:
        resource_url string : リソースURL
        resource_api_type string : リソース提供手段識別子
        provider string : 提供者ID
        contract string : 契約確認要否
        authorization string : 利用者トークン
        options : dict リクエストヘッダ情報 key:ヘッダ名 value:パラメータ
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        BytesIO :取得データ
        dict: レスポンスヘッダ情報 key:ヘッダ名 value:パラメータ レスポンスヘッダがない場合は空のdictを返す

    Raises:
        Cadde_excption: 提供者IDがNoneでないかつ、コンフィグファイルからコネクタロケーションが取得できなかった場合 エラーコード: 00002E
        Cadde_excption: データ交換I/Fのデータ交換要求の呼び出し時に、エラーが発生した場合 エラーコード: 14002E
        Cadde_excption: リソース提供手段識別子が'api/ngsi', 'file/ftp', 'file/http'以外の場合 エラーコード: 14003E
        Cadde_excption: 提供者IDがNoneでないかつ、コネクタロケーションから、提供者コネクタURLと契約管理サービスURLが取得できなかった場合 エラーコード: 14004E
        Cadde_excption: データ提供IFが使用するカスタムヘッダーの変換に失敗した場合 エラーコード: 14005E
        Cadde_excption: 契約確認要否が'required', 'notRequired'以外の場合 エラーコード: 14006E
        Cadde_excption: 契約確認要否が要に設定されているが、有効な利用者トークンが設定されていない場合 エラーコード: 14007E
        Cadde_excption: 受信履歴登録要求時に利用者IDが空の場合(運用上発生しない想定) エラーコード: 14008E
    """

    if resource_api_type != 'api/ngsi' and resource_api_type != 'file/ftp' and resource_api_type != 'file/http':
        raise CaddeException('14003E')

    if contract != __CADDEC_CONTRACT_REQUIRED and contract != __CADDEC_CONTRACT_NOT_REQUIRED:
        raise CaddeException('14006E')

    consumer_connector_id, consumer_connector_secret, history_management_token = __get_connector_config()

    consumer_id = None

    if authorization is not None:
        token_introspect_headers = {
            'Authorization': authorization,
            'consumer-connector-id': consumer_connector_id,
            'consumer-connector-secret': consumer_connector_secret
        }
        token_introspect_response = external_interface.http_get(
            __ACCESS_POINT_URL_CERTIFICATION_AUTHORIZATION, token_introspect_headers)

        if token_introspect_response.status_code < 200 or 300 <= token_introspect_response.status_code:
            raise CaddeException(
                message_id='19002E',
                status_code=token_introspect_response.status_code,
                replace_str_list=[
                    token_introspect_response.text])

        consumer_id = token_introspect_response.headers['consumer-id']

    response_bytes = None
    response_headers = {'x-cadde-provenance': ''}

    if provider is None:
        if resource_api_type == 'api/ngsi':
            response_bytes, response_headers = provide_data_ngsi(
                resource_url, consumer_id, options)
            response_headers['x-cadde-provenance'] = ''

        elif resource_api_type == 'file/ftp':
            response_bytes = provide_data_ftp(
                resource_url, external_interface, internal_interface)

        elif resource_api_type == 'file/http':
            response_bytes = provide_data_http(
                resource_url, options, external_interface, internal_interface)

        return response_bytes, response_headers

    else:

        data_exchange_url, catalog_search_url, provider_connector_id, contract_management_service_url = __get_location_config(
            provider)

        options_str = ''
        if resource_api_type == 'api/ngsi':
            try:
                options_str = __exchange_options_str(options)
            except Exception:
                raise CaddeException('14005E')

        if contract == __CADDEC_CONTRACT_REQUIRED and authorization is None:
            raise CaddeException('14007E')

        # 契約I/Fの契約状態確認処理 2021年03月版では呼び出しを行わない。

        headers_dict = {
            'x-cadde-resource-url': resource_url,
            'x-cadde-resource-api-type': resource_api_type,
            'x-cadde-provider-connector-url': data_exchange_url,
            'Authorization': authorization,
            'x-cadde-options': options_str
        }
        response = external_interface.http_get(
            __ACCESS_POINT_URL_FILE, headers_dict)
        if response.status_code < 200 or 300 <= response.status_code:
            raise CaddeException(
                '14002E',
                status_code=response.status_code,
                replace_str_list=[
                    response.text])

        response_bytes = BytesIO(response.content)
        response_headers = dict(response.headers)

        # 来歴管理者用トークンは2021年3月版では利用しないため、ダミー値を設定
        if response.headers['x-cadde-provenance'] != '':

            if consumer_id is None:
                raise CaddeException('14008E')

            received_headers = {
                'provider-id': provider_connector_id,
                'consumer-id': consumer_id,
                'caddec-resource-id-for-provenance': response.headers['x-cadde-provenance'],
                'token': 'dummy_token'}
            received_response = external_interface.http_post(
                __ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_RECEIVED, received_headers)

            if received_response.status_code < 200 or 300 <= received_response.status_code:
                raise CaddeException(
                    message_id='19002E',
                    status_code=received_response.status_code,
                    replace_str_list=[
                        received_response.text])

            response_headers['x-cadde-provenance'] = received_response.headers['x-cadde-provenance']

    return response_bytes, response_headers


def history_confirmation_call(
        caddec_resource_id_for_provenance: str,
        direction: str,
        depth: int,
        external_interface: ExternalInterface) -> Response:
    """
    来歴管理I/Fに来歴確認呼び出し処理を依頼する

    Args:
        caddec_resource_id_for_provenance str: 交換実績記録用リソースID
        direction str: 履歴取得方向
        depth str: 検索深度
        external_interface ExternalInterface : 外部にリクエストを行うインタフェース

    Returns:
        Response : 来歴管理呼び出しI/Fのレスポンス

    Raises:
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1B002E
        Cadde_excption : レスポンスを正常に取得できなかった場合 エラーコード : 1B003E
        Cadde_excption : 履歴取得方向に不正な値が設定されている場合 エラーコード : 1B004E
        Cadde_excption : 検索深度に不正な値が設定されている場合 エラーコード : 1B005E

    """

    if direction is not None and direction not in __DIRECTION_NORMALITY_VALUES:
        raise CaddeException(message_id='1B004E')

    if depth is not None and bool(int(depth) < __DEPTH_MIN_VALUE):
        raise CaddeException(message_id='1B005E')

    send_url = __ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_LINEAGE + \
        caddec_resource_id_for_provenance

    headers = {
        'direction': direction,
        'depth': depth
    }

    response = external_interface.http_get(send_url, headers)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='1B002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    if not hasattr(response, 'text') or not response.text:
        raise CaddeException(message_id='1B003E')

    return response


def history_id_search_call(
        body: dict,
        external_interface: ExternalInterface) -> Response:
    """
    来歴管理呼び出しI/Fに履歴ID検索処理を依頼する

    Args:
        body dict: 履歴ID検索用文字列
        external_interface ExternalInterface : 外部にリクエストを行うインタフェース

    Returns:
        Response : 来歴管理呼び出しI/Fのレスポンス

    Raises:
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1C002E
        Cadde_excption : レスポンスを正常に取得できなかった場合 エラーコード : 1C003E

    """
    header_dict = {'content-type': 'application/json'}

    response = external_interface.http_post(
        __ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_SEARCHEVENTS, header_dict, body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='1C002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    if not hasattr(response, 'text') or not response.text:
        raise CaddeException(message_id='1C003E')

    return response


def __exchange_options_str(options_dict: dict) -> str:
    """
    データ提供IFが使用するカスタムヘッダーの辞書型を文字列に変換する。
    変換前: {'key1': 'value1', 'key2': 'value2'}
    変換後: 'key1:value1,key2:value2・・・・'


    Args:
        options_dict dict : データ提供IFが使用するカスタムヘッダーの辞書型

    Returns:
        str:  データ提供IFが使用するカスタムヘッダーの文字列
    """

    return_str = ''

    if not options_dict:
        return return_str

    for key, value in options_dict.items():
        return_str = return_str + key + ':' + value + ','

    return_str = return_str[:-1]

    return return_str


def __get_location_config(provider) -> (str, str, str, str):
    """
    location.jsonからコンフィグ情報を取得し、
    提供者コネクタデータ交換URL、提供者コネクタカタログ検索URL、提供者側コネクタID、契約管理サービスURLを返す。

    Args:
        provider string : 提供者ID

    Returns:
        str: 提供者コネクタデータ交換URL
        str: 提供者コネクタカタログ検索URL
        str: 提供者側コネクタID
        str: 契約管理サービスURL

    Raises:
        Cadde_excption: コンフィグファイルからコネクタロケーションが取得できなかった場合 エラーコード: 00002E
        Cadde_excption: コネクタロケーションから、提供者コネクタURLと契約管理サービスURLが取得できなかった場合 エラーコード: 14004E

    """

    try:
        config = internal_interface.config_read(__CONFIG_LOCATION_FILE_PATH)
        connector_location = config[__CONFIG_CONNECTOR_LOCATION]

    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[__CONFIG_CONNECTOR_LOCATION])
    try:
        provider_info = connector_location[provider]
        provider_data_exchange_url = provider_info[__CONFIG_PROVIDER_DATA_EXCHANGE_URL]
        provider_catalog_search_url = provider_info[__CONFIG_PROVIDER_CATALOG_SEARCH_URL]
        provider_connector_id = provider_info[__CONFIG_PROVIDER_CONNECTOR_ID]
        contract_management_service_url = provider_info[__CONFIG_CONTRACT_MANAGEMENT_SERVICE_URL]
    except Exception:
        raise CaddeException('14004E')

    return provider_data_exchange_url, provider_catalog_search_url, provider_connector_id, contract_management_service_url


def __get_connector_config() -> (str, str, str):
    """
    connector.jsonからコンフィグ情報を取得し、
    利用者側コネクタID、利用者側コネクタのシークレット、来歴管理者用トークンを返す。

    Returns:
        str: 利用者側コネクタID
        str: 利用者側コネクタのシークレット
        str: 来歴管理者用トークン

    Raises:
        Cadde_excption: コンフィグファイルからコネクタロケーションが取得できなかった場合 エラーコード: 00002E

    """
    consumer_connector_id = None
    consumer_connector_secret = None
    history_management_token = None

    try:
        connector = internal_interface.config_read(
            __CONFIG_CONNECTOR_FILE_PATH)
        consumer_connector_id = connector[__CONFIG_CONSUMER_CONNECTOR_ID]
    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[__CONFIG_CONSUMER_CONNECTOR_ID])

    try:
        consumer_connector_secret = connector[__CONFIG_CONSUMER_CONNECTOR_SECRET]
    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[__CONFIG_CONSUMER_CONNECTOR_SECRET])

    try:
        history_management_token = connector[__CONFIG_HISTORY_MANAGEMENT_TOKEN]

    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[__CONFIG_HISTORY_MANAGEMENT_TOKEN])

    return consumer_connector_id, consumer_connector_secret, history_management_token
