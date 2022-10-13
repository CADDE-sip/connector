import logging
from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import history_confirmation_call
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.utilities.utilities import log_message_none_parameter_replace

logger = logging.getLogger(__name__)
internal_interface = InternalInterface()
external_interface = ExternalInterface()


def lineage(cadde_resource_id_for_provenance, direction=None, depth=None, authorization=None):  # noqa: E501
    """API. 来歴確認

    指定された交換実績記録用リソースIDから始まる来歴情報を取得する。  # noqa: E501

    :param cadde_resource_id_for_provenance: 交換実績記録用リソースID
    :type cadde_resource_id_for_provenance: str
    :param direction: 履歴取得方向 [BACKWARD(&#x3D;default),FORWARD, BOTH]
    :type direction: str
    :param depth: 交換実績記録用リソースIDで指定されたイベントからの深さ. 0は、交換実績記録用リソースIDで指定されたイベントを要求します. 正の整数は、指定されたレコードから指定された深さ以下のである全てのイベントを要求します. -1は、指定されたイベントから到達可能な全てのイベントを要求します.
    :type depth: int
    :param authorization: 認証トークン
    :type authorization: str

    :rtype: CDLEventList
    """

    # 引数のx-direction、x-depthは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    # x-direction、x-depthはyamlファイルでデフォルト値が設定されているが、
    # openapiではデフォルト値が廃止されているため、取得できない場合がある。
    direction = None
    depth = None
    if 'x-cadde-direction' in connexion.request.headers:
        direction = connexion.request.headers['x-cadde-direction']
    if 'x-cadde-depth' in connexion.request.headers:
        depth = int(connexion.request.headers['x-cadde-depth'])
    authorization = connexion.request.headers['Authorization']

    logger.debug(get_message('020302001N',
                             [cadde_resource_id_for_provenance,
                              log_message_none_parameter_replace(direction),
                              log_message_none_parameter_replace(depth)]))

    search_result = history_confirmation_call(
        cadde_resource_id_for_provenance,
        direction,
        depth,
        authorization,
        internal_interface,
        external_interface)
    response_headers = dict(search_result.headers)
    if 'Transfer-Encoding' in response_headers:
        del response_headers['Transfer-Encoding']
    response = Response(
        response=search_result.text,
        headers=response_headers,
        status=200,
        mimetype="application/json")

    return response
