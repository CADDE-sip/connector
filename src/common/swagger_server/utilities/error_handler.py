# -*- coding: utf-8 -*-
import traceback
import json
import logging
from flask import Response

from swagger_server.utilities.cadde_exception import CaddeException

logger = logging.getLogger(__name__)

__DEFAULT_ERROR_HTTP_STATUS_CODE = 500


def handle_api_exception(exception: Exception) -> Response:
    """
    エラーを基にログ出力とレスポンス作成を行う。

    Args:
        exception Exception : 発生したException

    Returns:
        Response: レスポンス

    """
    error_contents = ''
    http_status_code = __DEFAULT_ERROR_HTTP_STATUS_CODE
    is_transparent = False

    if isinstance(exception, CaddeException):
        error_contents = exception.error_message
        http_status_code = exception.http_status_code
        is_transparent = exception.is_transparent
    else:
        if hasattr(exception, 'message'):
            error_contents = str(exception.message)
        else:
            error_contents = str(exception)

        http_status_code = __DEFAULT_ERROR_HTTP_STATUS_CODE

    logger.warning(error_contents)
    logger.warning(
        traceback.format_exception(
            type(exception),
            exception,
            exception.__traceback__))

    if is_transparent:
        response_json = error_contents
    else:
        response_json = json.dumps({'detail': error_contents,
                                    'status': http_status_code,
                                    'title': '',
                                    'type': ''},
                                   ensure_ascii=False)

    response_info = Response(
        response=response_json,
        status=http_status_code,
        mimetype="application/json")

    response_info.headers['X-Content-Type-Options'] = 'nosniff'
    response_info.headers['X-XSS-Protection'] = '1; mode=block'
    response_info.headers['Content-Security-Policy'] = "default-src 'self'; frame-ancestors 'self'"
    response_info.headers['Referrer-Policy'] = "no-referrer always"

    return response_info
