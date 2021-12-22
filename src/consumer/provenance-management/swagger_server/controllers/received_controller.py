
import logging
from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import received_history_registration
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

logger = logging.getLogger(__name__)
internal_interface = InternalInterface()
external_interface = ExternalInterface()


def received(provider_id=None, consumer_id=None, caddec_resource_id_for_provenance=None, token=None):  # noqa: E501
    """API. 受信履歴登録要求

    来歴管理I/Fに対して、受信履歴登録要求を行い、識別情報を取得する。 Response: * 処理が成功した場合は200を返す * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param x-provider-id: 提供者ID
    :type x-provider-id: str
    :param x-provider-id: 利用者ID
    :type x-provider-id: str
    :param x-caddec-resource-id-for-provenance: 交換実績記録用リソースID
    :type x-caddec-resource-id-for-provenance: str
    :param x-token: 来歴管理者用トークン
    :type x-token: str

    :rtype: None
    """

    # 引数のprovider-id、consumer-id、caddec-resource-id-for-provenance、tokenは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    provider_id = connexion.request.headers['x-cadde-provider']
    consumer_id = connexion.request.headers['x-cadde-consumer']
    caddec_resource_id_for_provenance = connexion.request.headers[
        'x-caddec-resource-id-for-provenance']
    token = connexion.request.headers['x-token']

    logger.debug(
        get_message(
            '19001N', [
                provider_id, consumer_id, caddec_resource_id_for_provenance]))

    identification_information = received_history_registration(
        provider_id,
        consumer_id,
        caddec_resource_id_for_provenance,
        token,
        internal_interface,
        external_interface)

    response = Response(response='', status=200)
    response.headers['x-cadde-provenance'] = identification_information
    return response
