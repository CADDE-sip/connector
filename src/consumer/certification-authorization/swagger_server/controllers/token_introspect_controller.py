
import logging

from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import token_introspect_execute
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)
internal_interface = InternalInterface()
external_interface = ExternalInterface()


def token_introspect(authorization=None, consumer_connector_id=None, consumer_connector_secret=None):  # noqa: E501
    """API. 認証認可要求

    認証認可サーバに対して、認証認可要求を行い、利用者IDを返す。 Response: * 処理が成功した場合は200を返す * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param authorization: 利用者トークン
    :type authorization: str
    :param consumer_connector_id: 利用者コネクタID
    :type consumer_connector_id: str
    :param consumer_connector_secret: 利用者コネクタのシークレット
    :type consumer_connector_secret: str

    :rtype: None
    """
    # 引数のAuthorization、consumer-connector-id、consumer-connector-secretは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    authorization = connexion.request.headers['Authorization']
    consumer_connector_id = connexion.request.headers['consumer-connector-id']
    consumer_connector_secret = connexion.request.headers['consumer-connector-secret']

    logger.debug(
        get_message(
            '1A001N', [
                authorization, consumer_connector_id, consumer_connector_secret]))

    consumer_id = token_introspect_execute(
        authorization,
        consumer_connector_id,
        consumer_connector_secret,
        internal_interface,
        external_interface)

    return_response = Response(response='', status=200)
    return_response.headers['consumer-id'] = consumer_id
    return return_response
