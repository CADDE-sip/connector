import logging

from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import search_catalog_meta, search_catalog_detail
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.utilities import log_message_none_parameter_replace

logger = logging.getLogger(__name__)
internal_interface = InternalInterface()
external_interface = ExternalInterface()


def search(q=None, x_cadde_search=None, x_cadde_provider_connector_url=None, Authorization=None):  # noqa: E501
    """API. カタログ検索

    横断検索、詳細検索を判定し、 横断検索サイトまたは提供者カタログサイトからカタログ情報を取得する Response: * 処理が成功した場合は200を返す * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param q: CKAN検索条件クエリ CKAN APIに準拠
    :type q: str
    :param x-cadde-search: 横断検索、詳細検索を指定する(横断検索:meta、詳細検索:detail)
    :type x-cadde-search: str
    :param x-cadde-provider-connector-url: 提供者コネクタURL
    :type x-cadde-provider-connector-url: str
    :param Authorization: 認証トークン
    :type Authorization: str

    :rtype: None
    """
    query_string = "?"
    for key in connexion.request.args.keys():
        query_string += key + "=" + connexion.request.args[key] + "&"
    query_string = query_string[:-1]

    search = connexion.request.headers['x-cadde-search']

    if search == 'meta':
        logger.debug(get_message('020101001N', [query_string, search]))

        data = search_catalog_meta(
            query_string, internal_interface, external_interface)

    else:
        if 'x-cadde-provider-connector-url' in connexion.request.headers:
            provider_connector_url = connexion.request.headers['x-cadde-provider-connector-url']
        else:
            raise CaddeException(message_id='020101002E')

        authorization = None
        if 'Authorization' in connexion.request.headers:
            authorization = connexion.request.headers['Authorization']

        logger.debug(get_message('020101003N', [query_string, log_message_none_parameter_replace(
            provider_connector_url), log_message_none_parameter_replace(authorization), search]))

        data = search_catalog_detail(
            query_string,
            provider_connector_url,
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
