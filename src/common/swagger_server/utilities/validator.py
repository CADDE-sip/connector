# -*- coding: utf-8 -*-
from .cadde_exception import CaddeException


def validate_parameter_normality(check_param_keys: list, target: dict) -> None:
    """
    チェック対象の辞書型のキーを確認し、チェックするキー一覧が
    チェック対象のキーにすべて含まれているか確認する

    Args:
        check_param_keys list : チェックするキー一覧
        target dict : チェック対象

    Raises:
        CaddeException: チェック対象のキーにチェックするキー一覧のいずれかが含まれていない場合 エラーコード:000000001E
        CaddeException: 本処理中にExceptionが発生した場合 エラーコード:000000002E
    """

    if not target or not check_param_keys:
        raise CaddeException(message_id='000000001E')

    for check_param_key in check_param_keys:
        if check_param_key not in target:
            raise CaddeException(message_id='000000002E')
