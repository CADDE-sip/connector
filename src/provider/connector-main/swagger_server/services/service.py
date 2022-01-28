# -*- coding: utf-8 -*-
import datetime
import json
import logging
import hashlib
import urllib

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

__CONFIG_HTTP_FILE_PATH = '/usr/src/app/swagger_server/configs/http.json'
__CONFIG_FTP_FILE_PATH = '/usr/src/app/swagger_server/configs/ftp.json'
__CONFIG_NGSI_FILE_PATH = '/usr/src/app/swagger_server/configs/ngsi.json'


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
__ACCESS_POINT_TOKEN_INTROSPECT_URL = 'http://provider_authentication_authorization:8080/token_introspect'
__ACCESS_POINT_TOKEN_FEDERATION_URL = 'http://provider_authentication_authorization:8080/token_federation'
__ACCESS_POINT_TOKEN_PAT_REQ_URL = 'http://provider_authentication_authorization:8080/token_req_pat'
__ACCESS_POINT_TOKEN_RESOURCE_URL = 'http://provider_authentication_authorization:8080/token_resource'
__ACCESS_POINT_TOKEN_CONTRACT_URL = 'http://provider_authentication_authorization:8080/token_contract'
__ACCESS_POINT_TOKEN_RESOURCE_INFO_URL = 'http://provider_authentication_authorization:8080/token_resource_info'
__ACCESS_POINT_SENT_URL = 'http://provider_provenance_management:8080/eventwithhash/sent'
__ACCESS_POINT_VOUCHER_URL = 'http://provider_provenance_management:8080/voucher/sent'

# 交換実績記録用ID
__RESOURCE_ID_FOR_PROVENANCE = 'caddec_resource_id_for_provenance'

# HTTPコンフィグ
__HTTP_BASIC_AUTH = 'basic_auth'
__HTTP_HTTP_DOMAIN = 'domain'
__HTTP_BASIC_AUTH_ENABLE = 'authorization'

# FTPコンフィグ
__FTP_KEY_FTP_AUTH = 'ftp_auth'
__FTP_KEY_FTP_DOMAIN = 'domain'
__FTP_KEY_FTP_AUTH_ENABLE = 'authorization'

# NGSIコンフィグ
__NGSI_KEY_NGSI_AUTH = 'ngsi_auth'
__NGSI_KEY_NGSI_DOMAIN = 'domain'
__NGSI_KEY_NGSI_AUTH_ENABLE = 'authorization'

__URL_SPLIT_CHAR = '/'

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
        authorization str : 認証トークン
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
        # トークン連携(認可トークン取得)
        token_federation_headers = {
            'Authorization': authorization,
            'x-provider-connector-id': provider_connector_id,
            'x-provider-connector-secret': provider_connector_secret
        }
        token_federation_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_FEDERATION_URL, token_federation_headers)

        if token_federation_response.status_code < 200 or 300 <= token_federation_response.status_code:
            raise CaddeException(
                message_id='1A004N',
                status_code=token_federation_response.status_code,
                replace_str_list=[
                    token_federation_response.text])

        auth_token = token_federation_response.headers['auth-token']

        # 認可トークン検証
        token_introspect_headers = {
            'Authorization': auth_token,
            'x-provider-connector-id': provider_connector_id,
            'x-provider-connector-secret': provider_connector_secret
        }
        token_introspect_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_INTROSPECT_URL, token_introspect_headers)

        if token_introspect_response.status_code < 200 or 300 <= token_introspect_response.status_code:
            raise CaddeException(message_id='03003E',
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
        authorization str : 認証トークン
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
    contract_id = ''
    contract_check_enable = __get_contract_check_enable(resource_url, resource_api_type, internal_interface)
    # 認証認可処理実施
    if authorization is not None:
        # トークン連携(認可トークン取得)
        token_federation_headers = {
            'Authorization': authorization,
            'x-provider-connector-id': provider_connector_id,
            'x-provider-connector-secret': provider_connector_secret
        }
        token_federation_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_FEDERATION_URL, token_federation_headers)

        if token_federation_response.status_code < 200 or 300 <= token_federation_response.status_code:
            raise CaddeException(
                message_id='04014E',
                status_code=token_federation_response.status_code,
                replace_str_list=[
                    token_federation_response.text])

        auth_token = token_federation_response.headers['auth-token']

        # 認可トークン検証
        token_introspect_headers = {
            'Authorization': auth_token,
            'x-provider-connector-id': provider_connector_id,
            'x-provider-connector-secret': provider_connector_secret
        }

        token_introspect_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_INTROSPECT_URL, token_introspect_headers)

        if token_introspect_response.status_code < 200 or 300 <= token_introspect_response.status_code:
            raise CaddeException(
                message_id='04014E',
                status_code=token_introspect_response.status_code,
                replace_str_list=[
                    token_introspect_response.text])

        consumer_id = token_introspect_response.headers['consumer-id']

        # リソースURLのドメインが認可確認有ならば、認可確認を行う
        if contract_check_enable:

            # APIトークン取得
            token_pat_req_headers = {
                'x-provider-connector-id': provider_connector_id,
                'x-provider-connector-secret': provider_connector_secret
            }

            token_pat_req_response = external_interface.http_get(
                __ACCESS_POINT_TOKEN_PAT_REQ_URL, token_pat_req_headers)

            if token_pat_req_response.status_code < 200 or 300 <= token_pat_req_response.status_code:
                raise CaddeException(
                    message_id='04015E',
                    status_code=token_pat_req_response.status_code,
                    replace_str_list=[
                        token_pat_req_response.text])

            api_token = token_pat_req_response.headers['api-token']

            # リソースID取得
            token_resource_headers = {
                'Authorization': api_token,
                'x-resource-url': resource_url
            }

            token_resource_response = external_interface.http_get(
                __ACCESS_POINT_TOKEN_RESOURCE_URL, token_resource_headers)

            if token_resource_response.status_code < 200 or 300 <= token_resource_response.status_code:
                raise CaddeException(
                    message_id='04016E',
                    status_code=token_resource_response.status_code,
                    replace_str_list=[
                        token_resource_response.text])

            resource_id = token_resource_response.headers['resource-id']

            # 認可チェック
            token_contract_headers = {
                'Authorization': auth_token,
                'x-resource-id': resource_id,
                'x-provider-connector-id': provider_connector_id
            }

            token_contract_response = external_interface.http_get(
                __ACCESS_POINT_TOKEN_CONTRACT_URL, token_contract_headers)

            if token_contract_response.status_code < 200 or 300 <= token_contract_response.status_code:
                raise CaddeException(
                    message_id='04017E',
                    status_code=token_contract_response.status_code,
                    replace_str_list=[
                        token_contract_response.text])

    response_bytes = None
    response_headers = {}
    options_dict = None
    try:
        options_dict = __exchange_options_dict(options)
    except Exception:
        raise CaddeException('04009E')

    # リソースURLから、CKANを逆引き検索して、契約確認要否と交換実績記録用リソースIDを取得
    resource_id_for_provenance, dashboard_log_info = __ckan_search_execute(
        release_ckan_url, detail_ckan_url, resource_url, resource_api_type, options_dict, external_interface)

    if(resource_api_type == 'api/ngsi'):
        response_bytes, response_headers = provide_data_ngsi(
            resource_url, options_dict)

    elif(resource_api_type == 'file/ftp'):
        response_bytes = provide_data_ftp(
            resource_url, external_interface, internal_interface)

    elif(resource_api_type == 'file/http'):
        response_bytes = provide_data_http(
            resource_url, options_dict, external_interface, internal_interface)

    else:
        raise CaddeException('04002E')

    response_data = response_bytes.read()
    response_bytes.seek(0)

    # リソースURLのドメインが認可確認有の場合、データ証憑通知（送信）
    if contract_check_enable:
        # ハッシュ値算出
        hash_value = hashlib.sha512(response_data).hexdigest()

        # 取引ID取得
        token_resource_info_headers = {
            'Authorization': api_token,
            'x-resource-id': resource_id
        }

        token_resource_response_info = external_interface.http_get(
            __ACCESS_POINT_TOKEN_RESOURCE_INFO_URL, token_resource_info_headers)

        if token_resource_response_info.status_code < 200 or 300 <= token_resource_response_info.status_code:
            raise CaddeException(
                message_id='04018E',
                status_code=token_resource_response_info.status_code,
                replace_str_list=[
                    token_resource_response_info.text])

        if 'attributes' not in token_resource_response_info.headers:
            raise CaddeException(
                message_id='04019E',
                status_code=token_resource_response_info.status_code,
                replace_str_list=['attributes'])

        attributes = eval(token_resource_response_info.headers['attributes'])

        # attributeに取引IDが設定されている場合、契約有のデータとしてデータ証憑通知を行う
        if 'contract_id' in attributes:
            contract_id = attributes['contract_id'][0]

            # データ証憑通知（送信）
            sent_headers = {
                'x-cadde-provider': provider_id,
                'x-cadde-consumer': consumer_id,
                'x-cadde-contract-id': contract_id,
                'x-hash-get-data': hash_value,
                'x-cadde-contract-management-url': contract_management_service_url
            }
            sent_response = external_interface.http_post(
                __ACCESS_POINT_VOUCHER_URL, sent_headers)

            if sent_response.status_code < 200 or 300 <= sent_response.status_code:
                raise CaddeException(
                    message_id='04021E',
                    status_code=sent_response.status_code,
                    replace_str_list=[
                        sent_response.text])

    # 交換実績記録用IDがNoneでないかつ、利用者IDがNoneでない場合は、来歴管理I/Fの送信履歴登録要求実施
    provenance_id = ''

    # 来歴管理者用トークンは2022年3月版では利用しないため、ダミー値を設定
    if resource_id_for_provenance is not None and consumer_id is not None:
        sent_headers = {
            'x-cadde-provider': provider_id,
            'x-cadde-consumer': consumer_id,
            'x-caddec-resource-id-for-provenance': resource_id_for_provenance,
            'x-token': 'dummy_token'
        }
        sent_response = external_interface.http_post(
            __ACCESS_POINT_SENT_URL, sent_headers)

        if sent_response.status_code < 200 or 300 <= sent_response.status_code:
            raise CaddeException(
                message_id='04022E',
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
    response_headers['x-cadde-contract-id'] = contract_id

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

def __get_contract_check_enable(resource_url,
                                resource_api_type,
                                internal_interface) -> str:
    """
    リソースURLのドメインからhttp.json、ftp.json、ngsi.jsonを検索して、契約確認の有無を返却
    Args:
        resource_url str : リソースURL
        resource_api_type str : リソース提供手段識別子
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        enable: 契約確認有無(True or False)
    """

    domain = resource_url.split(__URL_SPLIT_CHAR)[2]
    enable = False
    if(resource_api_type == 'api/ngsi'):
        ngsi_auth_domain = []
        try:
            ngsi_config = internal_interface.config_read(__CONFIG_NGSI_FILE_PATH)
            ngsi_auth_domain = [e for e in ngsi_config[__NGSI_KEY_NGSI_AUTH] if e[__NGSI_KEY_NGSI_DOMAIN] == domain]
        except Exception:
            # コンフィグファイルから指定したドメインの情報が取得できない場合は何もしない
            pass
        if ngsi_auth_domain:
            if __NGSI_KEY_NGSI_AUTH_ENABLE not in ngsi_auth_domain[0]:
                raise CaddeException(
                    '00002E',
                    status_code=None,
                    replace_str_list=[__NGSI_KEY_NGSI_AUTH_ENABLE])

            if ngsi_auth_domain[0][__NGSI_KEY_NGSI_AUTH_ENABLE] == 'enable':
                enable = True
    elif(resource_api_type == 'file/ftp'):
        try:
            ftp_config = internal_interface.config_read(__CONFIG_FTP_FILE_PATH)
            ftp_auth_domain = [e for e in ftp_config[__FTP_KEY_FTP_AUTH] if e[__FTP_KEY_FTP_DOMAIN] == domain]
        except Exception:
            # コンフィグファイルから指定したドメインの情報が取得できない場合は何もしない
            pass

        if ftp_auth_domain:
            if __FTP_KEY_FTP_AUTH_ENABLE not in ftp_auth_domain[0]:
                raise CaddeException(
                    '00002E',
                    status_code=None,
                    replace_str_list=[__FTP_KEY_FTP_AUTH_ENABLE])

            if ftp_auth_domain[0][__FTP_KEY_FTP_AUTH_ENABLE] == 'enable':
                enable = True

    elif(resource_api_type == 'file/http'):
        try:
            http_config = internal_interface.config_read(__CONFIG_HTTP_FILE_PATH)
            http_config_domain = [e for e in http_config[__HTTP_BASIC_AUTH] if e[__HTTP_HTTP_DOMAIN] == domain]

        except Exception:
            # コンフィグファイルから指定したドメインの情報が取得できない場合は何もしない
            pass

        if http_config_domain:
            if __HTTP_BASIC_AUTH_ENABLE not in http_config_domain[0]:
                raise CaddeException(
                    '00002E',
                    status_code=None,
                    replace_str_list=[__HTTP_BASIC_AUTH_ENABLE])

            if http_config_domain[0][__HTTP_BASIC_AUTH_ENABLE] == 'enable':
                enable = True
    else:
        raise CaddeException('04002E')

    return enable

def __ckan_search_execute(release_ckan_url,
                          detail_ckan_url,
                          resource_url,
                          resource_api_type,
                          options_dict, 
                          external_interface) -> (str,
                                                  str):
    """
    公開Ckanと詳細CKANを検索して契約確認要否と、交換実績記録用リソースIDを返却
    Args:
        release_ckan_url str : 公開CKANのURL
        detail_ckan_url: 詳細CKANのURL
        resource_url: リソースURL

    Returns:
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

    if resource_api_type == 'api/ngsi':
        # /entitiesまでをクエリとすることで、候補となるURL（/entities?type=hogeや /entities/entity1など）を
        # すべて対象とする。
        query_url = resource_url.split('entities')[0]+'entities'
        query_string = __CKAN_RESOURCE_SEARCH_PROPATY + query_url
    else:
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

    ckan_check_result_list = __ckan_result_check(
        release_search_results_list,
        detail_search_results_list,
        resource_url,
        resource_api_type,
        options_dict)

    resource_id_for_provenance = None

    for one_data in ckan_check_result_list:
        if resource_id_for_provenance is None and one_data[__RESOURCE_ID_FOR_PROVENANCE] != '':
            resource_id_for_provenance = one_data[__RESOURCE_ID_FOR_PROVENANCE]

        if one_data[__RESOURCE_ID_FOR_PROVENANCE] != '' and resource_id_for_provenance != one_data[__RESOURCE_ID_FOR_PROVENANCE]:
            raise CaddeException(message_id='04013E')

    dashboard_log_info = None
    if 0 < len(detail_search_results_list):
        dashboard_log_info = detail_search_results_list[-1]
    else:
        dashboard_log_info = release_search_results_list[-1]
    return resource_id_for_provenance, dashboard_log_info


def __ckan_result_check(
        release_search_results_list,
        detail_search_results_list,
        resource_url, 
        resource_api_type,
        options_dict) -> list:
    """
    公開CKANと詳細CKANの検索結果を確認する。
    Args:
        release_search_results_list str : 公開CKANの検索結果
        detail_search_results_list: 詳細CKANの検索結果
        resource_url: リソースURL

    Returns:
        検索結果のリスト [{'resource_id_for_provenance': 交換実績記録用ID}.... ]
    """

    # 横断CKAN の整形結果取得
    return_list = __single_ckan_result_molding(
        release_search_results_list, resource_url, resource_api_type, options_dict)

    # 詳細CKAN の整形結果取得
    if detail_search_results_list is not None:
        return_list.extend(
            __single_ckan_result_molding(
                detail_search_results_list,
                resource_url, resource_api_type, options_dict))

    # 検索結果が1件もない場合はエラー
    if len(return_list) == 0:
        raise CaddeException(message_id='04010E')

    return return_list


def __single_ckan_result_molding(ckan_results_list, resource_url, resource_api_type, options_dict) -> dict:
    """
    CKANの検索結果を成型する。
    Args:
        ckan_results_list list[dict] : CKANの検索結果
        resource_url: リソースURL

    Returns:
        検索結果のリスト [{'resource_id_for_provenance': 交換実績記録用ID}.... ]
    """

    return_list = []

    for one_data in ckan_results_list:
        add_dict = {}

        if resource_api_type == 'api/ngsi':
            access_url = resource_url.split('entities')[0]+'entities'
            
            parse_url = urllib.parse.urlparse(resource_url)
            query = urllib.parse.parse_qs(parse_url.query)
            
            # typeクエリは必ず指定される。
            ngsi_type = query['type'][0]
            ngsi_tenant = ""
            ngsi_service_path = ""
            
            for key in options_dict:
                if 'fiware-service' == key.lower(): 
                    ngsi_tenant = options_dict[key].strip()
                if 'fiware-servicepath' == key.lower(): 
                    ngsi_service_path = options_dict[key].strip()
            
            # NGSIテナント、サービスパスの確認。指定しないケースを考慮する。
            ckan_ngsi_tenant = ""
            ckan_ngsi_service_path = ""
            if 'ngsi_tenant' in one_data.keys(): 
                ckan_ngsi_tenant = one_data['ngsi_tenant'] 
            if 'ngsi_service_path' in one_data.keys(): 
                ckan_ngsi_service_path = one_data['ngsi_service_path'] 
            
            if ckan_ngsi_tenant != ngsi_tenant or ckan_ngsi_service_path != ngsi_service_path:
                continue
            
            # NGSIデータ種別の確認。
            if 'ngsi_entity_type' not in one_data.keys() or one_data['ngsi_entity_type'] != ngsi_type:
                continue
            
            # URL確認
            if one_data['url'] not in access_url:
                continue

        else:
            if one_data['url'] != resource_url:
                continue

        # 交換実績記録用IDの設定
        if __RESOURCE_ID_FOR_PROVENANCE in one_data and one_data[__RESOURCE_ID_FOR_PROVENANCE] != '':
            add_dict[__RESOURCE_ID_FOR_PROVENANCE] = one_data[__RESOURCE_ID_FOR_PROVENANCE]
        else:
            add_dict[__RESOURCE_ID_FOR_PROVENANCE] = ''

        return_list.append(add_dict)

    return return_list
