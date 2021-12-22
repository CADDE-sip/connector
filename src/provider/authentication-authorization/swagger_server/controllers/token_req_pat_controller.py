
import logging

from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import token_req_pat_execute
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)

internal_interface = InternalInterface()
external_interface = ExternalInterface()


def token_req_pat(provider_connector_id=None, provider_connector_secret=None):  # noqa: E501
    """API. APIトークン取得要求

    認証認可サーバに対して、APIトークンをリクエストし、APIトークンを取得する。

    Response:
      ・処理が成功した場合は200を返す。
      ・処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。

    :param provider_connector_id: 提供者コネクタID
    :type provider_connector_id: str
    :param provider_connector_secret: 提供者コネクタのシークレット
    :type provider_connector_secret: str

    :rtype: None
    """
    # 引数のprovider-connector-id、provider-connector-secretは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    provider_connector_id = connexion.request.headers['x-provider-connector-id']
    provider_connector_secret = connexion.request.headers['x-provider-connector-secret']

    logger.debug(
        get_message(
            '0A006N', [
                provider_connector_id, provider_connector_secret]))

    api_token = token_req_pat_execute(
        provider_connector_id,
        provider_connector_secret,
        internal_interface,
        external_interface)

    return_response = Response(response='', status=200)
    return_response.headers['api-token'] = api_token
    return return_response
