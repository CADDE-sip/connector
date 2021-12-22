
import logging
from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import voucher_received_call
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()


def voucher_received(provider_id=None, consumer_id=None, contract_id=None, hash_get_data=None, contract_management_service_url=None):  # noqa: E501
    """API. データ証憑通知（受信）

    来歴管理I/Fにデータ証憑通知（受信）を依頼する。
     Response: 
     * 処理が成功した場合は200を返す 
     * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param provider_id: CADDEユーザID（提供者）
    :type provider_id: str
    :param consumer_id: CADDEユーザID（利用者）
    :type consumer_id: str
    :param contract_id:取引ID
    :type contract_id: str
    :param hash_get_data: ハッシュ値
    :type hash_get_data: str
    :param contract_management_service_url: 契約管理サービスURL
    :type contract_management_service_url: str

    :rtype: None
    """

    # 引数のx-cadde-provider、x-cadde-consumer、x-cadde-contract-id、x-hash-get-data、x-cadde-contact-management-urlは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。

    # TODO 契約管理サービスのIF仕様に応じて変更予定
    provider_id = connexion.request.headers['x-cadde-provider']
    # provider_connector_id = connexion.request.headers['x-cadde-provider-connector-id'],
    consumer_id = connexion.request.headers['x-cadde-consumer']
    # consumer_connector_id = connexion.request.headers['x-cadde-consumer-connector-id'],
    contract_id = connexion.request.headers['x-cadde-contract-id']
    hash_get_data = connexion.request.headers['x-hash-get-data']
    contract_management_service_url = connexion.request.headers['x-cadde-contact-management-url']

    logger.debug(
        get_message(
            '1F001N', [
                provider_id, consumer_id, contract_id, hash_get_data, contract_management_service_url]))

    voucher_result = voucher_received_call(
        cadde_consumer,
        trade_id,
        hash_get_data,
        contact_management_url,
        external_interface)

    response = Response(response='', status=200)
    return response
