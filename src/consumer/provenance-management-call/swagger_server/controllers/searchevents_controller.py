import logging
from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import history_id_search_call
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)
internal_interface = InternalInterface()
external_interface = ExternalInterface()


def searchevents(body=None):  # noqa: E501
    """API. 履歴ID検索呼び出し

    ボディ部に設定した検索条件を基に履歴情報を取得する。 ヘッダに&#x60;content-type: application/json&#x60; を追加してください.  # noqa: E501

    :param body: CouchDBの構文です. 右記を参照してください。 https://docs.couchdb.org/en/stable/api/database/find.html#find-selectors

    :type body: dict | bytes

    :rtype: CDLEventList
    """
    if connexion.request.is_json:
        #    body = Body.from_dict(connexion.request.get_json())  # noqa: E501
        body = connexion.request.get_json()

    logger.debug(get_message('1E001N', [body]))

    search_result = history_id_search_call(body, internal_interface, external_interface)
    response_headers = dict(search_result.headers)
    if 'Transfer-Encoding' in response_headers:
        del response_headers['Transfer-Encoding']
    response = Response(
        response=search_result.text,
        headers=response_headers,
        status=200,
        mimetype="application/json")

    return response
