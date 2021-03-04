# -*- coding: utf-8 -*-
import json

from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

__CONFIG_AUTHENTICATION_FILE_PATH = '/usr/src/app/swagger_server/configs/authentication.json'
__CONFIG_AUTHENTICATION_SERVER_URL = 'authentication_server_url'


def token_introspect_execute(
        authorization: str,
        consumer_connector_id: str,
        consumer_connector_secret: str,
        internal_interface: InternalInterface = InternalInterface(),
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    認証認可要求を行い、利用者IDを返す。

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
    except Exception:
        raise CaddeException(
            message_id='00002E',
            status_code=500,
            replace_str_list=[__CONFIG_AUTHENTICATION_SERVER_URL])

    # 引数からpost通信のbody部に指定する情報をdict型で作成

    post_body = {
        'client_id': consumer_connector_id,
        'client_secret': consumer_connector_secret,
        'token': authorization}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = external_interface.http_post(
        authentication_server_url, headers, post_body)

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
