import connexion
from flask import make_response
import logging

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import fetch_data
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.utilities import log_message_none_parameter_replace, get_url_file_name

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()


def files(authorization=None, resource_url=None, resource_api_type=None, provider=None):  # noqa: E501
    """API. データ取得(NGSI以外)

    CADDEインタフェースを用いて、HTTPサーバ、FTPサーバからファイルを取得する

    Response:
     * 処理が成功した場合は200を返す
     * 処理に失敗した場合は、2xx以外のコードを返す。 Responsesセクションを参照。 # noqa: E501

    :param Authorization: 利用者トークン
    :type Authorization: str
    :param resource_url: リソースURL
    :type resource_url: str
    :param resource_api_type: リソース提供手段識別子
    :type resource_api_type: str
    :param provider: CADDEユーザID（提供者）
    :type provider: str

    :rtype: None
    """
    # 引数のx-cadde-resource-url、x-cadde-resource-api-type、x-cadde-provider、Authorizationは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    resource_url = connexion.request.headers['x-cadde-resource-url']
    resource_api_type = connexion.request.headers['x-cadde-resource-api-type']

    provider = None
    authorization = None

    if 'x-cadde-provider' in connexion.request.headers:
        provider = connexion.request.headers['x-cadde-provider']
    if 'Authorization' in connexion.request.headers:
        authorization = connexion.request.headers['Authorization']

    logger.debug(get_message('020002001N',
                             [resource_url,
                              resource_api_type,
                              log_message_none_parameter_replace(provider),
                              log_message_none_parameter_replace(authorization)]))

    data, headers = fetch_data(
        authorization,
        resource_url,
        resource_api_type,
        provider,
        None,
        external_interface)

    response = make_response(data.read(), 200)
    response.headers = headers
    response.headers['Content-Disposition'] = 'attachment; filename=' + \
        get_url_file_name(resource_url)

    if 'Server' in response.headers:
        del response.headers['Server']

    if 'Date' in response.headers:
        del response.headers['Date']

    if 'Transfer-Encoding' in response.headers:
        del response.headers['Transfer-Encoding']

    return response
