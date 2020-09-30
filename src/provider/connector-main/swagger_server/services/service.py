# -*- coding: utf-8 -*-
from io import BytesIO

from swagger_server.utilities.cadde_exception import CaddeException
from swagger_server.utilities.external_interface import ExternalInterface
from swagger_server.utilities.internal_interface import InternalInterface
from swagger_server.services.ckan_access import search_catalog_ckan
from swagger_server.services.provide_data_ngsi import provide_data_ngsi
from swagger_server.services.provide_data_ftp import provide_data_ftp
from swagger_server.services.provide_data_http import provide_data_http

internal_interface = InternalInterface()


def detail_search(
        query_string: str,
        authorization: str,
        external_interface: ExternalInterface = ExternalInterface()) -> str:
    """
    データ管理に、カタログ詳細検索要求を行い、検索結果を返す

    Args:
        query_string str : クエリストリング
        authorization str : 契約トークン
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        str :検索結果

    Raises:
        Cadde_excption: リクエストに失敗した場合 エラーコード: 07002E

    """
    # 利用者コネクタ認証

    # 契約I/Fの契約状態確認_検索 2020年09月版では呼び出しを行わない。
    user_id = None

    return search_catalog_ckan(
        query_string,
        internal_interface,
        external_interface)


def fetch_data(
        resource_url: str,
        resource_api_type: str,
        authorization: str,
        options: str,
        external_interface: ExternalInterface = ExternalInterface()) -> BytesIO:
    """
    データ管理に、NGSI、FTP、HTTPの取得要求を行い、取得データを返す

    Args:
        resource_url str : リソースURL
        resource_api_type str : リソース提供手段識別子
        authorization str : 契約トークン
        options str : データ提供IFが使用するカスタムヘッダー
        external_interface ExternalInterface : GETリクエストを行うインタフェース

    Returns:
        BytesIO :取得データ
        dict :ヘッダ情報 ヘッダ情報がない場合は空のdictを返す
    Raises:
        Cadde_excption: リソース提供手段識別子が'api/ngsi', 'file/ftp', 'file/http'以外の場合 エラーコード: 04002E

    """

    # 利用者コネクタ認証

    # 契約I/Fの契約状態確認_検索 2020年09月版では呼び出しを行わない。
    user_id = 'dummy'

    response_bytes = None
    response_headers = {}
    options_dict = None
    try:
        options_dict = __exchange_options_dict(options)
    except Exception:
        raise CaddeException('04009E')
    if(resource_api_type == 'api/ngsi'):

        response_bytes, response_headers = provide_data_ngsi(
            resource_url, user_id, options_dict)
    elif(resource_api_type == 'file/ftp'):
        response_bytes = provide_data_ftp(
            resource_url, external_interface, internal_interface)

    elif(resource_api_type == 'file/http'):
        response_bytes = provide_data_http(
            resource_url, options_dict, external_interface, internal_interface)

    else:
        raise CaddeException('04002E')

    return response_bytes, response_headers


def __exchange_options_dict(options_str: str) -> dict:
    """
    データ提供IFが使用するカスタムヘッダーの文字列を辞書型に変換する。
    変換前: "key1:value1,key2:value2・・・・"
    変換後: {'key1': 'value1', 'key2': 'value2'}

    Args:
        options_str str : データ提供IFが使用するカスタムヘッダーの文字列

    Returns:
        dict:  データ提供IFが使用するカスタムヘッダーの辞書型
    """

    return_dict = {}

    if not options_str:
        return return_dict

    options_str_split = options_str.split(',')

    for one_object in options_str_split:
        one_object_split = one_object.split(':')
        return_dict[one_object_split[0]] = one_object_split[1]

    return return_dict
