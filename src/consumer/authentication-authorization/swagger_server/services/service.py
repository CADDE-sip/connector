# -*- coding: utf-8 -*-
import json

from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

__CONFIG_AUTHENTICATION_FILE_PATH = '/usr/src/app/swagger_server/configs/authentication.json'
__CONFIG_AUTHENTICATION_SERVER_URL = 'authentication_server_url'
__CONFIG_INTROSPECT = 'introspect'
__CONFIG_INTROSPECT_ENDPOINT = 'endpoint'
__CONFIG_FEDERATION = 'federation'
__CONFIG_FEDERATION_ENDPOINT = 'endpoint'
__CONFIG_FEDERATION_GRANT_TYPE = 'grant_type'
__CONFIG_FEDERATION_SUBJECT_TOKEN_TYPE = 'subject_token_type'
__CONFIG_FEDERATION_REQUESTED_TOKEN_TYPE = 'requested_token_type'
__CONFIG_FEDERATION_SUBJECT_ISSUER = 'subject_issuer'

__CADDE_IDP = 'cadde'

def token_introspect_execute(
        authorization: str,
        consumer_connector_id: str,
        consumer_connector_secret: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認証要求を行い、CADDEユーザID(利用者)を返す。

    Args:
        authorization str : 利用者トークン
        consumer_connector_id str : 利用者コネクタID
        consumer_connector_secret str : 利用者コネクタシークレットのID
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : 利用者ID

    Raises:
        Cadde_excption : コンフィグファイルからauthentication_server_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1A002E
        Cadde_excption : 利用者トークンが有効でなかった場合 エラーコード : 1A003E
    """

    # コンフィグファイルから認証認可サーバのURL取得
    try:
        config = internal_interface.config_read(
            __CONFIG_AUTHENTICATION_FILE_PATH)
        authentication_server_url = config[__CONFIG_AUTHENTICATION_SERVER_URL]
        endpoint = config[__CONFIG_INTROSPECT][__CONFIG_INTROSPECT_ENDPOINT]

    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[__CONFIG_AUTHENTICATION_SERVER_URL, __CONFIG_INTROSPECT, __CONFIG_INTROSPECT_ENDPOINT])

    # 引数からpost通信のbody部に指定する情報をdict型で作成

    post_body = {
        'client_id': consumer_connector_id,
        'client_secret': consumer_connector_secret,
        'token': authorization}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    access_url = authentication_server_url + '/' + endpoint
    response = external_interface.http_post(
        access_url, headers, post_body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='1A002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)

    if 'active' not in response_text_dict:
        raise CaddeException(message_id='1A003E')

    if not response_text_dict['active']:
        raise CaddeException(message_id='1A003E')

    if 'username' not in response_text_dict:
        raise CaddeException(message_id='1A003E')

    consumer_id = response_text_dict['username']

    # コネクタ限定チェック処理 (2021年3月版では実施しない)

    return consumer_id

def token_federation_execute(
        authorization: str,
        consumer_connector_id: str,
        consumer_connector_secret: str,
        idp: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認証トークン取得要求を行い、認証トークンを返す。

    Args:
        authorization str : 利用者トークン
        consumer_connector_id str : 利用者コネクタID
        consumer_connector_secret str : 利用者コネクタシークレットのID
        idp str : アイデンティティ・プロバイダー
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : 認証トークン

    Raises:
        Cadde_excption : コンフィグファイルからauthentication_server_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1A005E
        Cadde_excption : 利用者トークンが有効でなかった場合 エラーコード : 1A006E
    """

    # コンフィグファイルから認証認可サーバのURL取得
    try:
        config = internal_interface.config_read(
            __CONFIG_AUTHENTICATION_FILE_PATH)
        authentication_server_url = config[__CONFIG_AUTHENTICATION_SERVER_URL]
        endpoint = config[__CONFIG_FEDERATION][__CONFIG_FEDERATION_ENDPOINT]
        grant_type = config[__CONFIG_FEDERATION][__CONFIG_FEDERATION_GRANT_TYPE]
        subject_token_type = config[__CONFIG_FEDERATION][__CONFIG_FEDERATION_SUBJECT_TOKEN_TYPE]
        requested_token_type = config[__CONFIG_FEDERATION][__CONFIG_FEDERATION_REQUESTED_TOKEN_TYPE]
    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[
                __CONFIG_AUTHENTICATION_SERVER_URL,
                __CONFIG_FEDERATION,
                __CONFIG_FEDERATION_ENDPOINT,
                __CONFIG_FEDERATION_GRANT_TYPE,
                __CONFIG_FEDERATION_SUBJECT_TOKEN_TYPE,
                __CONFIG_FEDERATION_REQUESTED_TOKEN_TYPE])

    # 引数からpost通信のbody部に指定する情報をdict型で作成
    post_body = {}
    if idp == __CADDE_IDP:
        # 外部IdPを使用しない場合
        post_body = {
            'client_id': consumer_connector_id,
            'client_secret': consumer_connector_secret,
            'grant_type': grant_type,
            'subject_token': authorization
        }
    else:
        # 外部IdPを使用する場合
        post_body = {
            'client_id': consumer_connector_id,
            'client_secret': consumer_connector_secret,
            'grant_type': grant_type,
            'subject_token': authorization,
            'subject_token_type': subject_token_type,
            'requested_token_type': requested_token_type,
            'subject_issuer': idp}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    access_url = authentication_server_url + '/' + endpoint
    response = external_interface.http_post(
        access_url, headers, post_body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='1A005E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)

    if 'access_token' not in response_text_dict:
        raise CaddeException(message_id='1A006E')

    auth_token = response_text_dict['access_token']

    # コネクタ限定チェック処理 (2021年3月版では実施しない)

    return auth_token
