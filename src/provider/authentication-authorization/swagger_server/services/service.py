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
__CONFIG_PAT_REQ = 'pat_req'
__CONFIG_PAT_REQ_ENDPOINT = 'endpoint'
__CONFIG_PAT_REQ_GRANT_TYPE = 'grant_type'
__CONFIG_RESOURCE = 'resource'
__CONFIG_RESOURCE_ENDPOINT = 'endpoint'
__CONFIG_CONTRACT = 'contract'
__CONFIG_CONTRACT_ENDPOINT = 'endpoint'
__CONFIG_CONTRACT_GRANT_TYPE = 'grant_type'

def token_introspect_execute(
        authorization: str,
        provider_connector_id: str,
        provider_connector_secret: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認証認可要求を行い、CADDEユーザID(利用者)を返す。

    Args:
        authorization str : 認可トークン
        provider_connector_id str : 提供者コネクタID
        provider_connector_secret str : 提供者コネクタシークレットのID
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : CADDEユーザID(利用者)

    Raises:
        Cadde_excption : コンフィグファイルからauthentication_server_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 0A002E
        Cadde_excption : トークンが有効でなかった場合 エラーコード : 0A003E
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
        'client_id': provider_connector_id,
        'client_secret': provider_connector_secret,
        'token': authorization}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    access_url = authentication_server_url + '/' + endpoint
    response = external_interface.http_post(
        access_url, headers, post_body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='0A002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)

    if 'active' not in response_text_dict:
        raise CaddeException(message_id='0A003E')

    if not response_text_dict['active']:
        raise CaddeException(message_id='0A003E')

    if 'username' not in response_text_dict:
        raise CaddeException(message_id='0A003E')

    consumer_id = response_text_dict['username']

    return consumer_id

def token_federation_execute(
        authorization: str,
        provider_connector_id: str,
        provider_connector_secret: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認可トークン取得要求を行い、認可トークンを返す。

    Args:
        authorization str : 認証トークン
        provider_connector_id str : 提供者コネクタID
        provider_connector_secret str : 提供者コネクタシークレットのID
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : 認可トークン

    Raises:
        Cadde_excption : コンフィグファイルからauthentication_server_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1A005E
        Cadde_excption : 提供者トークンが有効でなかった場合 エラーコード : 1A006E
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
        subject_issuer = config[__CONFIG_FEDERATION][__CONFIG_FEDERATION_SUBJECT_ISSUER]
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
                __CONFIG_FEDERATION_REQUESTED_TOKEN_TYPE,
                __CONFIG_FEDERATION_SUBJECT_ISSUER])

    # 引数からpost通信のbody部に指定する情報をdict型で作成

    post_body = {
        'client_id': provider_connector_id,
        'client_secret': provider_connector_secret,
        'subject_token': authorization,
        'grant_type': grant_type,
        'subject_token_type': subject_token_type,
        'requested_token_type': requested_token_type,
        'subject_issuer': subject_issuer}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    access_url = authentication_server_url + '/' + endpoint
    response = external_interface.http_post(
        access_url, headers, post_body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='0A005E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)
    auth_token = response_text_dict['access_token']

    return auth_token

def token_req_pat_execute(
        provider_connector_id: str,
        provider_connector_secret: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認証認可サーバに対して、APIトークンをリクエストし、APIトークンを取得する。

    Args:
        provider_connector_id str : 提供者コネクタID
        provider_connector_secret str : 提供者コネクタシークレットのID
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : APIトークン

    Raises:
        Cadde_excption : コンフィグファイルからauthentication_server_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1A005E
        Cadde_excption : 提供者トークンが有効でなかった場合 エラーコード : 1A006E
    """

    # コンフィグファイルから認証認可サーバのURL取得
    try:
        config = internal_interface.config_read(
            __CONFIG_AUTHENTICATION_FILE_PATH)
        authentication_server_url = config[__CONFIG_AUTHENTICATION_SERVER_URL]
        endpoint = config[__CONFIG_PAT_REQ][__CONFIG_PAT_REQ_ENDPOINT]
        grant_type = config[__CONFIG_PAT_REQ][__CONFIG_PAT_REQ_GRANT_TYPE]
    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[
                __CONFIG_AUTHENTICATION_SERVER_URL,
                __CONFIG_PAT_REQ,
                __CONFIG_PAT_REQ_ENDPOINT,
                __CONFIG_PAT_REQ_GRANT_TYPE])

    # 引数からpost通信のbody部に指定する情報をdict型で作成

    post_body = {
        'client_id': provider_connector_id,
        'client_secret': provider_connector_secret,
        'grant_type': grant_type}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    access_url = authentication_server_url + '/' + endpoint
    response = external_interface.http_post(
        access_url, headers, post_body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='0A007E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)
    api_token = response_text_dict['access_token']

    return api_token

def token_resource_execute(
        authorization: str,
        resource_url: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認証認可サーバに対して、リソースIDチェックをリクエストし、リソースIDを取得する。

    Args:
        authorization str : APIトークン
        resource_url str : リソースURL
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : APIトークン

    Raises:
        Cadde_excption : コンフィグファイルからauthentication_server_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1A005E
        Cadde_excption : 提供者トークンが有効でなかった場合 エラーコード : 1A006E
    """

    # コンフィグファイルから認証認可サーバのURL取得
    try:
        config = internal_interface.config_read(
            __CONFIG_AUTHENTICATION_FILE_PATH)
        authentication_server_url = config[__CONFIG_AUTHENTICATION_SERVER_URL]
        endpoint = config[__CONFIG_RESOURCE][__CONFIG_RESOURCE_ENDPOINT]
    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[
                __CONFIG_AUTHENTICATION_SERVER_URL,
                __CONFIG_RESOURCE,
                __CONFIG_RESOURCE_ENDPOINT])

    # 引数からpost通信のbody部に指定する情報をdict型で作成

    post_body = {'uri': resource_url}

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + authorization
        }

    access_url = authentication_server_url + '/' + endpoint
    response = external_interface.http_get(
        access_url, headers, None, post_body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='0A009E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)
    resource_id = response_text_dict[0]

    return resource_id

def token_contract_execute(
        authorization: str,
        resource_id: str,
        provider_connector_id: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認証認可サーバに対して、契約確認をリクエストする。

    Args:
        authorization str : APIトークン
        resource_id str : リソースID
        provider_connector_id str : 提供者コネクタID
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : APIトークン

    Raises:
        Cadde_excption : コンフィグファイルからauthentication_server_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1A005E
        Cadde_excption : 提供者トークンが有効でなかった場合 エラーコード : 1A006E
    """

    # コンフィグファイルから認証認可サーバのURL取得
    try:
        config = internal_interface.config_read(
            __CONFIG_AUTHENTICATION_FILE_PATH)
        authentication_server_url = config[__CONFIG_AUTHENTICATION_SERVER_URL]
        endpoint = config[__CONFIG_CONTRACT][__CONFIG_CONTRACT_ENDPOINT]
        grant_type = config[__CONFIG_CONTRACT][__CONFIG_CONTRACT_GRANT_TYPE]
    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[
                __CONFIG_AUTHENTICATION_SERVER_URL,
                __CONFIG_RESOURCE,
                __CONFIG_RESOURCE_ENDPOINT])

    # 引数からpost通信のbody部に指定する情報をdict型で作成

    post_body = {
        'grant_type': grant_type,
        'permission': resource_id,
        'audience': provider_connector_id}

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + authorization
        }

    access_url = authentication_server_url + '/' + endpoint
    response = external_interface.http_post(
        access_url, headers, post_body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='0A011E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)

    if 'access_token' not in response_text_dict:
        raise CaddeException(message_id='0A012E')

    access_token = response_text_dict['access_token']

    return access_token

def token_resource_info_execute(
        authorization: str,
        resource_id: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認証認可サーバに対して、リソース情報をリクエストし、リソース情報を取得する。

    Args:
        authorization str : APIトークン
        resource_id str : リソースID
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : APIトークン

    Raises:
        Cadde_excption : コンフィグファイルからauthentication_server_urlを取得できない場合、エラーコード : 00002E
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 1A005E
        Cadde_excption : 提供者トークンが有効でなかった場合 エラーコード : 1A006E
    """

    # コンフィグファイルから認証認可サーバのURL取得
    try:
        config = internal_interface.config_read(
            __CONFIG_AUTHENTICATION_FILE_PATH)
        authentication_server_url = config[__CONFIG_AUTHENTICATION_SERVER_URL]
        endpoint = config[__CONFIG_RESOURCE][__CONFIG_RESOURCE_ENDPOINT]
    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[
                __CONFIG_AUTHENTICATION_SERVER_URL,
                __CONFIG_RESOURCE,
                __CONFIG_RESOURCE_ENDPOINT])

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + authorization
        }

    access_url = authentication_server_url + '/' + endpoint + '/' + resource_id
    response = external_interface.http_get(
        access_url, headers)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='0A014E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)

    if 'attributes' not in response_text_dict:
        raise CaddeException(message_id='0A015E')

    attributes = response_text_dict['attributes']

    return attributes

