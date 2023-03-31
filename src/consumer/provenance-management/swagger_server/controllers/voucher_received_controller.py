import logging
from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import voucher_received_call
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()


def voucher_received(cadde_provider=None, cadde_consumer=None, cadde_contract_id=None, hash_get_data=None, contract_management_service_url=None, Authorization=None):  # noqa: E501
    """API. データ証憑通知（受信）

    来歴管理I/Fにデータ証憑通知（受信）を依頼する。
     Response:
     * 処理が成功した場合は200を返す
     * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param cadde_provider: CADDEユーザID（提供者）
    :type cadde_provider: str
    :param cadde_consumer: CADDEユーザID（利用者）
    :type cadde_consumer: str
    :param cadde_contract_id:取引ID
    :type cadde_contract_id: str
    :param hash_get_data: ハッシュ値
    :type hash_get_data: str
    :param contract_management_service_url: 契約管理サービスURL
    :type contract_management_service_url: str
    :param Authorization: 認証トークン
    :type Authorization: str

    :rtype: None
    """

    # 引数のx-cadde-provider、x-cadde-consumer、x-cadde-contract-id、x-hash-get-data、x-cadde-contract-management-service-url、x-cadde-contract-management-keyは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。

    cadde_provider = connexion.request.headers['x-cadde-provider']
    cadde_consumer = connexion.request.headers['x-cadde-consumer']
    cadde_contract_id = connexion.request.headers['x-cadde-contract-id']
    hash_get_data = connexion.request.headers['x-cadde-hash-get-data']
    contract_management_service_url = connexion.request.headers[
        'x-cadde-contract-management-service-url']
    authorization = connexion.request.headers['Authorization']

    logger.debug(
        get_message(
            '020302001N', [
                cadde_provider, cadde_consumer, cadde_contract_id, hash_get_data,
                contract_management_service_url, authorization]))

    voucher_result = voucher_received_call(
        cadde_provider,
        cadde_consumer,
        cadde_contract_id,
        hash_get_data,
        contract_management_service_url,
        authorization,
        external_interface)

    response = Response(response='', status=200)
    return response
