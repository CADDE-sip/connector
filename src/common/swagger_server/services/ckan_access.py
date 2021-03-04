# -*- coding: utf-8 -*-
from logging import getLogger

from swagger_server.utilities.message_map import get_message_and_status_code
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface

__CONFIG_CKAN_URL_FILE_PATH = '/usr/src/app/swagger_server/configs/ckan.json'
__CONFIG_CKAN_URL = 'ckan_url'

logger = getLogger(__name__)


def search_catalog_ckan(
        ckan_url: str,
        query_string: str,
        ckan_data_get_interface: ExternalInterface) -> str:
    """
    CKANサーバからカタログ詳細検索結果を取得して返却する

    Args:
        ckan_url: str 接続先のCKANURL
        query_string str : クエリストリング
        ckan_get_interface ExternalInterface : ckanからデータの取得を行うインターフェース

    Returns:
        str :CKANから検索した結果の文字列
    """

    logger.debug(
        get_message_and_status_code(
            '07001N', [
                query_string, ckan_url]))

    response = ckan_data_get_interface.http_get(ckan_url + query_string)

    if response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='07002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    return response.text
