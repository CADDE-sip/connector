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


def received(provider_id=None, consumer_id=None, resource_id_for_provenance=None, provenance_management_service_url=None, authorization=None):  # noqa: E501
    """API. 受信履歴登録

    来歴管理I/Fに対して、受信履歴登録を行い、識別情報を取得する。
    Response:
     * 処理が成功した場合は200を返す
     * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param x-provider-id: CADDEユーザID（提供者）
    :type x-provider-id: str
    :param x-provider-id: CADDEユーザID（利用者）
    :type x-provider-id: str
    :param x-cadde-resource-id-for-provenance: 交換実績記録用リソースID
    :type x-cadde-resource-id-for-provenance: str
    :param x-cadde-provenance-management-service-url: 来歴管理サービスURL
    :type x-cadde-provenance-management-service-url: str
    :param Authorization: 認証トークン
    :type Authorization: str

    :rtype: None
    """

    # 引数のprovider-id、consumer-id、cadde-resource-id-for-provenance、tokenは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。
    provider_id = connexion.request.headers['x-cadde-provider']
    consumer_id = connexion.request.headers['x-cadde-consumer']
    resource_id_for_provenance = connexion.request.headers['x-cadde-resource-id-for-provenance']
    provenance_management_service_url = connexion.request.headers[
        'x-cadde-provenance-management-service-url']
    authorization = connexion.request.headers['Authorization']

    logger.debug(
        get_message(
            '020301001N', [
                provider_id, consumer_id, resource_id_for_provenance, provenance_management_service_url]))

    identification_information = received_history_registration(
        provider_id,
        consumer_id,
        resource_id_for_provenance,
        provenance_management_service_url,
        authorization,
        internal_interface,
        external_interface)

    response = Response(response='', status=200)
    response.headers['x-cadde-provenance'] = identification_information
    return response
