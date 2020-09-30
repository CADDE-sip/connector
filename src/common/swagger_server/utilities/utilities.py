# -*- coding: utf-8 -*-

from flask import Response

__LOG_MESSAGE_REPLACE_STR = '設定なし'
__URL_SPLIT_CHR = '/'

__FILE_NAME_RETENTION_ATTRIBUTE = 'Content-Disposition'
__FILE_NAME_ATTRIBUTE = 'filename='


def log_message_none_parameter_replace(target_str: str) -> str:
    """
    対象文字列を確認し、Noneの場合は"設定なし"、そうでない場合は対象文字列を返す。

    Args:
        target_str str : 対象文字列

    Returns:
        str: 文字列
    """
    if target_str is None:
        return __LOG_MESSAGE_REPLACE_STR
    else:
        return target_str


def get_response_file_name(response: Response) -> str:
    """
    レスポンスからファイル名を取得する

    Args:
        response Response : HTTPレスポンス

    Returns:
        str: ファイル名
    """

    contentDisposition = response.headers[__FILE_NAME_RETENTION_ATTRIBUTE]
    file_name = contentDisposition[contentDisposition.find(
        __FILE_NAME_ATTRIBUTE) + len(__FILE_NAME_ATTRIBUTE):]

    return file_name


def get_url_file_name(url: str) -> str:
    """
    urlからファイル名を取得する
    引数に設定されるURL内に必ず'/'が一つ以上存在し、最後に出現する'/'以降の文字列がファイル名となっている前提

    Args:
        url Str : URL

    Returns:
        str: ファイル名
    """

    return url.split(__URL_SPLIT_CHR)[-1]
