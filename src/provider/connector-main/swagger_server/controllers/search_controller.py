import connexion

import logging

from flask import Response
from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import detail_search
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.utilities.utilities import log_message_none_parameter_replace

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()
internal_interface = InternalInterface()


def search(q=None, Authorization=None):  # noqa: E501
    """API. カタログ検索(詳細検索)

    提供者カタログサイトからCKANカタログ情報を取得する. Response: * 処理が成功した場合は200を返す * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param q: CKAN検索条件クエリ CKAN APIに準拠
    :type q: str
    :param Authorization: 認証トークン
    :type Authorization: str

    :rtype: None
    """

    # 引数のAuthorizationはconnexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。

    query_string = "?"
    for key in connexion.request.args.keys():
        query_string += key + "=" + connexion.request.args[key] + "&"
    query_string = query_string[:-1]

    authorization = None
    if 'Authorization' in connexion.request.headers:
        authorization = connexion.request.headers['Authorization']

    logger.debug(
        get_message(
            '010001001N', [
                query_string, log_message_none_parameter_replace(authorization)]))

    data = detail_search(
        query_string,
        authorization,
        external_interface,
        internal_interface)

    response = Response(
        response=data,
        status=200,
        mimetype='application/json')

    return response
