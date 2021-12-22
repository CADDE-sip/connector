
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


def token_federation(authorization=None, consumer_connector_id=None, consumer_connector_secret=None, idp=None):  # noqa: E501
    """API. 認可トークン取得要求

    認証認可サーバに対して、トークンフェデレーションリクエストを行い、認可トークンを返す。

    Response:
      ・処理が成功した場合は200を返す。
      ・処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。

    :param authorization: 利用者トークン
    :type authorization: str
    :param consumer_connector_id: 利用者コネクタID
    :type consumer_connector_id: str
    :param consumer_connector_secret: 利用者コネクタのシークレット
    :type consumer_connector_secret: str
    :param idp: アイデンティティ・プロバイダー
    :type idp: str

    :rtype: None
    """
    # 引数のAuthorization、x-consumer-connector-id、x-consumer-connector-secret、x-idpは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    authorization = connexion.request.headers['Authorization']
    consumer_connector_id = connexion.request.headers['x-consumer-connector-id']
    consumer_connector_secret = connexion.request.headers['x-consumer-connector-secret']
    idp = connexion.request.headers['x-idp']

    logger.debug(
        get_message(
            '1A004N', [
                authorization, consumer_connector_id, consumer_connector_secret, idp]))

    auth_token = token_federation_execute(
        authorization,
        consumer_connector_id,
        consumer_connector_secret,
        idp,
        internal_interface,
        external_interface)

    return_response = Response(response='', status=200)
    return_response.headers['auth-token'] = auth_token
    return return_response
