# -*- coding: utf-8 -*-

import requests
from logging import getLogger
from io import BytesIO

from swagger_server.utilities.message_map import get_message
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

logger = getLogger(__name__)

__CONFIG_FILE_PATH = '/usr/src/app/swagger_server/configs/http.json'

__CONFIG_KEY_BASIC_AUTH = 'basic_auth'
__CONFIG_KEY_HTTP_DOMAIN = 'domain'
__CONFIG_KEY_BASIC_ID = 'basic_id'
__CONFIG_KEY_BASIC_PASS = 'basic_pass'

__URL_SPLIT_CHAR = '/'


def provide_data_http(
        resource_url: str,
        headers_dict: dict = None,
        file_get_interface: ExternalInterface = ExternalInterface(),
        config_get_interface: InternalInterface = InternalInterface()) -> BytesIO:
    """
    HTTPサーバからファイルを取得して返却する。
    ※2020年9月版ではダイジェスト認証、TLS証明書認証、OAuth等の認証処理は実施せず、
    ※ベーシック認証のみ実施する。

    Args:
        resource_url str : ファイル取得を行うリソースURL
        headers_dict : 設定するheader {ヘッダー名:パラメータ}
        file_get_interface object : ファイル取得処理を行うインタフェース
        config_get_interface object : コンフィグファイルからの情報取得を行うインタフェース

    Returns:
        BytesIO :取得データ

    Raises:
        Cadde_excption: パラメータが正常でない場合 エラーコード: 000201002E
        Cadde_excption: コンフィグファイルからベーシック認証時のIDもしくはパスワードが取得できない場合 エラーコード: 000201003E
        Cadde_excption: ファイルのダウンロードに失敗した場合 エラーコード: 000201004E
        Cadde_excption: 参照先URLにファイルが見つからない場合 エラーコード: 000201005E
        Cadde_excption: HTTP接続時のベーシック認証に失敗している場合 エラーコード: 000201006E
        Cadde_excption: リソースURLからドメイン情報の取得に失敗した場合 エラーコード: 000201007E
        Cadde_excption: タイムアウトが発生した場合 エラーコード: 000201008E

    """
    if not resource_url:
        raise CaddeException('000201002E')

    logger.debug(get_message('000201001N', [resource_url, headers_dict]))

    auth = None
    domain = None
    http_config_domain = []

    try:
        domain = __get_domain(resource_url)
    except Exception:
        raise CaddeException('000201003E')

    try:
        http_config = config_get_interface.config_read(__CONFIG_FILE_PATH)
        http_config_domain = [
            e for e in http_config[__CONFIG_KEY_BASIC_AUTH] if e[__CONFIG_KEY_HTTP_DOMAIN] == domain]
    except Exception:
        # コンフィグファイルから指定したドメインの情報が取得できない場合は何もしない
        pass

    if 0 < len(http_config_domain):
        if __CONFIG_KEY_BASIC_ID not in http_config_domain[0]:
            raise CaddeException(
                '000201004E',
                status_code=None,
                replace_str_list=[__CONFIG_KEY_BASIC_ID])

        if __CONFIG_KEY_BASIC_PASS not in http_config_domain[0]:
            raise CaddeException(
                '000201005E',
                status_code=None,
                replace_str_list=[__CONFIG_KEY_BASIC_PASS])

        auth = (
            http_config_domain[0][__CONFIG_KEY_BASIC_ID],
            http_config_domain[0][__CONFIG_KEY_BASIC_PASS])

    response = file_get_interface.http_get(resource_url, headers_dict, auth)

    if response.status_code == requests.codes.ok:
        return BytesIO(response.content)

    if response.status_code == requests.codes.not_found:
        raise CaddeException('000201006E')

    if response.status_code == requests.codes.unauthorized:
        raise CaddeException('000201007E')

    else:
        raise CaddeException(
            '000201008E',
            status_code=None,
            replace_str_list=[
                response.text])


def __get_domain(resource_url: str) -> str:
    """
    URLを解析し、ドメインを取得する。ポート番号が設定されている場合は、ポート番号も含む。
    URLはhttp[s]://(ドメイン部)/・・・・ の前提とする。

    Args:
        resource_url 対象URL

    Returns:
        str : ドメイン

    """

    return resource_url.split(__URL_SPLIT_CHAR)[2]
