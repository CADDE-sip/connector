
import logging
from flask import Response
import connexion

from swagger_server.utilities.message_map import get_message
from swagger_server.services.service import voucher_sent_call
from swagger_server.utilities.external_interface import ExternalInterface

logger = logging.getLogger(__name__)
external_interface = ExternalInterface()


def voucher_sent(cadde_provider_id=None, cadde_consumer_id=None, cadde_contract_id=None, cadde_hash_get_data=None, cadde_contract_management_url=None, Authorization=None):  # noqa: E501
    """API. データ証憑通知（送信）

    来歴管理I/Fにデータ証憑通知（送信）を依頼する。
     Response:
     * 処理が成功した場合は200を返す
     * 処理に失敗した場合は、2xx以外を返す。Responsesセクション参照。 # noqa: E501

    :param cadde_provider_id: CADDEユーザID（提供者）
    :type cadde_provider_id: str
    :param cadde_consumer_id: CADDEユーザID（利用者）
    :type cadde_consumer_id: str
    :param cadde_contract_id:取引ID
    :type cadde_contract_id: str
    :param cadde_hash_get_data: ハッシュ値
    :type cadde_hash_get_data: str
    :param cadde_contract_management_url: 契約管理サービスURL
    :type cadde_contract_management_url: str
    :param Authorization: 認証トークン
    :type Authorization: str

    :rtype: None
    """

    # 引数のx-cadde-provider、x-cadde-consumer、x-cadde-contract-id、x-cadde-hash-get-data、x-cadde-contract-management-service-url、Authorizationは
    # connexionの仕様上取得できないため、ヘッダから各パラメータを取得し、利用する。
    # 引数の値は利用しない。

    provider_id = connexion.request.headers['x-cadde-provider']
    consumer_id = connexion.request.headers['x-cadde-consumer']
    contract_id = connexion.request.headers['x-cadde-contract-id']
    hash_get_data = connexion.request.headers['x-cadde-hash-get-data']
    contract_url = connexion.request.headers['x-cadde-contract-management-service-url']
    authorization = connexion.request.headers['Authorization']

    logger.debug(
        get_message(
            '010302001N', [
                provider_id, consumer_id, contract_id, hash_get_data, contract_url]))

    voucher_result = voucher_sent_call(
        provider_id,
        consumer_id,
        contract_id,
        hash_get_data,
        contract_url,
        authorization,
        external_interface)

    response = Response(response='', status=200)
    return response
