# -*- coding: utf-8 -*-
from logging import getLogger

from swagger_server.utilities.message_map import get_message_and_status_code
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface

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

        Raises:
            CaddeException: 検索条件確認時に不正な値が設定されており、CKAN上でのカタログ検索に失敗した場合  エラーコード: 000101002E
            CaddeException: カタログ詳細検索要求 CKANへの検索要求時にエラーが発生した場合                   エラーコード: 000101003E

    """

    logger.debug(
        get_message_and_status_code(
            '000101001N', [
                query_string, ckan_url]))

    response = ckan_data_get_interface.http_get(ckan_url + query_string)

    if response.status_code == 400:
        raise CaddeException(
            message_id='000101002E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])
    elif response.status_code < 200 or 300 <= response.status_code:
        raise CaddeException(
            message_id='000101003E',
            status_code=response.status_code,
            replace_str_list=[
                response.text])

    return response.text
