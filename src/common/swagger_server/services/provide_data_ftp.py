# -*- coding: utf-8 -*-

from logging import getLogger
from io import BytesIO
from timeout_decorator import TimeoutError

from swagger_server.utilities.message_map import get_message
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface

logger = getLogger(__name__)

__CONFIG_FILE_PATH = '/usr/src/app/swagger_server/configs/ftp.json'

__CONFIG_KEY_FTP_AUTH = 'ftp_auth'
__CONFIG_KEY_FTP_DOMAIN = 'domain'
__CONFIG_KEY_FTP_ID = 'ftp_id'
__CONFIG_KEY_FTP_PASS = 'ftp_pass'

__FTP_DEFAULT_IDPASS = 'anonymous'

__URL_SPLIT_CHR = '/'
__ACCESS_POINT_SPLIT_CHR = ':'
__FTP_DEFAULT_PORT = 21


def provide_data_ftp(
        resource_url: str,
        file_get_interface: ExternalInterface = ExternalInterface(),
        config_get_interface: InternalInterface = InternalInterface()) -> BytesIO:
    """
    FTPサーバからファイルを取得して返却する。
    ※リソースURLに対して、ファイル取得を行う。接続方法はFTPのみとし、SFTPを用いた認証は行わない。

    Args:
        resource_url str : ファイル取得を行うリソースURL
        file_get_interface ExternalInterface : ファイル取得処理を行うインタフェース
        config_get_interface InternalInterface : コンフィグ情報取得処理を行うインタフェース

    Returns:
        BytesIO :取得データ

    Raises:
        Cadde_excption: リソースURLが取得できない場合 エラーコード: 000301002E
        Cadde_excption: コンフィグファイルから設定が取得できない場合          エラーコード: 000301003E
        Cadde_excption: パラメータが正常でない場合(ftp_id)                    エラーコード: 000301004E
        Cadde_excption: パラメータが正常でない場合(ftp_pass)                  エラーコード: 000301005E
        Cadde_excption: ファイルのダウンロードに失敗した場合                  エラーコード: 000301006E
        Cadde_excption: FTP接続時の認証に失敗している場合                     エラーコード: 000301007E
        Cadde_excption: 参照先ディレクトリもしくは、ファイルが存在しない場合  エラーコード: 000301008E
        Cadde_excption: タイムアウトが発生した場合                            エラーコード: 000301009E
        Cadde_excption: リソースURLからドメイン情報の取得に失敗した場合       エラーコード: 000301010E

    """
    if not resource_url:
        raise CaddeException("000301002E")

    logger.debug(get_message("000301001N", [resource_url]))

    try:
        domain = __get_domain(resource_url)
    except Exception:
        raise CaddeException('000301003E')

    ftp_auth_domain = []
    try:
        config = config_get_interface.config_read(__CONFIG_FILE_PATH)
        ftp_auth_domain = [e for e in config[__CONFIG_KEY_FTP_AUTH]
                           if e[__CONFIG_KEY_FTP_DOMAIN] == domain]
    except Exception:
        pass

    if 0 < len(ftp_auth_domain):
        if __CONFIG_KEY_FTP_ID not in ftp_auth_domain[0]:
            raise CaddeException(
                '000301004E',
                status_code=None,
                replace_str_list=[__CONFIG_KEY_FTP_ID])

        if __CONFIG_KEY_FTP_PASS not in ftp_auth_domain[0]:
            raise CaddeException(
                '000301005E',
                status_code=None,
                replace_str_list=[__CONFIG_KEY_FTP_PASS])

        ftp_id = ftp_auth_domain[0][__CONFIG_KEY_FTP_ID]
        ftp_pass = ftp_auth_domain[0][__CONFIG_KEY_FTP_PASS]
    else:
        ftp_id = __FTP_DEFAULT_IDPASS
        ftp_pass = __FTP_DEFAULT_IDPASS

    parsed_resource_url = __url_analysis(resource_url)

    response = None
    try:
        response = file_get_interface.ftp_get(
            parsed_resource_url, ftp_id, ftp_pass)
    except TimeoutError:
        raise CaddeException('000301006E')
    except Exception as e:
        error_message = str(e)
        error_code = error_message.split(' ')[0]
        if error_code == '530':
            raise CaddeException('000301007E')
        elif error_code == '550':
            raise CaddeException('000301008E')
        elif error_message == 'timed out':
            raise CaddeException('000301009E')
        else:
            raise CaddeException(
                '000301010E',
                status_code=None,
                replace_str_list=[error_message])

    return response


def __url_analysis(url: str) -> dict:
    """
    URLを解析し、接続先、ポート番号、ディレクトリ、ファイル名を取得する。
    ディレクトリは設定されていなければ空文字となる。
    ドメインの末尾にポート指定がない場合はポート番号に21を設定する。

    Args:
        url str : 解析するURL
        target dict : チェック対象

    Returns:
        dict :解析後データ {'access_point':(接続先), 'port_no':(ポート番号) 'directory':(ディレクトリ), 'file_name':(ファイル名)}

    """

    split_url = url.split(__URL_SPLIT_CHR)

    domain = split_url[2]

    split_domain = domain.split(__ACCESS_POINT_SPLIT_CHR)

    access_point = split_domain[0]
    port_no = __FTP_DEFAULT_PORT

    if len(split_domain) == 2:
        port_no = int(split_domain[1])

    directory = ''
    if len(split_url) > 3:

        directory_last_element = len(split_url) - 1
        for element in split_url[3:directory_last_element]:
            directory = directory + element + __URL_SPLIT_CHR

    file_name = split_url[-1]

    return {
        'access_point': access_point,
        'port_no': port_no,
        'directory': directory,
        'file_name': file_name}


def __get_domain(resource_url: str) -> str:
    """
    URLを解析し、ドメインを取得する。ポート番号が設定されている場合は、ポート番号も含む。
    URLはhttp[s]://(ドメイン部)/・・・・ の前提とする。

    Args:
        resource_url 対象URL

    Returns:
        str : ドメイン

    """

    return resource_url.split(__URL_SPLIT_CHR)[2]
