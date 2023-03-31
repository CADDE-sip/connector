# -*- coding: utf-8 -*-

from flask import Response

from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.cadde_exception import CaddeException

__HTTP_STATUS_CODE_SUCCESS_LOWER_LIMIT = 200
__HTTP_STATUS_CODE_SUCCESS_UPPER_LIMIT = 299

__ACCESS_POINT_URL = 'http://provider_connector_main:8080/cadde/api/v4/file'


def data_exchange(
        resource_url: str,
        resoruce_api_type: str,
        authorization: str,
        options: str,
        external_interface: ExternalInterface = ExternalInterface()) -> Response:
    """
    提供者側コネクタメインにGETリクエストを送信し、取得した情報を返す

    Args:
        resource_url str : リソースURL
        resoruce_api_type str : リソース提供手段識別子
        authorization str : トークン情報(認証トークン/None)
        external_interface ExternalInterface : GETリクエストを行うインタフェース
        options str : データ提供IFが使用するカスタムヘッダー

    Returns:
        Response :レスポンス

    Raises:
        Cadde_excption: リクエストに失敗した場合 エラーコード: 010201002E

    """

    headers_dict = {
        'x-cadde-resource-url': resource_url,
        'x-cadde-resource-api-type': resoruce_api_type,
        'Authorization': authorization,
        'x-cadde-options': options}

    response = external_interface.http_get(__ACCESS_POINT_URL, headers_dict)
    if (response.status_code < __HTTP_STATUS_CODE_SUCCESS_LOWER_LIMIT
            or __HTTP_STATUS_CODE_SUCCESS_UPPER_LIMIT < response.status_code):
        raise CaddeException(
            '010201002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    return response
