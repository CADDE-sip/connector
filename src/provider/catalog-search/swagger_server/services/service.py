# -*- coding: utf-8 -*-
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.cadde_exception import CaddeException

__ACCESS_POINT_URL = 'http://provider_connector_main:8080/cadde/api/v4/catalog'


def search_catalog_ckan(
        query_string: str,
        auth_token: str,
        external_interface: ExternalInterface) -> str:
    """
    コネクタメインに詳細検索を送信する

    Args:
        query_string str : 検索条件のクエリストリング
        auth_token str : HTTPリクエストヘッダとしての認証トークン
        external_interface ExternalInterface :  コネクタ外部とのインタフェース

    Returns:
        str : 取得したデータ文字列

    Raises:
        Cadde_excption : ステータスコード200 OKでない場合 エラーコード : 010101002E

    """

    response = external_interface.http_get(
        __ACCESS_POINT_URL + query_string, {'Authorization': auth_token})

    if response.status_code != 200:
        raise CaddeException(
            message_id='010101002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])
    else:
        return response.text
