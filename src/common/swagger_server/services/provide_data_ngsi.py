#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import urllib.request
import ssl
from logging import getLogger

from swagger_server.utilities.message_map import get_message
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.internal_interface import InternalInterface


logger = getLogger(__name__)

__CONFIG_FILE_PATH = './swagger_server/configs/ngsi.json'
__CONFIG_KEY_NGSI_NGSIAUTH = 'ngsi_auth'
__CONFIG_KEY_NGSI_DOMAIN = 'domain'
__CONFIG_KEY_AUTH = 'auth'
__URL_SPLIT_CHAR = '/'


def provide_data_ngsi(resource_url, options={}):
    """
   データ管理サーバ（NGSI）からコンテキスト情報を取得して返却する。

    Args:
        resource_url str  : コンテキスト情報取得を行うリソースURL
        options      dict : リクエストヘッダ情報 key:ヘッダ名 value:パラメータ

    Returns:
        BytesIO : 取得データ
        dict    : レスポンスヘッダ情報 key:ヘッダ名 value:パラメータ レスポンスヘッダがない場合は空のdictを返す

    Raises:
        Cadde_excption: パラメータが正常でない場合                      エラーコード: 000401002E
        Cadde_excption: リソースURLからドメイン情報の取得に失敗した場合 エラーコード: 000401003E
        Cadde_excption: 認証情報が不正の場合                            エラーコード: 000401004E
        Cadde_excption: 指定したリソースが見つからなかった場合          エラーコード: 000401005E
        Cadde_excption: 指定したリソースが複数存在する場合              エラーコード: 000401006E
        Cadde_excption: 上記以外でエラーが発生した場合                  エラーコード: 000401007E

    """

    if not resource_url:
        # invalid param
        logger.debug('関数のパラメータが不正です。')
        raise CaddeException('000401002E', status_code=400)

    # ngsi.jsonからアクセストークン（Authorization）を取得する
    # 対象のデータ管理サーバがアクセストークン不要のケースを考慮し、
    # コンフィグファイルの読み込みに失敗した場合、コンフィグファイルからアクセストークンが取得できない場合は
    # エラーさせず、HTTPリクエストのヘッダに設定しない。
    ngsi_auth = __get_accesstoken_ngsi(resource_url)

    logger.debug(get_message('000401001N', [resource_url]))

    context = ssl.SSLContext(ssl.PROTOCOL_TLS)

    # リソースURLに対してHTTPリクエストをGETメソッドで実行
    req = urllib.request.Request('{}'.format(resource_url))

    # リクエスト時のヘッダにアクセストークン（Authorization）を追加
    if ngsi_auth:
        req.add_header('Authorization', ngsi_auth)

    # リクエスト時のヘッダにその他のオプションを追加
    for key, value in options.items():
        req.add_header(key, value)

    try:
        # HTTPリクエストする。
        with urllib.request.urlopen(req, context=context, timeout=10) as res:
            data = io.BytesIO(res.read())
            headers = {}
            headers = dict(res.getheaders())
            # Flaskが返却するレスポンスヘッダにContent-Lengthが追加されるため、
            # Transfer-Encoding削除
            if 'Transfer-Encoding' in headers:
                logger.debug('Transfer-Encodingを削除しました。')
                del headers['Transfer-Encoding']

    # HTTPリクエストでエラーした場合
    except urllib.error.HTTPError as err:
        if err.code == 400:
            # Bad Request
            logger.debug('リクエストにエラーがありました。')
            raise CaddeException('000401003E', status_code=err.code)
        elif err.code == 401:
            # Unauthorized
            logger.debug(get_message('000401004E'))
            raise CaddeException('000401004E', status_code=err.code)
        elif err.code == 404:
            # Not Found
            logger.debug(get_message('000401005E'))
            raise CaddeException('000401005E', status_code=err.code)
        elif err.code == 409:
            # Conflict
            logger.debug(get_message('000401006E'))
            raise CaddeException('000401006E', status_code=err.code)
        else:
            # Other errors
            logger.debug(get_message('000401007E', [err.reason]))
            raise CaddeException(
                '000401007E',
                status_code=500,
                replace_str_list=[
                    err.reason])

    except urllib.error.URLError as err:
        logger.debug(get_message('000401007E', [err.reason]))
        raise CaddeException(
            '000401007E',
            status_code=500,
            replace_str_list=[
                err.reason])

    except Exception as err:
        logger.debug(get_message('000401007E', [err]))
        raise CaddeException(
            '000401007E',
            status_code=500,
            replace_str_list=[
                err])

    # 取得データとレスポンスヘッダを呼び出し元に返却する
    return data, headers


def __get_accesstoken_ngsi(resource_url):
    """
    アクセストークンを取得する

    Args:
        resource_url str : リソースURL

    Returns:
        str      : アクセストークン

    Raises:
        Cadde_excption: リソースURLからドメイン情報の取得に失敗した場合 エラーコード: 000401008E

    """

    ngsi_auth = None
    domain = None
    ngsi_config_domain = {}

    try:
        domain = __get_domain(resource_url)
    except Exception:
        raise CaddeException('000401008E')

    config_get_interface = InternalInterface()

    try:
        ngsi_config = config_get_interface.config_read(__CONFIG_FILE_PATH)

        # コンフィグファイルのドメインに一致した情報を取得
        for e in ngsi_config[__CONFIG_KEY_NGSI_NGSIAUTH]:
            if e[__CONFIG_KEY_NGSI_DOMAIN] == domain:
                ngsi_config_domain = e
                break

    except Exception:
        # コンフィグファイルから指定したドメインの情報が取得できない場合は何もしない
        pass

    if 0 < len(ngsi_config_domain):

        if __CONFIG_KEY_AUTH in ngsi_config_domain:
            if ngsi_config_domain[__CONFIG_KEY_AUTH] != '':
                ngsi_auth = 'Bearer ' + ngsi_config_domain[__CONFIG_KEY_AUTH]

    return ngsi_auth


def __get_domain(resource_url):
    """
    URLを解析し、ドメインを取得する。ポート番号が設定されている場合は、ポート番号も含む。
    URLはhttp[s]://(ドメイン部)/・・・・ の前提とする。

    Args:
        resource_url 対象URL

    Returns:
        str : ドメイン

    """

    return resource_url.split(__URL_SPLIT_CHAR)[2]
