# -*- coding: utf-8 -*-
import datetime
import json
import logging
import hashlib
import urllib
from io import BytesIO
from urllib.parse import quote

from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.services.ckan_access import search_catalog_ckan
from swagger_server.services.provide_data_ngsi import provide_data_ngsi
from swagger_server.services.provide_data_ftp import provide_data_ftp
from swagger_server.services.provide_data_http import provide_data_http

# CKANコンフィグ情報
__CONFIG_CKAN_URL_FILE_PATH = '/usr/src/app/swagger_server/configs/provider_ckan.json'
__CONFIG_RELEASE_CKAN_URL = 'release_ckan_url'
__CONFIG_DETAIL_CKAN_URL = 'detail_ckan_url'
__CONFIG_CKAN_AUTHORIZATION = 'authorization'

# ngsi/ftp/httpコンフィグ情報
__CONFIG_HTTP_FILE_PATH = '/usr/src/app/swagger_server/configs/http.json'
__CONFIG_FTP_FILE_PATH = '/usr/src/app/swagger_server/configs/ftp.json'
__CONFIG_NGSI_FILE_PATH = '/usr/src/app/swagger_server/configs/ngsi.json'


# コネクタコンフィグ情報
__CONFIG_CONNECTOR_FILE_PATH = '/usr/src/app/swagger_server/configs/connector.json'
__CONFIG_PROVIDER_ID = 'provider_id'
__CONFIG_PROVIDER_CONNECTOR_ID = 'provider_connector_id'
__CONFIG_PROVIDER_CONNECTOR_SECRET = 'provider_connector_secret'
__CONFIG_TRACE_LOG_ENABLE = 'trace_log_enable'

# コンフィグ：認可確認
__COMMON_KEY_AUTH_TARGET = 'authorization'
__COMMON_KEY_AUTH_URL = 'url'
__COMMON_KEY_AUTH_ENABLE = 'enable'

# コンフィグ：取引市場利用制御
__COMMON_KEY_CONTRACT_TARGET = 'contract_management_service'
__COMMON_KEY_CONTRACT_URL = 'url'
__COMMON_KEY_CONTRACT_ENABLE = 'enable'

# CKAN検索用情報
__CKAN_API_PATH = '/api/3/action/package_search'
__CKAN_RESOURCE_SEARCH_PATH = '/api/3/action/resource_search?'
__CKAN_RESOURCE_SEARCH_PROPATY = 'query=url:'

# 接続先URL情報
__ACCESS_POINT_TOKEN_INTROSPECT_URL = 'http://provider_authorization:8080/token_introspect'
__ACCESS_POINT_TOKEN_FEDERATION_URL = 'http://provider_authorization:8080/token_federation'
__ACCESS_POINT_TOKEN_CONTRACT_URL = 'http://provider_authorization:8080/token_contract'
__ACCESS_POINT_SENT_URL = 'http://provider_provenance_management:8080/eventwithhash/sent'
__ACCESS_POINT_VOUCHER_URL = 'http://provider_provenance_management:8080/voucher/sent'

# 交換実績記録用ID
__RESOURCE_ID_FOR_PROVENANCE = 'cadde_resource_id_for_provenance'


__URL_SPLIT_CHAR = '/'

logger = logging.getLogger(__name__)


def detail_search(
        query_string: str,
        authorization: str,
        external_interface: ExternalInterface = ExternalInterface(),
        internal_interface: InternalInterface = InternalInterface()) -> str:
    """
    データ管理に、カタログ詳細検索を行い、検索結果を返す

    Args:
        query_string str : クエリストリング
        authorization str : 認証トークン
        external_interface : 外部リクエストを行うインタフェース
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        str :検索結果

    Raises:
        Cadde_excption: 認可トークン取得時にエラーが発生した場合               エラーコード: 010001002E
        Cadde_excption: 認可トークン検証時にエラーが発生した場合               エラーコード: 010001003E
        Cadde_excption: 認可トークンからCADDEユーザIDが取得できなかった場合    エラーコード: 010001004E
        Cadde_excption: 認可確認の制御値と認証トークン有無に不整合があった場合 エラーコード: 010001005E
        Cadde_excption: 認可確認時にエラーが発生した場合                       エラーコード: 010001006E

    """

    release_ckan_url, detail_ckan_url, ckan_authorization = __get_ckan_config(
        internal_interface)
    provider_id, provider_connector_id, provider_connector_secret, trace_log_enable = __get_connector_config(
        internal_interface)

    consumer_id = ''

    # 認可処理
    if authorization:
        # トークン連携(認可トークン取得)
        token_federation_headers = {
            'Authorization': authorization,
            'x-cadde-provider': provider_id,
            'x-cadde-provider-connector-id': provider_connector_id,
            'x-cadde-provider-connector-secret': provider_connector_secret
        }
        token_federation_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_FEDERATION_URL, token_federation_headers)

        if token_federation_response.status_code < 200 or 300 <= token_federation_response.status_code:
            raise CaddeException(
                message_id='010001002E',
                status_code=token_federation_response.status_code,
                replace_str_list=[
                    token_federation_response.text])

        get_token = token_federation_response.headers['x-cadde-auth-token']
        auth_token = f'Bearer {get_token}'

        # 認可トークン検証
        token_introspect_headers = {
            'Authorization': auth_token,
            'x-cadde-provider': provider_id,
            'x-cadde-provider-connector-id': provider_connector_id,
            'x-cadde-provider-connector-secret': provider_connector_secret
        }
        token_introspect_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_INTROSPECT_URL, token_introspect_headers)

        if token_introspect_response.status_code < 200 or 300 <= token_introspect_response.status_code:
            raise CaddeException(message_id='010001003E',
                                 status_code=token_introspect_response.status_code,
                                 replace_str_list=[token_introspect_response.text])

        consumer_id = token_introspect_response.headers['x-cadde-consumer-id']

        if consumer_id == '':
            raise CaddeException(
                message_id='010001004E',
                replace_str_list=[
                    token_introspect_response.text])

    # 対象のリソースURLが認可確認有ならば、認可確認を行う
    if ckan_authorization:
        # 設定値との整合性確認
        if not authorization:
            raise CaddeException('010001005E')

        # 認可確認
        token_contract_headers = {
            'Authorization': auth_token,
            'x-cadde-provider': provider_id,
            'x-cadde-provider-connector-id': provider_connector_id,
            'x-cadde-provider-connector-secret': provider_connector_secret,
            'x-cadde-resource-url': detail_ckan_url
        }

        token_contract_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_CONTRACT_URL, token_contract_headers)

        if token_contract_response.status_code < 200 or 300 <= token_contract_response.status_code:
            raise CaddeException(
                message_id='010001006E',
                status_code=token_contract_response.status_code,
                replace_str_list=[
                    token_contract_response.text])

    # 詳細URLに/cadde/api/v4/catalog を追加
    if detail_ckan_url != '' and detail_ckan_url[-1:] == '/':
        detail_ckan_url = detail_ckan_url.rstrip('/')

    detail_ckan_url = detail_ckan_url + __CKAN_API_PATH

    # トレースログ
    if trace_log_enable:
        token = False
        dt_now = datetime.datetime.now()
        if authorization:
            token = True
        log_message = {}
        log_message['log_type'] = 'browsing'
        log_message['timestamp'] = dt_now.isoformat(timespec='microseconds')
        log_message['consumer_id'] = consumer_id
        log_message['provider_id'] = provider_id
        log_message['type'] = 'search'
        log_message['search_type'] = 'detail'
        log_message['query'] = query_string
        log_message['authorization'] = token
        log_message['authorization_enable'] = ckan_authorization
        logger.info(json.dumps(log_message, ensure_ascii=False))

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
    データ管理に、NGSI、FTP、HTTPの取得を行い、取得データを返す

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
        Cadde_excption: カスタムヘッダー取得が異常終了の場合 エラーコード: 010002002E
        Cadde_excption: 認可トークン取得が200以外の場合      エラーコード: 010002003E
        Cadde_excption: 認可トークン検証が200以外の場合      エラーコード: 010002004E
        Cadde_excption: consumer_idの値が不正の場合          エラーコード: 010002005E
        Cadde_excption: 認可確認の制御値と認証トークン有無に不整合があった場合                エラーコード: 010002007E
        Cadde_excption: 認可確認が200以外の場合                                               エラーコード: 010002006E
        Cadde_excption: リソース提供手段識別子が'api/ngsi', 'file/ftp', 'file/http'以外の場合 エラーコード: 010002008E
        Cadde_excption: データ証憑通知（送信）：contract_idの値が不正の場合                   エラーコード: 010002009E
        Cadde_excption: データ証憑通知（送信）：contract_urlの値が不正の場合                  エラーコード: 010002010E
        Cadde_excption: データ証憑通知（送信）が200以外の場合                                 エラーコード: 010002011E
        Cadde_excption: 認証トークンなしで交換実績記録用IDが存在する場合                      エラーコード: 010002012E
        Cadde_excption: 送信履歴登録が200以外の場合                                           エラーコード: 010002013E

    """

    # ckanコンフィグ情報取得
    release_ckan_url, detail_ckan_url, ckan_authorization = __get_ckan_config(
        internal_interface)

    # connectorコンフィグ情報取得
    provider_id, provider_connector_id, provider_connector_secret, trace_log_enable = __get_connector_config(
        internal_interface)

    # 認証設定情報取得
    auth_check_enable = __get_auth_check_enable(
        resource_url, resource_api_type, internal_interface)
    print('auth_check_enable', auth_check_enable)

    # 取引市場利用設定情報取得
    contract_check_enable = __get_contract_check_enable(
        resource_url, resource_api_type, internal_interface)
    print('contract_check_enable', contract_check_enable)

    # カスタムヘッダー取得
    options_dict = None
    try:
        options_dict = __exchange_options_dict(options)
    except Exception:
        raise CaddeException('010002002E')

    # 変数設置
    consumer_id = ''
    contract_id = ''
    contract_type = ''
    contract_url = ''

    # 認可処理
    if authorization:
        # トークン連携(認可トークン取得)
        token_federation_headers = {
            'Authorization': authorization,
            'x-cadde-provider': provider_id,
            'x-cadde-provider-connector-id': provider_connector_id,
            'x-cadde-provider-connector-secret': provider_connector_secret
        }
        token_federation_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_FEDERATION_URL, token_federation_headers)

        if token_federation_response.status_code < 200 or 300 <= token_federation_response.status_code:
            raise CaddeException(
                message_id='010002003E',
                status_code=token_federation_response.status_code,
                replace_str_list=[
                    token_federation_response.text])

        get_token = token_federation_response.headers['x-cadde-auth-token']
        auth_token = f'Bearer {get_token}'

        # 認可トークン検証
        token_introspect_headers = {
            'Authorization': auth_token,
            'x-cadde-provider': provider_id,
            'x-cadde-provider-connector-id': provider_connector_id,
            'x-cadde-provider-connector-secret': provider_connector_secret
        }

        token_introspect_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_INTROSPECT_URL, token_introspect_headers)

        if token_introspect_response.status_code < 200 or 300 <= token_introspect_response.status_code:
            raise CaddeException(
                message_id='010002004E',
                status_code=token_introspect_response.status_code,
                replace_str_list=[
                    token_introspect_response.text])

        consumer_id = token_introspect_response.headers['x-cadde-consumer-id']
        if not consumer_id:
            raise CaddeException(
                message_id='010002005E',
                replace_str_list=[
                    token_introspect_response.text])

    # 対象のリソースURLが認可確認有ならば、認可確認を行う
    if auth_check_enable:
        # 設定値との整合性確認
        if not authorization:
            raise CaddeException('010002006E')

        # リソースURLを識別子に合わせて補正する
        convert_resource_url = __convert_resource_url(
            resource_api_type, resource_url, options)

        # 認可確認
        token_contract_headers = {
            'Authorization': auth_token,
            'x-cadde-provider': provider_id,
            'x-cadde-provider-connector-id': provider_connector_id,
            'x-cadde-provider-connector-secret': provider_connector_secret,
            'x-cadde-resource-url': convert_resource_url
        }

        token_contract_response = external_interface.http_get(
            __ACCESS_POINT_TOKEN_CONTRACT_URL, token_contract_headers)

        if token_contract_response.status_code < 200 or 300 <= token_contract_response.status_code:
            raise CaddeException(
                message_id='010002007E',
                status_code=token_contract_response.status_code,
                replace_str_list=[
                    token_contract_response.text])

        contract_id = token_contract_response.headers['x-cadde-contract-id']
        contract_type = token_contract_response.headers['x-cadde-contract-type']
        contract_url = token_contract_response.headers['x-cadde-contract-management-service-url']

    response_bytes = None
    response_headers = {}

    # リソースURLから、CKANを逆引き検索して、交換実績記録用リソースIDを取得
    resource_id_for_provenance = __ckan_search_execute(
        release_ckan_url, detail_ckan_url, resource_url, resource_api_type, options_dict, external_interface)

    # 識別子ごとにデータ取得
    if (resource_api_type == 'api/ngsi'):
        response_bytes, response_headers = provide_data_ngsi(
            resource_url, options_dict)

    elif (resource_api_type == 'file/ftp'):
        response_bytes = provide_data_ftp(
            resource_url, external_interface, internal_interface)

    elif (resource_api_type == 'file/http'):
        response_bytes = provide_data_http(
            resource_url, options_dict, external_interface, internal_interface)

    else:
        raise CaddeException('010002008E')

    response_data = response_bytes.read()
    response_bytes.seek(0)

    # リソースURLのドメインが認可確認有の場合、データ証憑通知（送信）
    if contract_check_enable:

        # ハッシュ値算出
        hash_value = hashlib.sha512(response_data).hexdigest()

        # 取引IDを確認する
        if not contract_id:
            raise CaddeException(
                message_id='010002009E',
                replace_str_list=['contract_id'])

        # 取引市場URLを取得できていることを確認する
        if not contract_url:
            raise CaddeException(
                message_id='010002010E',
                replace_str_list=['contract_url'])

        # 取引IDと契約管理サービスURLに値がある場合、データ証憑通知（送信）を行う
        sent_headers = {
            'x-cadde-provider': provider_id,
            'x-cadde-consumer': consumer_id,
            'x-cadde-contract-id': contract_id,
            'x-cadde-hash-get-data': hash_value,
            'x-cadde-contract-management-service-url': contract_url,
            'Authorization': authorization
        }
        sent_response = external_interface.http_post(
            __ACCESS_POINT_VOUCHER_URL, sent_headers)

        if sent_response.status_code < 200 or 300 <= sent_response.status_code:
            raise CaddeException(
                message_id='010002011E',
                status_code=sent_response.status_code,
                replace_str_list=[
                    sent_response.text])

    provenance_id = ''
    provenance_url = ''

    # 来歴管理:送信履歴登録
    # 交換実績記録用IDが有効値
    # CADDEユーザID（利用者）が有効値
    if resource_id_for_provenance:
        if not consumer_id:
            raise CaddeException(
                message_id='010002012E',
                replace_str_list=['contract_url'])

        sent_headers = {
            'x-cadde-provider': provider_id,
            'x-cadde-consumer': consumer_id,
            'x-cadde-resource-id-for-provenance': resource_id_for_provenance,
            'Authorization': authorization
        }
        sent_response = external_interface.http_post(
            __ACCESS_POINT_SENT_URL, sent_headers)

        if sent_response.status_code < 200 or 300 <= sent_response.status_code:
            raise CaddeException(
                message_id='010002013E',
                status_code=sent_response.status_code,
                replace_str_list=[
                    sent_response.text])

        provenance_id = sent_response.headers['x-cadde-provenance']
        provenance_url = sent_response.headers['x-cadde-provenance-management-service-url']

    response_headers['x-cadde-provenance'] = provenance_id
    response_headers['x-cadde-provenance-management-service-url'] = provenance_url
    response_headers['x-cadde-contract-id'] = contract_id
    response_headers['x-cadde-contract-type'] = contract_type
    response_headers['x-cadde-contract-management-service-url'] = contract_url

    # トレースログ
    if trace_log_enable:
        token = False
        dt_now = datetime.datetime.now()
        if authorization:
            token = True
        log_message = {}
        log_message['log_type'] = 'browsing'
        log_message['timestamp'] = dt_now.isoformat(timespec='microseconds')
        log_message['consumer_id'] = consumer_id
        log_message['provider_id'] = provider_id
        log_message['type'] = 'data_exchange'
        log_message['resource_url'] = resource_url
        log_message['resource_type'] = resource_api_type
        log_message['authorization'] = token
        log_message['options'] = options
        log_message['authorization_enable'] = auth_check_enable
        log_message['contract_enable'] = contract_check_enable
        logger.info(json.dumps(log_message, ensure_ascii=False))

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


def __get_ckan_config(internal_interface) -> (str, str):
    """
    ckan.configから情報を取得して返却する

    Args:
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        str: カタログサイト(公開)アクセスURL
        str: カタログサイト(詳細)アクセスURL
        str: 認可設定


    Raises:
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合                  エラーコード: 010000001E
        Cadde_excption: 必須パラメータが設定されていなかった場合（詳細CKANのURL）   エラーコード: 010000002E
        Cadde_excption: 必須パラメータが設定されていなかった場合（公開CKANのURL）   エラーコード: 010000003E
        Cadde_excption: 必須パラメータが設定されていなかった場合（認可設定）        エラーコード: 010000004E

    """

    release_ckan_url = ''

    try:
        ckan_config = internal_interface.config_read(
            __CONFIG_CKAN_URL_FILE_PATH)
    except Exception:
        raise CaddeException(message_id='010000001E')

    try:
        detail_ckan_url = ckan_config[__CONFIG_DETAIL_CKAN_URL]
    except Exception:
        raise CaddeException(message_id='010000002E',
                             replace_str_list=[__CONFIG_DETAIL_CKAN_URL])

    try:
        release_ckan_url = ckan_config[__CONFIG_RELEASE_CKAN_URL]
    except Exception:
        raise CaddeException(
            message_id='010000003E',
            replace_str_list=[__CONFIG_RELEASE_CKAN_URL])

    try:
        ckan_authorization = ckan_config[__CONFIG_CKAN_AUTHORIZATION]
    except Exception:
        raise CaddeException(message_id='010000004E',
                             replace_str_list=[__CONFIG_CKAN_AUTHORIZATION])

    if detail_ckan_url == '':
        detail_ckan_url = None

    return release_ckan_url, detail_ckan_url, ckan_authorization


def __get_connector_config(internal_interface) -> (str, str, str, str):
    """
    connector.configから情報を取得して返却する

    Args:
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        str: CADDEユーザID（提供者）
        str: 提供者コネクタID
        str: 提供者側コネクタのシークレット

    Raises:
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合                                     エラーコード: 010000005E
        Cadde_excption: 必須パラメータが設定されていなかった場合（提供者ID）                           エラーコード: 010000006E
        Cadde_excption: 必須パラメータが設定されていなかった場合（提供者コネクタID）                   エラーコード: 010000007E
        Cadde_excption: 必須パラメータが設定されていなかった場合（提供者側コネクタのシークレット）     エラーコード: 010000008E
        Cadde_excption: 必須パラメータが設定されていなかった場合（提供者側コネクタのトレースログ設定） エラーコード: 010000009E

    """

    provider_id = None
    provider_connector_id = None
    provider_connector_secret = None
    trace_log_enable = None
    try:
        connector_config = internal_interface.config_read(
            __CONFIG_CONNECTOR_FILE_PATH)
    except Exception:
        raise CaddeException(message_id='010000005E')

    try:
        provider_id = connector_config[__CONFIG_PROVIDER_ID]
    except Exception:
        raise CaddeException(
            message_id='010000006E',
            replace_str_list=[__CONFIG_PROVIDER_ID])

    try:
        provider_connector_id = connector_config[__CONFIG_PROVIDER_CONNECTOR_ID]
    except Exception:
        raise CaddeException(message_id='010000007E',
                             replace_str_list=[__CONFIG_PROVIDER_CONNECTOR_ID])

    try:
        provider_connector_secret = connector_config[__CONFIG_PROVIDER_CONNECTOR_SECRET]
    except Exception:
        raise CaddeException(message_id='010000008E', replace_str_list=[
                             __CONFIG_PROVIDER_CONNECTOR_SECRET])

    try:
        trace_log_enable = connector_config[__CONFIG_TRACE_LOG_ENABLE]
    except Exception:
        raise CaddeException(message_id='010000009E', replace_str_list=[
                             __CONFIG_TRACE_LOG_ENABLE])

    return provider_id, provider_connector_id, provider_connector_secret, trace_log_enable


def __get_auth_check_enable(resource_url,
                            resource_api_type,
                            internal_interface) -> str:
    """
    リソースURLのドメインからhttp.json、ftp.json、ngsi.jsonを検索して、認可確認の有無を返却
    Args:
        resource_url str : リソースURL
        resource_api_type str : リソース提供手段識別子
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        enable: 認可確認有無(True or False)

    Raises:
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合(ngsi.json)       エラーコード: 010000010E
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合(ftp.json)        エラーコード: 010000011E
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合(http.json)       エラーコード: 010000012E
        Cadde_excption: リソース提供手段識別子確認時に不正な値が設定されている場合  エラーコード: 010000013E
        Cadde_excption: 必須パラメータが設定されていなかった場合(リソースURL)       エラーコード: 010000014E

    """

    target_auth_data = []
    enable = True

    if (resource_api_type == 'api/ngsi'):
        try:
            config_data = internal_interface.config_read(
                __CONFIG_NGSI_FILE_PATH)
        except Exception:
            raise CaddeException(
                message_id='010000010E',
                replace_str_list=[__CONFIG_NGSI_FILE_PATH])

    elif (resource_api_type == 'file/ftp'):
        try:
            config_data = internal_interface.config_read(
                __CONFIG_FTP_FILE_PATH)
        except Exception:
            raise CaddeException(
                message_id='010000011E',
                replace_str_list=[__CONFIG_FTP_FILE_PATH])

    elif (resource_api_type == 'file/http'):
        try:
            config_data = internal_interface.config_read(
                __CONFIG_HTTP_FILE_PATH)
        except Exception:
            raise CaddeException(
                message_id='010000012E',
                replace_str_list=[__CONFIG_HTTP_FILE_PATH])

    else:
        raise CaddeException('010000013E')

    try:
        target_auth_data = [e for e in config_data[__COMMON_KEY_AUTH_TARGET]
                            if e[__COMMON_KEY_AUTH_URL] in resource_url]
    except Exception:
        # コンフィグファイルから指定したURLの情報が取得できない場合は何もしない
        pass
    if target_auth_data:
        if __COMMON_KEY_AUTH_ENABLE not in target_auth_data[0]:
            raise CaddeException(
                '010000014E',
                replace_str_list=[__COMMON_KEY_AUTH_ENABLE])

        enable = target_auth_data[0][__COMMON_KEY_AUTH_ENABLE]

    return enable


def __get_contract_check_enable(resource_url,
                                resource_api_type,
                                internal_interface) -> str:
    """
    リソースURLのドメインからhttp.json、ftp.json、ngsi.jsonを検索して、取引市場利用の有無を返却
    Args:
        resource_url str : リソースURL
        resource_api_type str : リソース提供手段識別子
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        enable: 取引市場利用(True or False)

    Raises:
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合(ngsi.json)       エラーコード: 010000015E
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合(ftp.json)        エラーコード: 010000016E
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合(http.json)       エラーコード: 010000017E
        Cadde_excption: リソース提供手段識別子確認時に不正な値が設定されている場合  エラーコード: 010000018E
        Cadde_excption: 必須パラメータが設定されていなかった場合(リソースURL)       エラーコード: 010000019E

    """

    target_contract_data = []
    enable = True

    if (resource_api_type == 'api/ngsi'):
        try:
            config_data = internal_interface.config_read(
                __CONFIG_NGSI_FILE_PATH)
        except Exception:
            raise CaddeException(
                message_id='010000015E',
                replace_str_list=[__CONFIG_NGSI_FILE_PATH])

    elif (resource_api_type == 'file/ftp'):
        try:
            config_data = internal_interface.config_read(
                __CONFIG_FTP_FILE_PATH)
        except Exception:
            raise CaddeException(
                message_id='010000016E',
                replace_str_list=[__CONFIG_FTP_FILE_PATH])

    elif (resource_api_type == 'file/http'):
        try:
            config_data = internal_interface.config_read(
                __CONFIG_HTTP_FILE_PATH)
        except Exception:
            raise CaddeException(
                message_id='010000017E',
                replace_str_list=[__CONFIG_HTTP_FILE_PATH])

    else:
        raise CaddeException('010000018E')

    try:
        target_contract_data = [e for e in config_data[__COMMON_KEY_CONTRACT_TARGET]
                                if e[__COMMON_KEY_CONTRACT_URL] in resource_url]
    except Exception:
        # コンフィグファイルから指定したURLの情報が取得できない場合は何もしない
        pass
    if target_contract_data:
        if __COMMON_KEY_CONTRACT_ENABLE not in target_contract_data[0]:
            raise CaddeException(
                '010000019E',
                replace_str_list=[__COMMON_KEY_CONTRACT_ENABLE])

        enable = target_contract_data[0][__COMMON_KEY_CONTRACT_ENABLE]

    return enable


def __ckan_search_execute(release_ckan_url,
                          detail_ckan_url,
                          resource_url,
                          resource_api_type,
                          options_dict,
                          external_interface) -> (str,
                                                  str):
    """
    公開Ckanと詳細CKANを検索して交換実績記録用リソースIDを返却
    Args:
        release_ckan_url str : 公開CKANのURL
        detail_ckan_url: 詳細CKANのURL
        resource_url: リソースURL

    Returns:
        resource_id_for_provenance: 交換実績記録用ID(str or None)
        dashboard_log_info: トレースログを出力するための情報

    Raises:
        Cadde_excption: 交換実績記録用リソースIDに登録されている値が混在している場合      エラーコード: 010000020E

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
        query_url = resource_url.split('entities')[0] + 'entities'
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

        if (one_data[__RESOURCE_ID_FOR_PROVENANCE] != ''
                and resource_id_for_provenance != one_data[__RESOURCE_ID_FOR_PROVENANCE]):
            raise CaddeException(message_id='010000020E')

    return resource_id_for_provenance


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

    Raises:
        Cadde_excption: 検索結果が取得できなかった場合      エラーコード: 010000021E

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
        raise CaddeException(message_id='010000021E')

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
            access_url = resource_url.split('entities')[0] + 'entities'

            parse_url = urllib.parse.urlparse(resource_url)
            query = urllib.parse.parse_qs(parse_url.query)

            # typeクエリは必ず指定される。
            ngsi_type = ''
            if 'type' in query.keys() and query['type'][0]:
                ngsi_type = query['type'][0]
            ngsi_tenant = ''
            ngsi_service_path = ''

            for key in options_dict:
                if 'fiware-service' == key.lower():
                    ngsi_tenant = options_dict[key].strip()
                if 'fiware-servicepath' == key.lower():
                    ngsi_service_path = options_dict[key].strip()

            # NGSIテナント、サービスパスの確認。指定しないケースを考慮する。
            ckan_ngsi_tenant = ''
            ckan_ngsi_service_path = ''
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


def __convert_resource_url(resource_api_type, resource_url, options_dict) -> (str):
    """
    リソースURLを識別子に合わせて補正する

    Returns:
        str: リソース識別子
        str: リソースURL
        dict: オプション

    Raises:
    """
    after_url = resource_url
    if (resource_api_type == 'api/ngsi'):
        ngsi_tenant = ''
        ngsi_service_path = ''
        for key in options_dict:
            if 'fiware-service' == key.lower():
                ngsi_tenant = ',Fiware-Service=' + options_dict[key].strip()
            if 'fiware-servicepath' == key.lower():
                ngsi_service_path = ',Fiware-ServicePath=' + \
                    options_dict[key].strip()
        after_url = resource_url + ngsi_tenant + ngsi_service_path

    result_url = after_url

    return result_url
