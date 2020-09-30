# -*- coding: utf-8 -*-
import json


class InternalInterface:
    def config_read(self, file_path: str) -> dict:
        """
        コンフィグファイルからパラメータを取得する

        Args:
            file_path str : コンフィグファイルのパス

        Returns:
            dict : コンフィグファイルの内容
        """

        json_file = open(file_path, 'r')
        json_data = json.load(json_file)

        return json_data
