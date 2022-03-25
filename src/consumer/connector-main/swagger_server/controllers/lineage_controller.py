import logging
from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import history_confirmation_call
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.utilities import log_message_none_parameter_replace

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()


def lineage(x_caddec_resource_id_for_provenance=None, x_direction=None, x_depth=None):  # noqa: E501
    """API. 来歴確認呼び出し

    指定された交換実績記録用リソースIDから始まる来歴情報を取得する。  # noqa: E501

    :param caddec_resource_id_for_provenance: 交換実績記録用リソースID
    :type caddec_resource_id_for_provenance: str
    :param direction: 履歴取得方向 [BACKWARD(&#x3D;default),FORWARD, BOTH]
    :type direction: str
    :param depth: 交換実績記録用リソースIDで指定されたイベントからの深さ. 0は、交換実績記録用リソースIDで指定されたイベントを要求します. 正の整数は、指定されたレコードから指定された深さ以下のである全てのイベントを要求します. -1は、指定されたイベントから到達可能な全てのイベントを要求します.
    :type depth: int

    :rtype: CDLEventList
    """
    # 引数のdirection、depthは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    # direction、depthはyamlファイルでデフォルト値が設定されているが、
    # openapiではデフォルト値が廃止されているため、取得できない場合がある。
    caddec_resource_id_for_provenance = connexion.request.headers['x-caddec-resource-id-for-provenance']
    direction = None
    depth = None
    if 'x-direction' in connexion.request.headers:
        direction = connexion.request.headers['x-direction']
    if 'x-depth' in connexion.request.headers:
        depth = connexion.request.headers['x-depth']

    logger.debug(get_message('1B001N',
                             [caddec_resource_id_for_provenance,
                              log_message_none_parameter_replace(direction),
                              log_message_none_parameter_replace(depth)]))

    search_result = history_confirmation_call(
        caddec_resource_id_for_provenance,
        direction,
        depth,
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
