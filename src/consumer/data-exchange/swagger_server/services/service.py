# -*- coding: utf-8 -*-
from flask import Response

from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface

__HTTP_STATUS_CODE_SUCCESS_LOWER_LIMIT = 200
__HTTP_STATUS_CODE_SUCCESS_UPPER_LIMIT = 299
__SET_EXCHANGE_URL = '/cadde/api/v4/file'


def data_exchange(
        resource_url: str,
        resource_api_type: str,
        provider_connector_url: str,
        authorization: str,
        options: str,
        external_interface: ExternalInterface = ExternalInterface()) -> Response:
    """
    提供者側コネクタにデータ交換を行い、取得した情報を返す

    Args:
        resource_url str : リソースURL
        resource_api_type str : リソース提供手段識別子
        provider_connector_url str : 提供者コネクタURL
        authorization str : 認証トークン
        options str : データ提供IFが使用するカスタムヘッダー
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        Response :レスポンス

    Raises:
        Cadde_excption: リスエストのステータスコードが2xxでない場合 エラーコード: 020201002E

    """

    headers_dict = {
        'x-cadde-resource-url': resource_url,
        'x-cadde-resource-api-type': resource_api_type,
        'Authorization': authorization,
        'x-cadde-options': options}

    data_exchange_url = provider_connector_url + __SET_EXCHANGE_URL

    response = external_interface.http_get(
        data_exchange_url, headers_dict)
    if (response.status_code < __HTTP_STATUS_CODE_SUCCESS_LOWER_LIMIT
            or __HTTP_STATUS_CODE_SUCCESS_UPPER_LIMIT < response.status_code):
        raise CaddeException(
            '020201002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    return response
