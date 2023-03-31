# -*- coding: utf-8 -*-
from .message_map import get_message_and_status_code
import json


class CaddeException(Exception):
    """
    独自Exception
    Exception生成時にメッセージIDを受け取り、エラーメッセージ、httpステータスコードを保持する。
    """

    def __init__(
            self,
            message_id: str,
            status_code: int = None,
            replace_str_list: list = None):
        """
        コンストラクタ
        メッセージIDを基に、エラーメッセージ、httpステータスコードを取得し保持する。
        引数でステータスコードを保持していない場合は、get_message_and_status_codeから取得するステータスコードを保持
        保持している場合は、引数のステータスコードを保持

        Args:
            message_id str : メッセージID
            status_code int : ステータスコード
            replace_str_list list : 置き換え文字列リスト
        """
        self.is_transparent = False
        try:
            if replace_str_list is not None and len(replace_str_list) == 1:
                # エラーメッセージの場合は透過
                json.loads(replace_str_list[0])
                self.error_message = replace_str_list[0] + \
                    '(' + message_id + ')'
                self.is_transparent = True
            else:
                result = get_message_and_status_code(
                    message_id, replace_str_list)
                self.error_message = result['message'] + '(' + message_id + ')'
        except Exception:
            result = get_message_and_status_code(message_id, replace_str_list)
            self.error_message = result['message'] + '(' + message_id + ')'

        if not status_code:
            self.http_status_code = result['http_status_code']
        else:
            self.http_status_code = status_code
