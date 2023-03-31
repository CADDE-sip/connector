import connexion

import re
import urllib
from flask import make_response
from logging import getLogger

from swagger_server.services.service import fetch_data
from swagger_server.utilities.message_map import get_message
from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.utilities import log_message_none_parameter_replace, get_url_file_name

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
        Cadde_excption: 必須パラメータが設定されていなかった場合
        （リクエストヘッダ）                              エラーコード:  020003002E
        Cadde_excption: リソース提供識別子が"api/ngsi"でない場合
                                                          エラーコード:  020003003E
        Cadde_excption: 必須パラメータが設定されていなかった場合
        （データ管理サーバ（NGSI）エンティティ取得のURL） エラーコード:  020003004E
        Cadde_excption: 必須パラメータが設定されていなかった場合
        （データ管理サーバ（NGSI）のサポートURL）         エラーコード:  020003005E
        Cadde_excption: 必須パラメータが設定されていなかった場合
        （タイプ指定）                                    エラーコード:  020003006E
        Cadde_excption: データ提供IFが使用するカスタムヘッダーの変換に失敗した場合
                                                          エラーコード:  020003007E

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
    x-cadde-cadde-provider     str  : CADDEユーザID（提供者）
    Authorization              str  : 利用者トークン
    x-cadde-options            str  : APIごとに利用する固有のオプション
                                      例： "key:val, key2:val2, ..."

    """
    resource_url = connexion.request.headers["x-cadde-resource-url"]
    resource_api_type = connexion.request.headers["x-cadde-resource-api-type"]

    provider = None
    authorization = None

    if "x-cadde-provider" in connexion.request.headers:
        provider = connexion.request.headers["x-cadde-provider"]
    if "Authorization" in connexion.request.headers:
        authorization = connexion.request.headers["Authorization"]

    options = ""
    if "x-cadde-options" in connexion.request.headers:
        options = connexion.request.headers["x-cadde-options"]
        logger.debug("NGSIオプションを設定します。options:{}".format(options))

    # HTTP Request Headerのチェック
    # x-cadde-provider、Authorization、x_cadde_optionsはオプションなのでチェックしない
    if not resource_url or not resource_api_type:
        # invalid param
        logger.debug("リクエストヘッダが取得できませんでした。")
        raise CaddeException('020003002E')

    # リソース提供識別子のチェック
    if resource_api_type != "api/ngsi":
        logger.debug(get_message('020003003E'))
        raise CaddeException('020003003E')

    # resource_urlのチェック
    # データ管理サーバ（NGSI）のI/Fであることをチェック
    if not re.match(r"https?://.*/v2.*/entities", resource_url):
        logger.debug("データ管理サーバ（NGSI）エンティティ取得のURLではありません。")
        raise CaddeException('020003004E')

    # データ管理サーバ（NGSI）のエンティティの属性値以降を取得するようなI/Fでないことをチェック
    if re.match(r"https?://.*/v2.*/entities/.*/attr", resource_url):
        logger.debug("データ管理サーバ（NGSI）の未サポートURLです。")
        raise CaddeException('020003005E')

    # エンティティタイプが指定されていることをチェック
    parse_url = urllib.parse.urlparse(resource_url)
    query = urllib.parse.parse_qs(parse_url.query)
    if 'type' not in query:
        logger.debug("クエリにタイプ指定が必要です。")
        raise CaddeException('020003006E')

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
            raise CaddeException('020003007E')

    # API定義されていないリクエストヘッダをオプションに追加
    for key, value in connexion.request.headers.items():
        if key.lower() == "fiware-service" or \
           key.lower() == "fiware-servicepath":
            options_dict[key.lower()] = value

    logger.debug(
        get_message(
            '020003001N',
            [resource_url,
             resource_api_type,
             log_message_none_parameter_replace(provider),
             log_message_none_parameter_replace(authorization)]))

    try:
        # メイン制御
        data, headers = fetch_data(authorization,
                                   resource_url,
                                   resource_api_type,
                                   provider,
                                   options_dict)
    except BaseException:
        logger.debug("メイン制御内部でエラーが発生しました。")
        raise

    # flaskレスポンスを生成して返却する
    response = make_response(data.read(), 200)
    response.headers = headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers[
        'Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'self'; object-src 'none'; script-src 'none';"
    response.headers['Referrer-Policy'] = "no-referrer always"
    response.headers['Content-Disposition'] = 'attachment; filename=' + \
        get_url_file_name(resource_url)

    if 'Server' in response.headers:
        del response.headers['Server']

    if 'Date' in response.headers:
        del response.headers['Date']

    if 'Transfer-Encoding' in response.headers:
        del response.headers['Transfer-Encoding']

    return response
