
import logging

from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import token_contract_execute
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)

internal_interface = InternalInterface()
external_interface = ExternalInterface()


def token_contract(authorization=None, cadde_provider=None, provider_connector_id=None, provider_connector_secret=None, resource_url=None):  # noqa: E501
    """API. 認可確認

    認可サーバに対して、契約確認をリクエストする。

    :param authorization: 認可トークン
    :type authorization: str
    :param provider_connector_id: 提供者コネクタID
    :type provider_connector_id: str
    :param provider_connector_secret: 提供者コネクタのシークレット
    :type provider_connector_secret: str
    :param resource_url: リソースURL
    :type resource_id: str

    :rtype: None
    """
    # 引数のAuthorization、x-resource-id、x-provider-connector-idは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    authorization = connexion.request.headers['Authorization']
    cadde_provider = connexion.request.headers['x-cadde-provider']
    provider_connector_id = connexion.request.headers['x-cadde-provider-connector-id']
    provider_connector_secret = connexion.request.headers['x-cadde-provider-connector-secret']
    resource_url = connexion.request.headers['x-cadde-resource-url']

    logger.debug(
        get_message(
            '010403001N', [
                authorization, cadde_provider, provider_connector_id, provider_connector_secret, resource_url]))

    contract_id, contract_type, contract_url = token_contract_execute(
        authorization,
        cadde_provider,
        provider_connector_id,
        provider_connector_secret,
        resource_url,
        internal_interface,
        external_interface)

    return_response = Response(response='', status=200)

    return_response.headers['x-cadde-contract-id'] = contract_id
    return_response.headers['x-cadde-contract-type'] = contract_type
    return_response.headers['x-cadde-contract-management-service-url'] = contract_url

    return return_response
