import connexion

from flask import send_file
import logging

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import fetch_data
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.utilities import log_message_none_parameter_replace, get_url_file_name

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()


def files(x_cadde_resource_url=None, x_cadde_resource_api_type=None, x_cadde_contract=None, x_cadde_provider=None, Authorization=None):  # noqa: E501
    """API.02 データ取得(NGSI以外)

    CADDEインタフェースを用いて、HTTPサーバ、FTPサーバからファイルを取得する Response: * 処理が成功した場合は200を返す * 処理に失敗した場合は、2xx以外のコードを返す。 Responsesセクションを参照。 # noqa: E501

    :param x-cadde-resource-url: リソースURL
    :type x-cadde-resource-url: str
    :param x-cadde-resource-api-type: リソース提供手段識別子
    :type x-cadde-resource-api-type: str
    :param x-cadde-contract: 契約確認要否
    :type x-cadde-contract: str
    :param x-cadde-provider: 提供者ID
    :type x-cadde-provider: str
    :param Authorization: 利用者トークン
    :type Authorization: str

    :rtype: None
    """
    # 引数のx-cadde-resource-url、x-cadde-resource-api-type、x-cadde-contract、x-cadde-provider、Authorizationは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    resource_url = connexion.request.headers['x-cadde-resource-url']
    resource_api_type = connexion.request.headers['x-cadde-resource-api-type']
    contract = connexion.request.headers['x-cadde-contract']

    provider = None
    authorization = None

    if 'x-cadde-provider' in connexion.request.headers:
        provider = connexion.request.headers['x-cadde-provider']
    if 'Authorization' in connexion.request.headers:
        authorization = connexion.request.headers['Authorization']

    logger.debug(get_message('14001N',
                             [resource_url,
                              resource_api_type,
                              log_message_none_parameter_replace(provider),
                              contract,
                              log_message_none_parameter_replace(authorization)]))

    response_bytes, headers_dict = fetch_data(
        resource_url, resource_api_type, provider, contract, authorization, None, external_interface)

    fileName = get_url_file_name(resource_url)
    
    response = send_file(response_bytes, as_attachment=True,attachment_filename=fileName)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'self'"
    return response, 200

