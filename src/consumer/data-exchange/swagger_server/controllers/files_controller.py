import logging

import connexion
from flask import Response

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import data_exchange
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.utilities import log_message_none_parameter_replace, get_url_file_name

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()


def files(x_cadde_resource_url=None, x_cadde_resource_api_type=None, x_cadde_provider_connector_url=None, Authorization=None, x_cadde_options=None):  # noqa: E501
    """API. データ交換(cadde)

    CADDEインタフェースを用いてファイルを取得する
    Response: * 処理が成功した場合は200を返す * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param x-cadde-resource-url: リソースURL
    :type x-cadde-resource-url: str
    :param x-cadde-resource-api-type: リソース提供手段識別子
    :type x-cadde-resource-api-type: str
    :param x-cadde-provider-connector-url: 提供者コネクタURL
    :type x-cadde-provider-connector-url: str
    :param Authorization: 認可トークン
    :type Authorization: str
    :param x-cadde-options: NGSIオプション("key1:value1,key2:value2・・・"形式)
    :type x-cadde-options: str

    :rtype: None
    """

    # 引数のx-cadde-resource-url、x-cadde-resource-api-type、x-cadde-provider-connector-url、Authorization、x-cadde-optionsは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。

    authorization = None
    options = None

    resource_url = connexion.request.headers['x-cadde-resource-url']
    resource_api_type = connexion.request.headers['x-cadde-resource-api-type']
    provider_connector_url = connexion.request.headers['x-cadde-provider-connector-url']

    if 'Authorization' in connexion.request.headers:
        authorization = connexion.request.headers['Authorization']

    if 'x-cadde-options' in connexion.request.headers:
        options = connexion.request.headers['x-cadde-options']

    logger.debug(get_message('020201001N',
                             [resource_url,
                              resource_api_type,
                              provider_connector_url,
                              log_message_none_parameter_replace(
                                  authorization),
                              log_message_none_parameter_replace(options)]))

    data = data_exchange(
        resource_url,
        resource_api_type,
        provider_connector_url,
        authorization,
        options,
        external_interface)

    response = Response(
        response=data.content,
        headers=dict(data.headers),
        status=200,
        mimetype='application/json')

    if 'Server' in response.headers:
        del response.headers['Server']

    if 'Date' in response.headers:
        del response.headers['Date']

    if 'Transfer-Encoding' in response.headers:
        del response.headers['Transfer-Encoding']

    if 'Content-Disposition' not in response.headers:
        response.headers[
            'Content-Disposition'] = 'attachment; filename=' + get_url_file_name(resource_url)

    return response
