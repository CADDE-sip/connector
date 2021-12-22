
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


def token_contract(authorization=None, resource_id=None, provider_connector_id=None):  # noqa: E501
    """API. 契約確認要求処理

    認証認可サーバに対して、契約確認をリクエストする。

    :param authorization: 契約トークン/利用者トークン
    :type authorization: str
    :param resource_id: リソースID
    :type resource_id: str
    :param provider_connector_id: 提供者コネクタID
    :type provider_connector_id: str

    :rtype: None
    """
    # 引数のAuthorization、x-resource-id、x-provider-connector-idは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    authorization = connexion.request.headers['Authorization']
    resource_id = connexion.request.headers['x-resource-id']
    provider_connector_id = connexion.request.headers['x-provider-connector-id']

    logger.debug(
        get_message(
            '0A010N', [
                authorization, resource_id, provider_connector_id]))

    access_token = token_contract_execute(
        authorization,
        resource_id,
        provider_connector_id,
        internal_interface,
        external_interface)

    return_response = Response(response='', status=200)
    return return_response
