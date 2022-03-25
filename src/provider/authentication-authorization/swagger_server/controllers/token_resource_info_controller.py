
import logging

from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import token_resource_info_execute
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)

internal_interface = InternalInterface()
external_interface = ExternalInterface()


def token_resource_info(authorization=None, resource_id=None):  # noqa: E501
    """API. リソース情報取得要求

    認証認可サーバに対して、リソース情報取得をリクエストし、リソース情報を取得する。

    :param authorization: APIトークン
    :type authorization: str
    :param resource_id: リソースID
    :type resource_id: str

    :rtype: None
    """
    # 引数のAuthorization、x-resource-idは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    authorization = connexion.request.headers['Authorization']
    resource_id = connexion.request.headers['x-resource-id']

    logger.debug(
        get_message(
            '0A013N', [
                authorization, resource_id]))

    attributes = token_resource_info_execute(
        authorization,
        resource_id,
        internal_interface,
        external_interface)

    return_response = Response(response='', status=200)
    return_response.headers['attributes'] = attributes
    return return_response
