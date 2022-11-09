# -*- coding: utf-8 -*-
import datetime
import json
import logging
import hashlib
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


__LOCATION_SERVICE_PATH = '/cadde/api/v4/location/'
__CONFIG_LOCATION_FILE_PATH = '/usr/src/app/swagger_server/configs/location.json'
__CONFIG_CONNECTOR_FILE_PATH = '/usr/src/app/swagger_server/configs/connector.json'

__CONFIG_CONSUMER_CONNECTOR_ID = 'consumer_connector_id'
__CONFIG_CONSUMER_CONNECTOR_SECRET = 'consumer_connector_secret'
__CONFIG_TRACE_LOG_ENABLE = 'trace_log_enable'

__CONFIG_CONNECTOR_LOCATION = 'connector_location'
__CONFIG_LOCATION_SERVICE_URL = 'location_service_url'
__CONFIG_PROVIDER_CONNECTOR_URL = 'provider_connector_url'
__LOCATION_SERVICE_PROVIDER_CONNECTOR_URL = 'provider_connector_url'


__ACCESS_POINT_URL_SEARCH = 'http://consumer_catalog_search:8080/cadde/api/v4/catalog'
__ACCESS_POINT_URL_FILE = 'http://consumer_data_exchange:8080/cadde/api/v4/file'
__ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_LINEAGE = ('http://consumer_provenance_management:8080/'
                                                         'cadde/api/v4/history/lineage/')
__ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_SEARCHEVENTS = ('http://consumer_provenance_management:8080/'
                                                              'cadde/api/v4/history/searchevents')
__ACCESS_POINT_URL_AUTHENTICATION_AUTHORIZATION_FEDERATION = 'http://consumer_authentication:8080/token_federation'
__ACCESS_POINT_URL_AUTHENTICATION_AUTHORIZATION_INTROSPECT = 'http://consumer_authentication:8080/token_introspect'
__ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_RECEIVED = ('http://consumer_provenance_management:8080/'
                                                          'eventwithhash/received')
__ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_VOUCHER = 'http://consumer_provenance_management:8080/voucher/received'


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
    カタログ検索I/Fに、カタログ検索を行い、検索結果を返す

    Args:
        query_string str : クエリストリング
        search str : 検索種別
        provider str: CADDEユーザID（提供者）
        authorization str: 利用者トークン
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        Response : 取得した情報

    Raises:
        Cadde_excption: 検索種別確認時に不正な値が設定されている場合                エラーコード: 020001002E
        Cadde_excption: 認証I/F 認証トークン取得処理でエラーが発生した場合          エラーコード: 020001003E
        Cadde_excption: 認証I/F 認証トークン検証処理でエラーが発生した場合          エラーコード: 020001004E
        Cadde_excption: 提供者コネクタURLの取得に失敗した場合                       エラーコード: 020001005E
        Cadde_excption: カタログ検索I/Fのカタログ検索処理の呼び出しに失敗した場合   エラーコード: 020001006E

    """

    if search != 'meta' and search != 'detail':
        raise CaddeException('020001002E')

    consumer_connector_id, consumer_connector_secret, location_service_url, trace_log_enable = __get_connector_config()

    auth_token = None
    consumer_id = None

    if authorization:

        # トークン交換(認証トークン取得)
        token_federation_headers = {
            'Authorization': authorization,
            'x-cadde-consumer-connector-id': consumer_connector_id,
            'x-cadde-consumer-connector-secret': consumer_connector_secret
        }
        token_federation_response = external_interface.http_get(
            __ACCESS_POINT_URL_AUTHENTICATION_AUTHORIZATION_FEDERATION, token_federation_headers)

        if token_federation_response.status_code < 200 or 300 <= token_federation_response.status_code:
            raise CaddeException(
                message_id='020001003E',
                status_code=token_federation_response.status_code,
                replace_str_list=[
                    token_federation_response.text])

        get_token = token_federation_response.headers['x-cadde-auth-token']
        auth_token = f'Bearer {get_token}'

        # 認証トークン検証
        token_introspect_headers = {
            'Authorization': auth_token,
            'x-cadde-consumer-connector-id': consumer_connector_id,
            'x-cadde-consumer-connector-secret': consumer_connector_secret
        }
        token_introspect_response = external_interface.http_get(
            __ACCESS_POINT_URL_AUTHENTICATION_AUTHORIZATION_INTROSPECT, token_introspect_headers)

        if token_introspect_response.status_code < 200 or 300 <= token_introspect_response.status_code:
            raise CaddeException(
                message_id='020001004E',
                status_code=token_introspect_response.status_code,
                replace_str_list=[
                    token_introspect_response.text])

        consumer_id = token_introspect_response.headers['x-cadde-consumer-id']

    # ロケーション情報の設定
    if search == 'meta':
        provider_connector_url = None

    if search == 'detail':
        provider_connector_url = __get_location_info(
            provider, location_service_url, external_interface)
        if not provider_connector_url:
            raise CaddeException('020001005E')

    headers_dict = {
        'x-cadde-search': search,
        'x-cadde-provider-connector-url': provider_connector_url,
        'Authorization': auth_token,
    }

    target_url = __ACCESS_POINT_URL_SEARCH + query_string

    response = external_interface.http_get(target_url, headers_dict)
    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            '020001006E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    provider_id = ''
    provider_id = provider
    # トレースログ
    dt_now = datetime.datetime.now()
    if trace_log_enable:
        token = False
        if authorization:
            token = True
        log_message = {}
        log_message['log_type'] = 'browsing'
        log_message['timestamp'] = dt_now.isoformat(timespec='microseconds')
        log_message['consumer_id'] = consumer_id
        log_message['provider_id'] = provider_id
        log_message['type'] = 'search'
        log_message['search_type'] = search
        log_message['query'] = query_string
        log_message['authorization'] = token
        logger.info(json.dumps(log_message, ensure_ascii=False))
    return response


def fetch_data(authorization: str,
               resource_url: str,
               resource_api_type: str,
               provider: str,
               options: dict,
               external_interface: ExternalInterface = ExternalInterface()) -> (BytesIO,
                                                                                dict):
    """
    データ交換I/Fからデータを取得する、もしくはデータ管理から直接データを取得する。

    Args:
        resource_url str : リソースURL
        resource_api_type str : リソース提供手段識別子
        provider str : CADDEユーザID（提供者）
        authorization str : 利用者トークン
        options : dict リクエストヘッダ情報 key:ヘッダ名 value:パラメータ
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        BytesIO :取得データ
        dict: レスポンスヘッダ情報 key:ヘッダ名 value:パラメータ レスポンスヘッダがない場合は空のdictを返す

    Raises:
        Cadde_excption: リソース提供手段識別子確認時に不正な値が設定されている場合           エラーコード: 020004001E
        Cadde_excption: 認証I/F 認証トークン取得処理でエラーが発生した場合                   エラーコード: 020004002E
        Cadde_excption: 認証I/F 認証トークン検証処理でエラーが発生した場合                   エラーコード: 020004003E
        Cadde_excption: 提供者コネクタURLの取得に失敗した場合                                エラーコード: 020004004E
        Cadde_excption: データ提供IFが使用するカスタムヘッダーの変換に失敗した場合           エラーコード: 020004005E
        Cadde_excption: データ交換I/Fのデータ交換の呼び出し時に、エラーが発生した場合        エラーコード: 020004006E
        Cadde_excption: データ証憑通知(受信)時にCADDEユーザID（利用者）が空の場合            エラーコード: 020004007E
        Cadde_excption: 来歴管理I/F データ証憑通知(受信)API呼び出し時にエラーが発生した場合  エラーコード: 020004008E
        Cadde_excption: 受信履歴登録時にCADDEユーザID（利用者）が空の場合                    エラーコード: 020004009E
        Cadde_excption: 来歴管理I/F 受信履歴登録（来歴）API呼び出し時にエラーが発生した場合  エラーコード: 020004010E

    """

    if resource_api_type != 'api/ngsi' and resource_api_type != 'file/ftp' and resource_api_type != 'file/http':
        raise CaddeException('020004001E')

    consumer_connector_id, consumer_connector_secret, location_service_url, trace_log_enable = __get_connector_config()

    auth_token = None
    consumer_id = None

    if authorization:

        # トークン連携(認証トークン取得)
        token_federation_headers = {
            'Authorization': authorization,
            'x-cadde-consumer-connector-id': consumer_connector_id,
            'x-cadde-consumer-connector-secret': consumer_connector_secret
        }
        token_federation_response = external_interface.http_get(
            __ACCESS_POINT_URL_AUTHENTICATION_AUTHORIZATION_FEDERATION, token_federation_headers)

        if token_federation_response.status_code < 200 or 300 <= token_federation_response.status_code:
            raise CaddeException(
                message_id='020004002E',
                status_code=token_federation_response.status_code,
                replace_str_list=[
                    token_federation_response.text])

        get_token = token_federation_response.headers['x-cadde-auth-token']
        auth_token = f'Bearer {get_token}'

        # 認証トークン検証
        token_introspect_headers = {
            'Authorization': auth_token,
            'x-cadde-consumer-connector-id': consumer_connector_id,
            'x-cadde-consumer-connector-secret': consumer_connector_secret
        }
        token_introspect_response = external_interface.http_get(
            __ACCESS_POINT_URL_AUTHENTICATION_AUTHORIZATION_INTROSPECT, token_introspect_headers)

        if token_introspect_response.status_code < 200 or 300 <= token_introspect_response.status_code:
            raise CaddeException(
                message_id='020004003E',
                status_code=token_introspect_response.status_code,
                replace_str_list=[
                    token_introspect_response.text])

        consumer_id = token_introspect_response.headers['x-cadde-consumer-id']

    response_bytes = None
    response_headers = {'x-cadde-provenance': '', 'x-cadde-contract-id': ''}

    # CADDEユーザID（提供者）なし
    if not provider:
        if resource_api_type == 'api/ngsi':
            response_bytes, response_headers = provide_data_ngsi(
                resource_url, options)
            response_headers['x-cadde-provenance'] = ''

        elif resource_api_type == 'file/ftp':
            response_bytes = provide_data_ftp(
                resource_url, external_interface, internal_interface)

        elif resource_api_type == 'file/http':
            response_bytes = provide_data_http(
                resource_url, options, external_interface, internal_interface)

        return response_bytes, response_headers

    # CADDEユーザID（提供者）あり
    else:

        provider_connector_url = __get_location_info(
            provider, location_service_url, external_interface)
        if not provider_connector_url:
            raise CaddeException('020004004E')

        options_str = ''
        if resource_api_type == 'api/ngsi':
            try:
                options_str = __exchange_options_str(options)
            except Exception:
                raise CaddeException('020004005E')

        # データ取得用ヘッダーを生成
        headers_dict = {
            'x-cadde-resource-url': resource_url,
            'x-cadde-resource-api-type': resource_api_type,
            'x-cadde-provider-connector-url': provider_connector_url,
            'Authorization': auth_token,
            'x-cadde-options': options_str
        }

        # データ取得実行
        response = external_interface.http_get(
            __ACCESS_POINT_URL_FILE, headers_dict)
        if response.status_code < 200 or 300 <= response.status_code:
            raise CaddeException(
                '020004006E',
                status_code=response.status_code,
                replace_str_list=[
                    response.text])

        response_bytes = BytesIO(response.content)
        get_headers = {}
        get_headers = dict(response.headers)
        response_data = response_bytes.read()
        response_bytes.seek(0)

        # レスポンスヘッダからデータを取得
        contract_url = ''
        contract_url = get_headers['x-cadde-contract-management-service-url']
        contract_id = ''
        contract_id = get_headers['x-cadde-contract-id']
        provenance_id = ''
        provenance_id = get_headers['x-cadde-provenance']
        provenance_url = ''
        provenance_url = get_headers['x-cadde-provenance-management-service-url']

        # 来歴管理：データ証憑通知(受信)
        # 契約している場合（戻り値に取引ID、契約管理サービスURLが設定されている場合）に行う
        if contract_id and contract_url:
            # 認証あり（consumer_id有効）の場合に行う
            if consumer_id is None:
                raise CaddeException('020004007E')
            # ハッシュ値算出
            hash_value = hashlib.sha512(response_data).hexdigest()

            sent_headers = {
                'x-cadde-provider': provider,
                'x-cadde-consumer': consumer_id,
                'x-cadde-contract-id': contract_id,
                'x-cadde-hash-get-data': hash_value,
                'x-cadde-contract-management-service-url': contract_url,
                'Authorization': authorization
            }

            sent_response = external_interface.http_post(
                __ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_VOUCHER, sent_headers)

            if sent_response.status_code < 200 or 300 <= sent_response.status_code:
                raise CaddeException(
                    message_id='020004008E',
                    status_code=sent_response.status_code,
                    replace_str_list=[
                        sent_response.text])

            # レスポンスヘッダ：契約IDを更新
            response_headers['x-cadde-contract-id'] = contract_id

        # 来歴管理：受信履歴登録
        # 交換実績記録用リソースIDあり、かつ、認証あり（consumer_id有効）
        if provenance_id != '':
            if consumer_id is None:
                raise CaddeException('020004009E')

            received_headers = {
                'x-cadde-provider': provider,
                'x-cadde-consumer': consumer_id,
                'x-cadde-resource-id-for-provenance': provenance_id,
                'x-cadde-provenance-management-service-url': provenance_url,
                'Authorization': auth_token,
            }

            received_response = external_interface.http_post(
                __ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_RECEIVED, received_headers)

            if received_response.status_code < 200 or 300 <= received_response.status_code:
                raise CaddeException(
                    message_id='020004010E',
                    status_code=received_response.status_code,
                    replace_str_list=[
                        received_response.text])

            # レスポンスヘッダ：識別情報を更新
            response_headers['x-cadde-provenance'] = received_response.headers['x-cadde-provenance']

    provider_id = ''
    provider_id = provider
    # トレースログ
    dt_now = datetime.datetime.now()
    if trace_log_enable:
        token = False
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
        logger.info(json.dumps(log_message, ensure_ascii=False))

    return response_bytes, response_headers


def history_confirmation_call(
        authorization: str,
        cadde_resource_id_for_provenance: str,
        direction: str,
        depth: int,
        external_interface: ExternalInterface) -> Response:
    """
    来歴管理I/Fに来歴確認処理を依頼する

    Args:
        cadde_resource_id_for_provenance str: 交換実績記録用リソースID
        direction str: 履歴取得方向
        depth str: 検索深度
        external_interface ExternalInterface : 外部にリクエストを行うインタフェース

    Returns:
        Response : 来歴管理I/Fのレスポンス

    Raises:
        Cadde_excption : 各機能でパラメータ確認時に必須パラメータが設定されていなかった場合
        （履歴取得方向）                                                              エラーコード :020005002E
        Cadde_excption : 各機能でパラメータ確認時に必須パラメータが設定されていなかった場合
        （検索深度）                                                                  エラーコード :020005003E
        Cadde_excption : 認証I/F 認証トークン取得処理でエラーが発生した場合           エラーコード :020005004E
        Cadde_excption : 来歴確認処理でエラーが発生した場合                           エラーコード :020005005E
        Cadde_excption : 来歴登録に成功したがレスポンスを正常に取得できなかった場合   エラーコード :020005006E

    """

    consumer_connector_id, consumer_connector_secret, location_service_url, trace_log_enable = __get_connector_config()

    if direction is not None and direction not in __DIRECTION_NORMALITY_VALUES:
        raise CaddeException(message_id='020005002E')

    if depth is not None and bool(int(depth) < __DEPTH_MIN_VALUE):
        raise CaddeException(message_id='020005003E')

    # トークン連携(認証トークン取得)
    token_federation_headers = {
        'Authorization': authorization,
        'x-cadde-consumer-connector-id': consumer_connector_id,
        'x-cadde-consumer-connector-secret': consumer_connector_secret
    }
    token_federation_response = external_interface.http_get(
        __ACCESS_POINT_URL_AUTHENTICATION_AUTHORIZATION_FEDERATION, token_federation_headers)

    if token_federation_response.status_code < 200 or 300 <= token_federation_response.status_code:
        raise CaddeException(
            message_id='020005004E',
            status_code=token_federation_response.status_code,
            replace_str_list=[
                token_federation_response.text])

    get_token = token_federation_response.headers['x-cadde-auth-token']
    auth_token = f'Bearer {get_token}'

    send_url = __ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_LINEAGE + \
        cadde_resource_id_for_provenance

    headers = {
        'Authorization': auth_token,
        'x-cadde-direction': direction,
        'x-cadde-depth': depth
    }

    response = external_interface.http_get(send_url, headers)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='020005005E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    if not hasattr(response, 'text') or not response.text:
        raise CaddeException(message_id='020005006E')

    return response


def history_id_search_call(
        authorization: str,
        body: dict,
        external_interface: ExternalInterface) -> Response:
    """
    来歴管理I/Fに履歴ID検索処理を依頼する

    Args:
        body dict: 履歴ID検索用文字列
        external_interface ExternalInterface : 外部にリクエストを行うインタフェース

    Returns:
        Response : 来歴管理I/Fのレスポンス

    Raises:
        Cadde_excption : 認証I/F 認証トークン取得処理でエラーが発生した場合       エラーコード :020006002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード               エラーコード :020006003E
        Cadde_excption : レスポンスを正常に取得できなかった場合 エラーコード      エラーコード :020006004E

    """

    consumer_connector_id, consumer_connector_secret, location_service_url, trace_log_enable = __get_connector_config()

    # トークン連携(認証トークン取得)
    token_federation_headers = {
        'Authorization': authorization,
        'x-cadde-consumer-connector-id': consumer_connector_id,
        'x-cadde-consumer-connector-secret': consumer_connector_secret
    }
    token_federation_response = external_interface.http_get(
        __ACCESS_POINT_URL_AUTHENTICATION_AUTHORIZATION_FEDERATION, token_federation_headers)

    if token_federation_response.status_code < 200 or 300 <= token_federation_response.status_code:
        raise CaddeException(
            message_id='020006002E',
            status_code=token_federation_response.status_code,
            replace_str_list=[
                token_federation_response.text])

    get_token = token_federation_response.headers['x-cadde-auth-token']
    auth_token = f'Bearer {get_token}'

    header_dict = {
        'Authorization': auth_token,
        'content-type': 'application/json'
    }

    response = external_interface.http_post(
        __ACCESS_POINT_URL_PROVENANCE_MANAGEMENT_CALL_SEARCHEVENTS, header_dict, body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='020006003E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    if not hasattr(response, 'text') or not response.text:
        raise CaddeException(message_id='020006004E')

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


def __get_location_info(provider, location_service_url, external_interface) -> (str):
    """
    ロケーション情報取得
    CADDEユーザID（提供者）をキーにして、ロケーションサービスから情報を取得する。
    ロケーションサービスから取得ができなかった場合、
    location.jsonからコンフィグ情報を取得する。

    Args:
        provider string : CADDEユーザID（提供者）
        location_service_url string : ロケーションサービスのURL

    Returns:
        str: 提供者コネクタのアクセスURL

    Raises:
        Cadde_excption: 必須パラメータが設定されていなかった場合（ロケーションサービスのURL）     エラーコード: 020000001E
        Cadde_excption: 必須パラメータが設定されていなかった場合（CADDEユーザID（提供者））       エラーコード: 020000002E
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合                                エラーコード: 020000003E
        Cadde_excption: 必須パラメータが設定されていなかった場合（コネクタロケーション）          エラーコード: 020000004E

    """

    if location_service_url is None:
        raise CaddeException(
            message_id='020000001E',
            replace_str_list=['location_service_url'])

    if provider is None:
        raise CaddeException(
            message_id='020000002E',
            replace_str_list=['provider_id'])

    provider_connector_url = ''

    # ロケーションサービスへ取得リクエスト
    response = __get_location_from_location_service(
        provider, location_service_url, external_interface)

    if response:
        provider_connector_url = response
        return provider_connector_url

    # コンフィグから再取得を試みる
    logger.info(f'Not Found {provider} from {location_service_url}')
    try:
        config = internal_interface.config_read(__CONFIG_LOCATION_FILE_PATH)
    except Exception:  # pathミス
        raise CaddeException(
            message_id='020000003E',
            replace_str_list=[__CONFIG_LOCATION_FILE_PATH])
    try:
        connector_location = config[__CONFIG_CONNECTOR_LOCATION]
    except Exception:  # オブジェクトなし
        raise CaddeException(
            message_id='020000004E',
            replace_str_list=[__CONFIG_CONNECTOR_LOCATION])
    try:
        provider_info = connector_location[provider]
        provider_connector_url = provider_info[__CONFIG_PROVIDER_CONNECTOR_URL]
    except Exception:  # コンフィグファイルから指定したURLの情報が取得できない場合は何もしない
        pass

    return provider_connector_url


def __get_location_from_location_service(provider, location_service_url, external_interface) -> (str):
    """
    ロケーションサービス問合せ
    ロケーションサービスから取得APIを実行して 提供者コネクタのアクセスURLを取得する

    Args:
        provider string : CADDEユーザID（提供者）
        location_service_url string : ロケーションサービスのURL

    Returns:
        str: 提供者コネクタのアクセスURL

    Raises:
        本処理ではエラーのキャッチは行わない

    """
    response = {}
    provider_connector_url = ''

    send_url = location_service_url + __LOCATION_SERVICE_PATH + provider
    header = {
        'accept': 'application/json'
    }
    # 取得リクエストを実行
    try:
        response = external_interface.http_get(send_url, header)
        # レスポンスからロケーション情報取得
        response_text_dict = json.loads(response.text)
        if __LOCATION_SERVICE_PROVIDER_CONNECTOR_URL in response_text_dict:
            provider_connector_url = response_text_dict[__LOCATION_SERVICE_PROVIDER_CONNECTOR_URL]

    except Exception:
        pass

    return provider_connector_url


def __get_connector_config() -> (str, str, str, str):
    """
    connector.jsonからコンフィグ情報を取得し、
    利用者側コネクタID、利用者側コネクタのシークレット、来歴管理者用トークンを返す。

    Returns:
        str: 利用者側コネクタID
        str: 利用者側コネクタのシークレット
        str: ロケーションサービスのURL
        str: トレースログ設定

    Raises:
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合                                エラーコード: 020000005E
        Cadde_excption: 必須パラメータが設定されていなかった場合（利用者コネクタID）              エラーコード: 020000006E
        Cadde_excption: 必須パラメータが設定されていなかった場合（利用者コネクタのシークレット）  エラーコード: 020000007E
        Cadde_excption: 必須パラメータが設定されていなかった場合（ロケーションサービスのURL）     エラーコード: 020000008E
        Cadde_excption: 必須パラメータが設定されていなかった場合（トレースログ設定）              エラーコード: 020000009E

    """
    consumer_connector_id = None
    consumer_connector_secret = None
    location_service_url = None
    trace_log_enable = None

    try:
        connector = internal_interface.config_read(
            __CONFIG_CONNECTOR_FILE_PATH)
    except Exception:
        raise CaddeException(
            message_id='020000005E',
            replace_str_list=[__CONFIG_CONNECTOR_FILE_PATH])

    try:
        consumer_connector_id = connector[__CONFIG_CONSUMER_CONNECTOR_ID]
    except Exception:
        raise CaddeException(
            message_id='020000006E',
            replace_str_list=[__CONFIG_CONSUMER_CONNECTOR_ID])

    try:
        consumer_connector_secret = connector[__CONFIG_CONSUMER_CONNECTOR_SECRET]
    except Exception:
        raise CaddeException(
            message_id='020000007E',
            replace_str_list=[__CONFIG_CONSUMER_CONNECTOR_SECRET])

    try:
        location_service_url = connector[__CONFIG_LOCATION_SERVICE_URL]
    except Exception:
        raise CaddeException(
            message_id='020000008E',
            replace_str_list=[__CONFIG_LOCATION_SERVICE_URL])

    try:
        trace_log_enable = connector[__CONFIG_TRACE_LOG_ENABLE]
    except Exception:
        raise CaddeException(
            message_id='020000009E',
            replace_str_list=[__CONFIG_TRACE_LOG_ENABLE])

    return consumer_connector_id, consumer_connector_secret, location_service_url, trace_log_enable

