import connexion

from flask import send_file, Response
import logging
from io import BytesIO

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import data_exchange
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.utilities import log_message_none_parameter_replace, get_url_file_name

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()


def files(x_cadde_resource_url=None, x_cadde_resource_api_type=None, Authorization=None, x_cadde_options=None):  # noqa: E501
    """API. ファイル取得(cadde)

    CADDEインタフェースを用いてファイルを取得する

    Response:
     * 処理が成功した場合は200を返す
     * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param x-cadde-resource-url: リソースURL
    :type x-cadde-resource-url: str
    :param x-cadde-resource-api-type: リソース提供手段識別子
    :type x-cadde-resource-api-type: str
    :param Authorization: 認可トークン
    :type Authorization: str
    :param x-cadde-options: データ提供IFが使用するカスタムヘッダー("key1:value1,key2:value2・・・"形式)
    :type x-cadde-options: str

    :rtype: None
    """

    # 引数のx-cadde-resource-url、x-cadde-resource-api-type、Authorization、x-cadde-optionsは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。

    authorization = None
    options = None

    resource_url = connexion.request.headers['x-cadde-resource-url']
    resource_api_type = connexion.request.headers['x-cadde-resource-api-type']

    if 'Authorization' in connexion.request.headers:
        authorization = connexion.request.headers['Authorization']

    if 'x-cadde-options' in connexion.request.headers:
        options = connexion.request.headers['x-cadde-options']

    logger.debug(get_message('010201001N',
                             [resource_url,
                              resource_api_type,
                              log_message_none_parameter_replace(
                                  authorization),
                              log_message_none_parameter_replace(options)]))

    response = data_exchange(
        resource_url,
        resource_api_type,
        authorization,
        options,
        external_interface)

    if resource_api_type == 'api/ngsi':
        ngsi_headers = dict(response.headers)
        return_response = Response(
            response=response.content,
            headers=ngsi_headers,
            status=200,
            mimetype="application/json")

    else:
        cadde_headers = dict(response.headers)
        fileName = get_url_file_name(resource_url)
        return_response = send_file(
            BytesIO(
                response.content),
            as_attachment=True,
            download_name=fileName)
        return_response.headers = cadde_headers

    check_headers = dict(response.headers)

    if 'x-cadde-provenance' in check_headers:
        return_response.headers['x-cadde-provenance'] = check_headers['x-cadde-provenance']
    else:
        return_response.headers['x-cadde-provenance'] = ''

    if 'x-cadde-provenance-management-service-url' in check_headers:
        return_response.headers[
            'x-cadde-provenance-management-service-url'
        ] = check_headers['x-cadde-provenance-management-service-url']
    else:
        return_response.headers['x-cadde-provenance-management-service-url'] = ''

    if 'x-cadde-contract-id' in check_headers:
        return_response.headers['x-cadde-contract-id'] = check_headers['x-cadde-contract-id']
    else:
        return_response.headers['x-cadde-contract-id'] = ''

    if 'x-cadde-contract-type' in check_headers:
        return_response.headers['x-cadde-contract-type'] = check_headers['x-cadde-contract-type']
    else:
        return_response.headers['x-cadde-contract-type'] = ''

    if 'x-cadde-contract-management-service-url' in check_headers:
        return_response.headers[
            'x-cadde-contract-management-service-url'
        ] = check_headers['x-cadde-contract-management-service-url']
    else:
        return_response.headers['x-cadde-contract-management-service-url'] = ''

    return_response.headers['X-Content-Type-Options'] = 'nosniff'
    return_response.headers['X-XSS-Protection'] = '1; mode=block'
    return_response.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'self'"
    return_response.headers['Referrer-Policy'] = "no-referrer always"

    return return_response
