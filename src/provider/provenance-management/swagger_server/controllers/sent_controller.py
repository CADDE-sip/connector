import logging
from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import sent_history_registration
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

logger = logging.getLogger(__name__)
internal_interface = InternalInterface()
external_interface = ExternalInterface()


def sent(provider_id=None, consumer_id=None, cadde_resource_id_for_provenance=None, Authorization=None):  # noqa: E501
    """API. 送信履歴登録

    来歴管理I/Fに対して、送信履歴登録を行い、識別情報を取得する。 Response: * 処理が成功した場合は200を返す * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param provider_id: CADDEユーザID（提供者）
    :type provider_id: str
    :param consumer_id: CADDEユーザID（利用者）
    :type consumer_id: str
    :param cadde_resource_id_for_provenance: 交換実績記録用リソースID
    :type cadde_resource_id_for_provenance: str
    :param Authorization: 認証トークン
    :type Authorization: str

    :rtype: None
    """

    # 引数のx-provider-id、x-cadde-consumer、x-cadde-resource-id-for-provenanceは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。

    provider_id = connexion.request.headers['x-cadde-provider']
    consumer_id = connexion.request.headers['x-cadde-consumer']
    cadde_resource_id_for_provenance = connexion.request.headers[
        'x-cadde-resource-id-for-provenance']
    authorization = connexion.request.headers['Authorization']

    logger.debug(
        get_message(
            '010301001N', [
                provider_id, consumer_id, cadde_resource_id_for_provenance]))

    identification_information, server_url = sent_history_registration(
        provider_id,
        consumer_id,
        cadde_resource_id_for_provenance,
        authorization,
        internal_interface,
        external_interface)

    response = Response(response='', status=200)
    response.headers['x-cadde-provenance'] = identification_information
    response.headers['x-cadde-provenance-management-service-url'] = server_url
    return response
