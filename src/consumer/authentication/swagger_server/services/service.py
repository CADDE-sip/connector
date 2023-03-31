# -*- coding: utf-8 -*-
import json
import base64

from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface


__CONFIG_AUTHENTICATION_FILE_PATH = '/usr/src/app/swagger_server/configs/authentication.json'
__CONFIG_AUTHENTICATION_SERVER_URL = 'authentication_server_url'

__CADDE_INTROSPECT = '/cadde/api/v4/token/introspect'


def token_introspect_execute(
        authorization: str,
        consumer_connector_id: str,
        consumer_connector_secret: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認証トークン検証を行い、CADDEユーザID(利用者)を返す。

    Args:
        authorization str : 利用者トークン
        consumer_connector_id str : 利用者コネクタID
        consumer_connector_secret str : 利用者コネクタシークレットのID
        internal_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str : CADDEユーザID（利用者）

    Raises:
        Cadde_excption : ステータスコード2xxでない場合 エラーコード : 020402002E
        Cadde_excption : 利用者トークンが有効でなかった場合 エラーコード : 020402003E
        Cadde_excption : 利用者トークンが有効でなかった場合 エラーコード : 020402004E
        Cadde_excption : 利用者トークンが有効でなかった場合 エラーコード : 020402005E

    """

    # コンフィグファイルから認証サーバのURL取得
    authentication_server_url = __get_authentication_url(authorization[7:])

    # Authorizationにセットする情報をBase64エンコードする
    credential = f'{consumer_connector_id}:{consumer_connector_secret}'
    bearer = base64.b64encode(credential.encode()).decode()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {bearer}'
    }

    # 引数からpost通信のbody部に指定する情報をdict型で作成
    post_body = {
        'access_token': authorization[7:]
    }

    # アクセスURLの生成
    access_url = authentication_server_url + __CADDE_INTROSPECT

    # リクエスト実行
    response = external_interface.http_post(
        access_url, headers, post_body)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='020402002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    response_text_dict = json.loads(response.text)

    if 'user_id' not in response_text_dict or not response_text_dict['user_id']:
        raise CaddeException(message_id='020402003E')

    consumer_id = response_text_dict['user_id']

    return consumer_id


def __get_authentication_url(target_token) -> (str):
    """
    リクエストパラメータのトークンをデコードし、issに記載されているURLから認証サーバのURLを取得する

    Args:
        target_token : 利用者トークン

    Returns:
        str: 認可サーバアクセスURL

    Raises:
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合 エラーコード: 020400001E
        Cadde_excption: コンフィグファイルの読み込みに失敗した場合 エラーコード: 020400002E
    """
    target_arry = {}
    authentication_url = ''

    # AuthorizationからURLを取得する
    tmp = target_token.split('.')
    try:
        target_arry = json.loads(base64.urlsafe_b64decode(
            tmp[1] + '=' * (-len(target_token) % 4)).decode())
    except Exception:
        raise CaddeException(
            message_id='020400001E'
        )

    if 'iss' not in target_arry:
        raise CaddeException(
            message_id='020400002E'
        )
    iss = target_arry['iss']
    tmp = iss.split('/')
    authentication_url = tmp[0] + '/' + tmp[1] + '/' + tmp[2]

    return authentication_url
