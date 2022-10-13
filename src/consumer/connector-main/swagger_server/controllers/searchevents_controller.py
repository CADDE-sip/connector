import logging
from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import history_id_search_call
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()


def searchevents(authorization=None, body=None):  # noqa: E501
    """API. 履歴ID検索

    ボディ部に設定した検索条件を基に履歴情報を取得する。 ヘッダに&#x60;content-type: application/json&#x60; を追加してください.  # noqa: E501

    :param authorization: 利用者トークン
    :type authorization: str
    :param body: CouchDBの構文です. 右記を参照してください。 https://docs.couchdb.org/en/stable/api/database/find.html#find-selectors
    :type body: dict | bytes

    :rtype: CDLEventList

    """

    authorization = connexion.request.headers['Authorization']

    if connexion.request.is_json:
        body = connexion.request.get_json()

    logger.debug(get_message('020006001N', [body]))

    search_result = history_id_search_call(
        authorization,
        body,
        external_interface)
    response_headers = dict(search_result.headers)
    response = Response(
        response=search_result.text,
        headers=response_headers,
        status=200,
        mimetype="application/json")

    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'self'"
    response.headers['Referrer-Policy'] = "no-referrer always"

    return response
