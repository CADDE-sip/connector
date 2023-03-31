# -*- coding: utf-8 -*-
import json
import base64

from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

__CONFIG_AUTHORIZATION_FILE_PATH = '/usr/src/app/swagger_server/configs/authorization.json'
__CONFIG_AUTHORIZATION_SERVER_URL = 'authorization_server_url'

__CADDE_FEDERATION = '/cadde/api/v4/token/federate'
__CADDE_AUTHZ = '/cadde/api/v4/authz/confirm'


def token_federation_execute(
        authorization: str,
        cadde_provider: str,
        provider_connector_id: str,
        provider_connector_secret: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認可トークン取得を行い、認可トークンを返す。

    Args:
        authorization str : 認証トークン
        cadde_provider : CADDEユーザID（提供者）
        provider_connector_id str : 提供者コネクタID
        provider_connector_secret str : 提供者コネクタシークレットのID
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : 認可トークン

    Raises:
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 010401002E

    """

    # コンフィグファイルから認可サーバのURL取得
    authorization_server_url = __get_authorization_config(internal_interface)

    if not authorization_server_url:
        authorization_server_url = __get_authorization_url(authorization[7:])

    # authorizationからtokenを抜き出す
    if not authorization.startswith('Bearer'):
        raise CaddeException(message_id='010401002E')

    # Authorizationにセットする情報をBase64エンコードする
    credential = f'{provider_connector_id}:{provider_connector_secret}'
    bearer = base64.b64encode(credential.encode()).decode()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {bearer}'
    }

    # 引数からpost通信のbody部に指定する情報をdict型で作成
    post_body = {
        'access_token': authorization[7:],
        'provider_id': cadde_provider
    }

    # アクセスURLの生成
    access_url = authorization_server_url + __CADDE_FEDERATION

    # リクエスト実行
    response = external_interface.http_post(
        access_url, headers, post_body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='010401003E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)

    if 'access_token' not in response_text_dict or not response_text_dict['access_token']:
        raise CaddeException(
            message_id='010400004E'
        )

    auth_token = response_text_dict['access_token']

    # authorizationからtokenを抜き出す
    consumer_id = __get_authorization_consumer_id(authorization[7:])

    return auth_token, consumer_id


def token_contract_execute(
        authorization: str,
        cadde_provider: str,
        provider_connector_id: str,
        provider_connector_secret: str,
        resource_url: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> (str, str, str):
    """
    認可サーバに対して、契約確認をリクエストする。

    Args:
        authorization str : 認可トークン
        cadde_provider str : CADDEユーザID(提供者)
        provider_connector_id str : 提供者コネクタID
        provider_connector_secret str : 提供者コネクタのシークレット
        resource_url str : リソースURL
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : 取引ID
        str : 契約形態
        str : 契約管理サービスURL

    Raises:
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 010403002E

    """

    # コンフィグファイルから認可サーバのURL取得
    authorization_server_url = __get_authorization_config(internal_interface)

    if not authorization_server_url:
        authorization_server_url = __get_authorization_url(authorization[7:])

    # Authorizationにセットする情報をBase64エンコードする
    credential = f'{provider_connector_id}:{provider_connector_secret}'
    bearer = base64.b64encode(credential.encode()).decode()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {bearer}'
    }

    # 引数からpost通信のbody部に指定する情報をdict型で作成
    post_body = {
        'access_token': authorization[7:],
        'provider_id': cadde_provider,
        'resource_url': resource_url
    }

    # アクセスURLの生成
    access_url = authorization_server_url + __CADDE_AUTHZ

    # リクエスト実行
    response = external_interface.http_post(
        access_url, headers, post_body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='010403002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)
    contract_id = response_text_dict['contract']['trade_id']
    contract_type = response_text_dict['contract']['contract_type']
    contract_url = response_text_dict['contract']['contract_url']

    return contract_id, contract_type, contract_url


def __get_authorization_config(internal_interface) -> (str):
    """
    authorization.configから認可サーバのURL取得

    Args:
        internal_interface : 内部リクエストを行うインタフェース

    Returns:
        str: 認可サーバアクセスURL

    Raises:
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合 エラーコード: 010400001E

    """

    authorization_server_url = ''

    try:
        connector_config = internal_interface.config_read(
            __CONFIG_AUTHORIZATION_FILE_PATH)
    except Exception:
        raise CaddeException(
            message_id='010400001E',
            replace_str_list=[__CONFIG_AUTHORIZATION_FILE_PATH])
    try:
        authorization_server_url = connector_config[__CONFIG_AUTHORIZATION_SERVER_URL]
    except Exception:
        pass

    if authorization_server_url.endswith('/'):
        authorization_server_url = authorization_server_url[:-1]

    return authorization_server_url


def __get_authorization_decode(target_token) -> (str):
    """
    リクエストパラメータのトークンをデコードする

    Args:
        target_token : 認証トークン

    Returns:
        str: トークンのデコード情報

    Raises:
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合 エラーコード: 020400002E
    """
    target_arry = {}

    # AuthorizationからURLを取得する
    tmp = target_token.split('.')
    try:
        target_arry = json.loads(base64.urlsafe_b64decode(
            tmp[1] + '=' * (-len(target_token) % 4)).decode())
    except Exception:
        raise CaddeException(
            message_id='010400002E'
        )

    return target_arry


def __get_authorization_url(target_token) -> (str):
    """
    リクエストパラメータのトークンをデコードし、issを取得する

    Args:
        target_token : 認証トークン

    Returns:
        str: トークンのデコード情報

    Raises:
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合 エラーコード: 020400003E
    """
    authentication_url = ''
    target_arry = __get_authorization_decode(target_token)

    if 'iss' not in target_arry:
        raise CaddeException(
            message_id='010400003E'
        )
    iss = target_arry['iss']
    tmp = iss.split('/')
    authentication_url = tmp[0] + '/' + tmp[1] + '/' + tmp[2]

    return authentication_url


def __get_authorization_consumer_id(target_token) -> (str):
    """
    リクエストパラメータのトークンをデコードし、preferred_usernameを取得する

    Args:
        target_token : 認証トークン

    Returns:
        str: CADDEユーザID（利用者）

    Raises:
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合 エラーコード: 020400004E
    """
    consumer_id = ''
    target_arry = __get_authorization_decode(target_token)

    if 'preferred_username' not in target_arry:
        raise CaddeException(
            message_id='010400004E'
        )
    consumer_id = target_arry['preferred_username']

    return consumer_id
