import logging

from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import token_federation_execute
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)

internal_interface = InternalInterface()
external_interface = ExternalInterface()


def token_federation(authorization=None, cadde_provider=None, provider_connector_id=None, provider_connector_secret=None):  # noqa: E501
    """API. 認可トークン取得

    認可サーバに対して、リソース情報をリクエストし、リソース情報を取得する。

    Response:
      ・処理が成功した場合は200を返す。
      ・処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。

    :param authorization: 認証トークン
    :type authorization: str
    :param provider_connector_id: 提供者コネクタID
    :type provider_connector_id: str
    :param provider_connector_secret: 提供者コネクタのシークレット
    :type provider_connector_secret: str

    :rtype: None
    """
    # 引数のAuthorization、x-provider-connector-id、x-provider-connector-secretは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    authorization = connexion.request.headers['Authorization']
    cadde_provider = connexion.request.headers['x-cadde-provider']
    provider_connector_id = connexion.request.headers['x-cadde-provider-connector-id']
    provider_connector_secret = connexion.request.headers['x-cadde-provider-connector-secret']

    logger.debug(
        get_message(
            '010401001N', [
                authorization, cadde_provider, provider_connector_id, provider_connector_secret]))

    auth_token, consumer_id = token_federation_execute(
        authorization,
        cadde_provider,
        provider_connector_id,
        provider_connector_secret,
        internal_interface,
        external_interface)

    return_response = Response(response='', status=200)
    return_response.headers['x-cadde-auth-token'] = auth_token
    return_response.headers['x-cadde-consumer-id'] = consumer_id

    return return_response
