import connexion
import logging
import urllib.parse

from flask import Response
from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import catalog_search
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.utilities import log_message_none_parameter_replace

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()


def search(q=None, search=None, provider=None, authorization=None):  # noqa: E501
    """API. カタログ検索

    提供者カタログサイトからCKANカタログ情報を取得する.

    Response:
     * 処理が成功した場合は200を返す
     * 処理に失敗した場合は、2xx以外のコードを返す。 Responsesセクション参照。 # noqa: E501

    :param q: CKAN検索条件クエリ CKAN APIに準拠
    :type q: str
    :param search: 横断検索、詳細検索を指定する(横断検索:meta, 詳細検索:detail)
    :type search: str
    :param provider: CADDEユーザID（提供者）
    :type provider: str
    :param authorization: 利用者トークン
    :type authorization: str

    :rtype: None

    """
    # 引数のx-cadde-search, x-cadde-provider, x-idp-url, Authorizationはconnexionの仕様上取得できないため、
    # ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。

    query_string = '?'
    for key in connexion.request.args.keys():
        query_string += key + "=" + \
            urllib.parse.quote(connexion.request.args[key]) + "&"
    query_string = query_string[:-1]

    search = connexion.request.headers['x-cadde-search']
    provider = None
    authorization = None

    if 'x-cadde-provider' in connexion.request.headers:
        provider = connexion.request.headers['x-cadde-provider']
    if 'Authorization' in connexion.request.headers:
        authorization = connexion.request.headers['Authorization']

    logger.debug(get_message('020001001N', [query_string, log_message_none_parameter_replace(
        provider), log_message_none_parameter_replace(authorization), search]))

    data = catalog_search(
        query_string,
        search,
        provider,
        authorization,
        external_interface)

    response = Response(
        response=data.text,
        status=200,
        mimetype="application/json")

    if 'Server' in response.headers:
        del response.headers['Server']

    if 'Date' in response.headers:
        del response.headers['Date']

    if 'Transfer-Encoding' in response.headers:
        del response.headers['Transfer-Encoding']

    return response
