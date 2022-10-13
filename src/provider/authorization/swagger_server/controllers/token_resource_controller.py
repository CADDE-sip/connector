
import logging

from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import token_resource_execute
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)

internal_interface = InternalInterface()
external_interface = ExternalInterface()


def token_resource(authorization=None, resource_url=None):  # noqa: E501
    """API. リソースID取得要求

    認証認可サーバに対して、リソースURLチェックをリクエストし、リソースIDを取得する。

    Response:
      ・処理が成功した場合は200を返す。
      ・処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。

    :param authorization: PATトークン
    :type authorization: str
    :param resource_url: リソースURL
    :type resource_url: str

    :rtype: None
    """
    # 引数のAuthorization、x-resource-urlは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    authorization = connexion.request.headers['Authorization']
    resource_url = connexion.request.headers['x-resource-url']

    logger.debug(
        get_message(
            '0A008N', [
                authorization, resource_url]))

    resource_id = token_resource_execute(
        authorization,
        resource_url,
        internal_interface,
        external_interface)

    return_response = Response(response='', status=200)
    return_response.headers['resource-id'] = resource_id
    return return_response
