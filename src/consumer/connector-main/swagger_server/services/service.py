# -*- coding: utf-8 -*-
from io import BytesIO

from flask import Response

from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.services.provide_data_ngsi import provide_data_ngsi
from swagger_server.services.provide_data_ftp import provide_data_ftp
from swagger_server.services.provide_data_http import provide_data_http

internal_interface = InternalInterface()

__CONFIG_LOCATION_FILE_PATH = '/usr/src/app/swagger_server/configs/location.json'
__CONFIG_CONNECTOR_LOCATION = 'connector_location'
__CONFIG_PROVIDER_DATA_EXCHANGE_URL = 'provider_connector_data_exchange_url'
__CONFIG_PROVIDER_CATALOG_SEARCH_URL = 'provider_connector_catalog_search_url'
__CONFIG_CONTRACT_MANAGEMENT_SERVICE_URL = 'contract_management_service_url'

__ACCESS_POINT_URL_SEARCH = 'http://consumer_catalog_search:8080/api/3/action/package_search'
__ACCESS_POINT_URL_FILE = 'http://consumer_data_exchange:8080/cadde/api/v1/file'

__HTTP_STATUS_CODE_SUCCESS_LOWER_LIMIT = 200
__HTTP_STATUS_CODE_SUCCESS_UPPER_LIMIT = 299


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
        Cadde_excption: 検索種別がdetailかつ、コネクタロケーションから、提供者コネクタURLと契約管理サービスURLが取得できなかった場合 エラーコード: 12003E

    """
    # 利用者コネクタ認証

    user_id = None
    provider_connector_url = None
    contract_management_service_url = None
    contract_token = None

    if search == 'detail':

        data_exchange_url, catalog_search_url, contract_management_service_url = __get_location_config(
            provider)

        # 契約I/Fの契約状態確認_検索 2020年09月版では呼び出しを行わない。

    if search == 'meta':
        catalog_search_url = None
        contract_token = None

    headers_dict = {
        'x-cadde-search': search,
        'x-cadde-provider-connector-url': catalog_search_url,
        'Authorization': contract_token,
    }

    target_url = __ACCESS_POINT_URL_SEARCH + query_string

    response = external_interface.http_get(target_url, headers_dict)
    if response.status_code < __HTTP_STATUS_CODE_SUCCESS_LOWER_LIMIT or __HTTP_STATUS_CODE_SUCCESS_UPPER_LIMIT < response.status_code:
        raise CaddeException(
            '14002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

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
    """

    if resource_api_type != 'api/ngsi' and resource_api_type != 'file/ftp' and resource_api_type != 'file/http':
        raise CaddeException('14003E')

    if contract != 'required' and contract != 'notRequired':
        raise CaddeException('14006E')

    # 利用者コネクタ認証

    response_bytes = None
    response_headers = {}

    if provider is None:
        if resource_api_type == 'api/ngsi':
            response_bytes, response_headers = provide_data_ngsi(
                resource_url, None, options)

        elif resource_api_type == 'file/ftp':
            response_bytes = provide_data_ftp(
                resource_url, external_interface, internal_interface)

        elif resource_api_type == 'file/http':
            response_bytes = provide_data_http(
                resource_url, options, external_interface, internal_interface)

    else:
        provider_connector_url = None
        contract_management_service_url = None

        # 契約I/Fの契約状態確認_検索 2020年09月版では呼び出しを行わない。
        user_id = 'dummy'

        data_exchange_url, catalog_search_url, contract_management_service_url = __get_location_config(
            provider)

        options_str = ''
        if resource_api_type == 'api/ngsi':
            try:
                options_str = __exchange_options_str(options)
            except Exception:
                raise CaddeException('14005E')

        headers_dict = {
            'x-cadde-resource-url': resource_url,
            'x-cadde-resource-api-type': resource_api_type,
            'x-cadde-provider-connector-url': data_exchange_url,
            'Authorization': authorization,
            'x-cadde-options': options_str
        }
        response = external_interface.http_get(
            __ACCESS_POINT_URL_FILE, headers_dict)
        if response.status_code < __HTTP_STATUS_CODE_SUCCESS_LOWER_LIMIT or __HTTP_STATUS_CODE_SUCCESS_UPPER_LIMIT < response.status_code:
            raise CaddeException(
                '14002E',
                status_code=response.status_code,
                replace_str_list=[
                    response.text])

        response_bytes = BytesIO(response.content)
        response_headers = dict(response.headers)

    return response_bytes, response_headers


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


def __get_location_config(provider: str) -> (str, str):
    """
    location.jsonからコンフィグ情報を取得し、
    提供者コネクタURL、契約管理サービスURLを返す。

    Args:
        provider string : 提供者ID

    Returns:
        str: 提供者コネクタデータ交換URL
        str: 提供者コネクタカタログ検索URL
        str: 契約管理サービスURL

    Raises:
        Cadde_excption: コンフィグファイルからコネクタロケーションが取得できなかった場合 エラーコード: 00002E
        Cadde_excption: コネクタロケーションから、提供者コネクタURLと契約管理サービスURLが取得できなかった場合 エラーコード: 14004E

    """

    provider_connector_url = None
    contract_management_service_url = None

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
        contract_management_service_url = provider_info[__CONFIG_CONTRACT_MANAGEMENT_SERVICE_URL]

    except Exception:
        raise CaddeException('14004E')

    return provider_data_exchange_url, provider_catalog_search_url, contract_management_service_url
