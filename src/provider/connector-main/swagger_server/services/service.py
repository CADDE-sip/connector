# -*- coding: utf-8 -*-
import datetime
import json
import logging

from io import BytesIO

from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.services.ckan_access import search_catalog_ckan
from swagger_server.services.provide_data_ngsi import provide_data_ngsi
from swagger_server.services.provide_data_ftp import provide_data_ftp
from swagger_server.services.provide_data_http import provide_data_http

# CKANコンフィグ情報
__CONFIG_CKAN_URL_FILE_PATH = '/usr/src/app/swagger_server/configs/ckan.json'
__CONFIG_RELEASE_CKAN_URL = 'release_ckan_url'
__CONFIG_DETAIL_CKAN_URL = 'detail_ckan_url'

# コネクタコンフィグ情報
__CONFIG_CONNECTOR_FILE_PATH = '/usr/src/app/swagger_server/configs/connector.json'
__CONFIG_PROVIDER_ID = 'provider_id'
__CONFIG_PROVIDER_CONNECTOR_ID = 'provider_connector_id'
__CONFIG_PROVIDER_CONNECTOR_SECRET = 'provider_connector_secret'
__CONFIG_CONTRACT_MANAGEMENT_SERVICE_URL = 'contract_management_service_url'

# CKAN検索用情報
__CKAN_API_PATH = '/api/3/action/package_search'
__CKAN_RESOURCE_SEARCH_PATH = '/api/3/action/resource_search?'
__CKAN_RESOURCE_SEARCH_PROPATY = 'query=url:'

# 接続先URL情報
__ACCESS_POINT_TOKEN_INTROSPECT_URL = 'http://provider-certification-authorization:8080/token_introspect'
__ACCESS_POINT_SENT_URL = 'http://provider-provenance-management-call:8080/eventwithhash/sent'

# 契約確認要否
__CADDEC_CONTRACT = 'caddec_contract_required'
__CADDEC_CONTRACT_REQUIRED = 'required'
__CADDEC_CONTRACT_NOT_REQUIRED = 'notRequired'
__CADDEC_CONTRACT_REQUIRED_NORMAL = [
    __CADDEC_CONTRACT_REQUIRED,
    __CADDEC_CONTRACT_NOT_REQUIRED]

# 交換実績記録用ID
__RESOURCE_ID_FOR_PROVENANCE = 'caddec_resource_id_for_provenance'

logger = logging.getLogger(__name__)

def detail_search(
        query_string: str,
        authorization: str,
        external_interface: ExternalInterface = ExternalInterface(),
        internal_interface: InternalInterface = InternalInterface()) -> str:
    """
    データ管理に、カタログ詳細検索要求を行い、検索結果を返す

    Args:
        query_string str : クエリストリング
        authorization str : 契約トークン
        external_interface : 外部リクエストを行うインタフェース
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        str :検索結果

    Raises:
        Cadde_excption: リクエストに失敗した場合 エラーコード: 07002E

    """

    release_ckan_url, detail_ckan_url = __get_ckan_config(
        False, internal_interface)
    provider_id, provider_connector_id, provider_connector_secret, contract_management_service_url = __get_connector_config(
        internal_interface)

    # 認証認可処理実施
    consumer_id = ''
    if authorization is not None:
        token_introspect_headers = {
            'Authorization': authorization,
            'provider-connector-id': provider_connector_id,
            'provider-connector-secret': provider_connector_secret
        }
        token_introspect_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_INTROSPECT_URL, token_introspect_headers)

        if token_introspect_response.status_code < 200 or 300 <= token_introspect_response.status_code:
            raise CaddeException(message_id='19002E',
                                 status_code=token_introspect_response.status_code,
                                 replace_str_list=[token_introspect_response.text])

        consumer_id = token_introspect_response.headers['consumer-id']

        # 契約状態確認処理(2021年3月版では実施しない)
        # 契約状態確認処理の代わりに2021年3月版では以下を実施する
        if consumer_id == '':
            raise CaddeException(message_id='03003E')

    # 詳細URLに/api/3/action/package_search を追加
    if detail_ckan_url != '' and detail_ckan_url[-1:] == '/':
        detail_ckan_url = detail_ckan_url.rstrip('/')

    detail_ckan_url = detail_ckan_url + __CKAN_API_PATH

    return search_catalog_ckan(
        detail_ckan_url,
        query_string,
        external_interface)


def fetch_data(
        resource_url: str,
        resource_api_type: str,
        authorization: str,
        options: str,
        external_interface: ExternalInterface = ExternalInterface(),
        internal_interface: InternalInterface = InternalInterface()) -> (BytesIO, dict):
    """
    データ管理に、NGSI、FTP、HTTPの取得要求を行い、取得データを返す

    Args:
        resource_url str : リソースURL
        resource_api_type str : リソース提供手段識別子
        authorization str : 契約トークン
        options str : データ提供IFが使用するカスタムヘッダー
        external_interface : 外部リクエストを行うインタフェース
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        BytesIO :取得データ
        dict :ヘッダ情報 ヘッダ情報がない場合は空のdictを返す
    Raises:
        Cadde_excption: リソース提供手段識別子が'api/ngsi', 'file/ftp', 'file/http'以外の場合 エラーコード: 04002E

    """

    release_ckan_url, detail_ckan_url = __get_ckan_config(
        True, internal_interface)
    provider_id, provider_connector_id, provider_connector_secret, contract_management_service_url = __get_connector_config(
        internal_interface)

    consumer_id = None
    # 認証認可処理実施
    if authorization is not None:
        token_introspect_headers = {
            'Authorization': authorization,
            'provider-connector-id': provider_connector_id,
            'provider-connector-secret': provider_connector_secret
        }

        token_introspect_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_INTROSPECT_URL, token_introspect_headers)

        if token_introspect_response.status_code < 200 or 300 <= token_introspect_response.status_code:
            raise CaddeException(
                message_id='19002E',
                status_code=token_introspect_response.status_code,
                replace_str_list=[
                    token_introspect_response.text])

        consumer_id = token_introspect_response.headers['consumer-id']

    # リソースURLから、CKANを逆引き検索して、契約確認要否と交換実績記録用リソースIDを取得
    contract_required, resource_id_for_provenance, dashboard_log_info = __ckan_search_execute(
        release_ckan_url, detail_ckan_url, resource_url, external_interface)

    # 契約確認要 かつ 利用者IDがNoneならエラー
    if contract_required == __CADDEC_CONTRACT_REQUIRED and consumer_id is None:
        raise CaddeException('04014E')

    response_bytes = None
    response_headers = {}
    options_dict = None
    try:
        options_dict = __exchange_options_dict(options)
    except Exception:
        raise CaddeException('04009E')

    if(resource_api_type == 'api/ngsi'):
        response_bytes, response_headers = provide_data_ngsi(
            resource_url, consumer_id, options_dict)

    elif(resource_api_type == 'file/ftp'):
        response_bytes = provide_data_ftp(
            resource_url, external_interface, internal_interface)

    elif(resource_api_type == 'file/http'):
        response_bytes = provide_data_http(
            resource_url, options_dict, external_interface, internal_interface)

    else:
        raise CaddeException('04002E')

    # 交換実績記録用IDがNoneでないかつ、利用者IDがNoneでない場合は、来歴管理呼び出しI/Fの送信履歴登録要求実施
    provenance_id = ''

    # 来歴管理者用トークンは2021年3月版では利用しないため、ダミー値を設定
    if resource_id_for_provenance is not None and consumer_id is not None and resource_api_type != 'api/ngsi':
        sent_headers = {
            'provider-id': provider_id,
            'consumer-id': consumer_id,
            'caddec-resource-id-for-provenance': resource_id_for_provenance,
            'token': 'dummy_token'
        }
        sent_response = external_interface.http_post(
            __ACCESS_POINT_SENT_URL, sent_headers)

        if sent_response.status_code < 200 or 300 <= sent_response.status_code:
            raise CaddeException(
                message_id='19002E',
                status_code=sent_response.status_code,
                replace_str_list=[
                    sent_response.text])

        provenance_id = sent_response.headers['x-cadde-provenance']

    if authorization is not None:
        detail_ckan_url = detail_ckan_url + __CKAN_API_PATH
        query_string = '?q=id:' + dashboard_log_info['package_id']
        package_info_text = search_catalog_ckan(
            detail_ckan_url,
            query_string,
            external_interface)
        fee = ''
        price_range = ''
        package_info = json.loads(package_info_text)
        for extra in package_info['result']['results'][0]['extras']:
            if extra['key'] == 'fee':
                fee = extra['value']
            if extra['key'] == 'pricing_price_range':
                price_range = extra['value']
 
        dt_now = datetime.datetime.now()
        log_message = {}
        log_message['log_type'] = 'providing'
        log_message['timestamp'] = dt_now.isoformat(timespec='microseconds')
        log_message['consumer_id'] = consumer_id
        log_message['provider_id'] = provider_id
        log_message['package_id'] = dashboard_log_info['package_id']
        log_message['resource_id'] = dashboard_log_info['id']
        log_message['resource_name'] = dashboard_log_info['name']
        log_message['fee'] = fee
        log_message['price_range'] = price_range
        logger.info(json.dumps(log_message, ensure_ascii=False))

    response_headers['x-cadde-provenance'] = provenance_id

    return response_bytes, response_headers


def __exchange_options_dict(options_str: str) -> dict:
    """
    データ提供IFが使用するカスタムヘッダーの文字列を辞書型に変換する。
    変換前: "key1:value1,key2:value2・・・・"
    変換後: {'key1': 'value1', 'key2': 'value2'}

    Args:
        options_str str : データ提供IFが使用するカスタムヘッダーの文字列

    Returns:
        dict:  データ提供IFが使用するカスタムヘッダーの辞書型
    """

    return_dict = {}

    if not options_str:
        return return_dict

    options_str_split = options_str.split(',')

    for one_object in options_str_split:
        one_object_split = one_object.split(':')
        return_dict[one_object_split[0]] = one_object_split[1]

    return return_dict


def __get_ckan_config(is_fetch_data, internal_interface) -> (str, str):
    """
    ckan.configから情報を取得して返却する

    Args:
        is_fetch_data bool : Trueの場合はファイル取得処理
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        str: 公開CKANのURL
        str: 詳細CKANのURL

    Raises:
        Cadde_excption: コンフィグから情報が取得できない場合 エラーコード: 00002E
    """

    release_ckan_url = ''

    try:
        ckan_config = internal_interface.config_read(
            __CONFIG_CKAN_URL_FILE_PATH)
        detail_ckan_url = ckan_config[__CONFIG_DETAIL_CKAN_URL]
    except Exception:
        raise CaddeException(message_id='00002E',
                             replace_str_list=[__CONFIG_DETAIL_CKAN_URL])

    if is_fetch_data:
        try:
            release_ckan_url = ckan_config[__CONFIG_RELEASE_CKAN_URL]
        except Exception:
            raise CaddeException(
                message_id='00002E',
                replace_str_list=[__CONFIG_RELEASE_CKAN_URL])

    if detail_ckan_url == '':
        detail_ckan_url = None

    return release_ckan_url, detail_ckan_url


def __get_connector_config(internal_interface) -> (str, str, str, str):
    """
    connector.configから情報を取得して返却する

    Args:
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        str: 提供者ID
        str: 提供者コネクタID
        str: 提供者側コネクタのシークレット
        str: 契約管理サービスURL

    Raises:
        Cadde_excption: コンフィグから情報が取得できない場合 エラーコード: 00002E
    """

    try:
        connector_config = internal_interface.config_read(
            __CONFIG_CONNECTOR_FILE_PATH)
        provider_id = connector_config[__CONFIG_PROVIDER_ID]
    except Exception:
        raise CaddeException(
            message_id='00002E',
            replace_str_list=[__CONFIG_PROVIDER_ID])

    try:
        provider_connector_id = connector_config[__CONFIG_PROVIDER_CONNECTOR_ID]
    except Exception:
        raise CaddeException(message_id='00002E',
                             replace_str_list=[__CONFIG_PROVIDER_CONNECTOR_ID])

    try:
        provider_connector_secret = connector_config[__CONFIG_PROVIDER_CONNECTOR_SECRET]
    except Exception:
        raise CaddeException(message_id='00002E', replace_str_list=[
                             __CONFIG_PROVIDER_CONNECTOR_SECRET])

    try:
        contract_management_service_url = connector_config[__CONFIG_CONTRACT_MANAGEMENT_SERVICE_URL]
    except Exception:
        raise CaddeException(message_id='00002E', replace_str_list=[
                             __CONFIG_CONTRACT_MANAGEMENT_SERVICE_URL])

    return provider_id, provider_connector_id, provider_connector_secret, contract_management_service_url


def __ckan_search_execute(release_ckan_url,
                          detail_ckan_url,
                          resource_url,
                          external_interface) -> (str,
                                                  str):
    """
    公開Ckanと詳細CKANを検索して契約確認要否と、交換実績記録用リソースIDを返却
    Args:
        release_ckan_url str : 公開CKANのURL
        detail_ckan_url: 詳細CKANのURL
        resource_url: リソースURL

    Returns:
        contract_required: 契約確認要否('required' or 'notRequired')
        resource_id_for_provenance: 交換実績記録用ID(str or None)
        dashboard_log_info: ダッシュボード用ログを出力するための情報
    """

    # 公開CKANURL、詳細CKANURLの末尾に検索用文字列を設定
    if release_ckan_url[-1:] == '/':
        release_ckan_url = release_ckan_url.rstrip('/')

    release_ckan_url = release_ckan_url + __CKAN_RESOURCE_SEARCH_PATH

    if detail_ckan_url is not None:
        if detail_ckan_url[-1:] == '/':
            detail_ckan_url = detail_ckan_url.rstrip('/')

        detail_ckan_url = detail_ckan_url + __CKAN_RESOURCE_SEARCH_PATH

    query_string = __CKAN_RESOURCE_SEARCH_PROPATY + resource_url

    release_ckan_text = search_catalog_ckan(
        release_ckan_url, query_string, external_interface)
    release_search_results_list = json.loads(release_ckan_text)[
        'result']['results']

    detail_search_results_list = []

    if detail_ckan_url is not None:
        detail_ckan_text = search_catalog_ckan(
            detail_ckan_url, query_string, external_interface)
        detail_search_results_list = json.loads(
            detail_ckan_text)['result']['results']

    ckan_chack_result_list = __ckan_result_chack(
        release_search_results_list,
        detail_search_results_list,
        resource_url)

    contract_required = None
    resource_id_for_provenance = None

    for one_data in ckan_chack_result_list:
        if contract_required is None:
            contract_required = one_data[__CADDEC_CONTRACT]

        if resource_id_for_provenance is None and one_data[__RESOURCE_ID_FOR_PROVENANCE] != '':
            resource_id_for_provenance = one_data[__RESOURCE_ID_FOR_PROVENANCE]

        if contract_required != one_data[__CADDEC_CONTRACT]:
            raise CaddeException(message_id='04011E')

        if one_data[__RESOURCE_ID_FOR_PROVENANCE] != '' and resource_id_for_provenance != one_data[__RESOURCE_ID_FOR_PROVENANCE]:
            raise CaddeException(message_id='04013E')

    return contract_required, resource_id_for_provenance, detail_search_results_list[-1]


def __ckan_result_chack(
        release_search_results_list,
        detail_search_results_list,
        resource_url) -> list:
    """
    公開CKANと詳細CKANの検索結果を確認する。
    Args:
        release_search_results_list str : 公開CKANの検索結果
        detail_search_results_list: 詳細CKANの検索結果
        resource_url: リソースURL

    Returns:
        検索結果のリスト [{'caddec_contract_required': 契約確認要否, 'resource_id_for_provenance': 交換実績記録用ID}.... ]
    """

    # 横断CKAN の整形結果取得
    return_list = __single_ckan_result_molding(
        release_search_results_list, resource_url)

    # 詳細CKAN の整形結果取得
    if detail_search_results_list is not None:
        return_list.extend(
            __single_ckan_result_molding(
                detail_search_results_list,
                resource_url))

    # 検索結果が1件もない場合はエラー
    if len(return_list) == 0:
        raise CaddeException(message_id='04010E')

    return return_list


def __single_ckan_result_molding(ckan_results_list, resource_url) -> dict:
    """
    CKANの検索結果を成型する。
    Args:
        ckan_results_list list[dict] : CKANの検索結果
        resource_url: リソースURL

    Returns:
        検索結果のリスト [{'caddec_contract_required': 契約確認要否, 'resource_id_for_provenance': 交換実績記録用ID}.... ]
    """

    return_list = []

    for one_data in ckan_results_list:
        add_dict = {}

        if one_data['url'] != resource_url:
            continue

        # 契約確認要否の設定
        if __CADDEC_CONTRACT in one_data:

            if one_data[__CADDEC_CONTRACT] not in __CADDEC_CONTRACT_REQUIRED_NORMAL:
                raise CaddeException(message_id='04012E')
            add_dict[__CADDEC_CONTRACT] = one_data[__CADDEC_CONTRACT]
        else:
            add_dict[__CADDEC_CONTRACT] = __CADDEC_CONTRACT_NOT_REQUIRED

        # 交換実績記録用IDの設定
        if __RESOURCE_ID_FOR_PROVENANCE in one_data and one_data[__RESOURCE_ID_FOR_PROVENANCE] != '':
            add_dict[__RESOURCE_ID_FOR_PROVENANCE] = one_data[__RESOURCE_ID_FOR_PROVENANCE]
        else:
            add_dict[__RESOURCE_ID_FOR_PROVENANCE] = ''

        return_list.append(add_dict)

    return return_list
