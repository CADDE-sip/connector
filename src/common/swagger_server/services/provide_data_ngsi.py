#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import json
import urllib.request
import ssl
from logging import getLogger

from swagger_server.utilities.message_map import get_message
from swagger_server.utilities.cadde_exception import CaddeException


logger = getLogger(__name__)

__CONFIG_FILE_PATH = './swagger_server/configs/ngsi.json'


def provide_data_ngsi(resource_url, user_id, options={}):
    """
   データ管理サーバ（NGSI）からコンテキスト情報を取得して返却する。

    Args:
        resource_url str  : コンテキスト情報取得を行うリソースURL
        user_id      str  : 認証認可処理で取得する利用者ID
        options      dict : リクエストヘッダ情報 key:ヘッダ名 value:パラメータ

    Returns:
        BytesIO : 取得データ
        dict    : レスポンスヘッダ情報 key:ヘッダ名 value:パラメータ レスポンスヘッダがない場合は空のdictを返す

    Raises:
        Cadde_excption: パラメータが正常でない場合                   エラーコード: 00001E
        Cadde_excption: 認証情報が不正の場合                         エラーコード: 08002E
        Cadde_excption: 指定したリソースが見つからなかった場合       エラーコード: 08003E
        Cadde_excption: 指定したリソースが複数存在する場合           エラーコード: 08004E
        Cadde_excption: 上記以外でエラーが発生した場合               エラーコード: 08005E

    """

    if not resource_url:
        # invalid param
        logger.debug("関数のパラメータが不正です。")
        raise CaddeException("00001E", status_code=400)

    # 利用者IDをキーにngsi.jsonからアクセストークン（Authorization）を取得する
    # user_idは"TEST_ID"固定とする。（2020/9版）
    #
    # 対象のデータ管理サーバがアクセストークン不要のケースを考慮し、
    # コンフィグファイルの読み込みに失敗した場合、コンフィグファイルからアクセストークンが取得できない場合は
    # エラーさせず、HTTPリクエストのヘッダに設定しない。
    user_id = "TEST_ID"
    ngsi_auth = None
    try:
        with open(__CONFIG_FILE_PATH, "r") as f:
            config = json.load(f)
            ngsi_auth = "Bearer " + config["ngsi_auth"][user_id]["auth"]

    except Exception:
        logger.debug("コンフィグファイル（ngsi.json）の読み込みに失敗しました。")
        pass

    logger.debug(get_message("08001N", [resource_url]))

    context = ssl.SSLContext(ssl.PROTOCOL_TLS)

    # リソースURLに対してHTTPリクエストをGETメソッドで実行
    req = urllib.request.Request("{}".format(resource_url))

    # リクエスト時のヘッダにアクセストークン（Authorization）を追加
    if ngsi_auth:
        req.add_header("Authorization", ngsi_auth)

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
            if "Transfer-Encoding" in headers:
                logger.debug("Transfer-Encodingを削除しました。")
                del headers["Transfer-Encoding"]

    # HTTPリクエストでエラーした場合
    except urllib.error.HTTPError as err:
        if err.code == 400:
            # Bad Request
            logger.debug("リクエストにエラーがありました。")
            raise CaddeException("00001E", status_code=err.code)
        elif err.code == 401:
            # Unauthorized
            logger.debug(get_message("08002E"))
            raise CaddeException("08002E", status_code=err.code)
        elif err.code == 404:
            # Not Found
            logger.debug(get_message("08003E"))
            raise CaddeException("08003E", status_code=err.code)
        elif err.code == 409:
            # Conflict
            logger.debug(get_message("08004E"))
            raise CaddeException("08004E", status_code=err.code)
        else:
            # Other errors
            logger.debug(get_message("08005E", [err.reason]))
            raise CaddeException(
                "08005E",
                status_code=500,
                replace_str_list=[
                    err.reason])

    except urllib.error.URLError as err:
        logger.debug(get_message("08005E", [err.reason]))
        raise CaddeException(
            "08005E",
            status_code=500,
            replace_str_list=[
                err.reason])

    except Exception as err:
        logger.debug(get_message("08005E", [err]))
        raise CaddeException(
            "08005E",
            status_code=500,
            replace_str_list=[
                err])

    # 取得データとレスポンスヘッダを呼び出し元に返却する
    return data, headers
