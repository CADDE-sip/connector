import connexion

import re
from flask import make_response
from logging import getLogger

from swagger_server.services.service import fetch_data
from swagger_server.utilities.message_map import get_message
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.utilities import log_message_none_parameter_replace

logger = getLogger(__name__)


def retrieve_entity():
    """Retrieve Entity

    NGSIインタフェースを用いて、コンテキスト情報を取得する。
    Response: * 処理が成功した場合は200を返す。
              * 処理に失敗した場合は、2xxでないコードを返す。場合によりエラーを示すペイロードがつく場合もある。
                Responsesセクションを参照すること
    Args:

    Returns:
        NGSIレスポンスデータ（flaskのレスポンスオブジェクト）

    Raises:
        Cadde_excption: パラメータが正常でない場合 エラーコード:                   00001E


    """

    """
    HTTP Request Header取得
    x-cadde-resource-url       str  : 指定可能なリソースURLは以下とする
                                     ・http://{ドメイン名}/v2/entities?type={entityType}
                                       entityTypeで指定したtypeを持つエンティティの一覧を取得する。
                                       entityTypeを指定しない場合はエラーを返す。
                                     ・http://{ドメイン名}/v2/entities/{entityId}
                                       entityIdで指定したエンティティの情報を取得する。
    x-cadde-resource-api-type  str  : リソース提供手段識別子
    x-cadde-provider           str  : 提供者ID
    x-idp-url                  str  : IdP URL
    Authorization              str  : 利用者トークン
    x-cadde-options            str  : APIごとに利用する固有のオプション
                                      例： "key:val, key2:val2, ..."

    """
    resource_url = connexion.request.headers["x-cadde-resource-url"]
    resource_api_type = connexion.request.headers["x-cadde-resource-api-type"]

    provider = None
    idp_url = None
    authorization = None

    if "x-cadde-provider" in connexion.request.headers:
        provider = connexion.request.headers["x-cadde-provider"]
    if "x-idp-url" in connexion.request.headers:
        idp_url = connexion.request.headers["x-idp-url"]
    if "Authorization" in connexion.request.headers:
        authorization = connexion.request.headers["Authorization"]

    options = ""
    if "x-cadde-options" in connexion.request.headers:
        options = connexion.request.headers["x-cadde-options"]
        logger.debug("NGSIオプションを設定します。options:{}".format(options))

    # HTTP Request Headerのチェック
    # x-cadde-provider、Authorization、x_cadde_optionsはオプションなのでチェックしない（2020/9版）
    if not resource_url or not resource_api_type or not contract:
        # invalid param
        logger.debug("リクエストヘッダが取得できませんでした。")
        raise CaddeException("00001E", status_code=400)

    # リソース提供識別子のチェック
    if resource_api_type != "api/ngsi":
        logger.debug(get_message("18002E"))
        raise CaddeException("18002E", status_code=400)

    # resource_urlのチェック
    # データ管理サーバ（NGSI）のI/Fであることをチェック
    if not re.match(r"https?://.*/v2.*/entities", resource_url):
        logger.debug("データ管理サーバ（NGSI）エンティティ取得のURLではありません。")
        raise CaddeException("00001E", status_code=400)

    # データ管理サーバ（NGSI）のエンティティの属性値以降を取得するようなI/Fでないことをチェック
    if re.match(r"https?://.*/v2.*/entities/.*/attr", resource_url):
        logger.debug("データ管理サーバ（NGSI）の未サポートURLです。")
        raise CaddeException("00001E", status_code=400)

    # エンティティの一覧取得の場合はentityTypeが指定されていることをチェック
    if not re.match(r"https?://.*/v2.*/entities/", resource_url):
        if not re.match(r"https?://.*/v2.*/entities\?.*type=", resource_url):
            logger.debug("エンティティの一覧取得にはクエリにタイプ指定が必要です。")
            raise CaddeException("00001E", status_code=400)

    # x_cadde_optionsのカンマ区切り文字列を辞書にする。
    # "key:val, key2:val2, ..."
    # → { "key": "val", "key2": "val2", ... }
    options_dict = {}
    if options:
        try:
            options = options.split(",")
            for key in options:
                key = key.strip()
                tmp = key.split(":")
                options_dict[tmp[0]] = tmp[1]
        except Exception:
            raise CaddeException('14005E')

    # API定義されていないリクエストヘッダをオプションに追加
    for key, value in connexion.request.headers.items():
        if key.lower() == "fiware-service" or \
           key.lower() == "fiware-servicepath":
            options_dict[key] = value

    logger.debug(
        get_message(
            "18001N",
            [resource_url,
             resource_api_type,
             log_message_none_parameter_replace(provider),
             idp_url,
             log_message_none_parameter_replace(authorization)]))

    try:
        # メイン制御
        data, headers = fetch_data(resource_url,
                                   resource_api_type,
                                   provider,
                                   contract,
                                   idp_url,
                                   authorization,
                                   options_dict)
    except BaseException:
        logger.debug("メイン制御内部でエラーが発生しました。")
        raise

    # flaskレスポンスを生成して返却する
    response = make_response(data.read(), 200)
    response.headers = headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'self'"
    response.headers['Referrer-Policy'] = "no-referrer always"
    return response
