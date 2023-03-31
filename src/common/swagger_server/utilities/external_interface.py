# -*- coding: utf-8 -*-
import requests
from io import BytesIO
import ftplib

from requests.exceptions import Timeout
from timeout_decorator import timeout

from .cadde_exception import CaddeException


class FTP_IgnoreHost(ftplib.FTP):
    def makepasv(self):
        _, port = super().makepasv()
        return self.host, port


class ExternalInterface:

    __HTTP_CONNECT_TIMEOUT = 10
    __HTTP_READ_TIMEOUT = 60
    __FTP_TIMEOUT = 10

    def http_get(
            self,
            target_url: str,
            headers: dict = None,
            auth: tuple = None,
            post_body: dict = None):
        """
        対象URLに対してhttp(get)通信を行ってレスポンスを取得する。

        Args:
            target_url str : 接続するURL
            headers : 設定するheader {ヘッダー名:パラメータ}
            auth : ベーシック認証時のidとpass
            post_body : 設定するbody部

        Returns:
            response : get通信のレスポンス

        Raises:
            CaddeException: 本処理中にExceptionが発生した場合 エラーコード: 000001001E
            CaddeException: タイムアウトが発生した場合 エラーコード: 000001002E

        """

        if not headers:
            headers = {}

        headers['Cache-Control'] = 'no-cache'

        try:
            response = requests.get(
                target_url,
                headers=headers,
                timeout=(
                    self.__HTTP_CONNECT_TIMEOUT,
                    self.__HTTP_READ_TIMEOUT),
                auth=auth,
                params=post_body)

        except Timeout:
            raise CaddeException('000001001E')

        except Exception as e:
            raise CaddeException(
                '000001002E',
                status_code=None,
                replace_str_list=[e])

        return response

    def http_post(
            self,
            target_url: str,
            headers: dict = None,
            post_body: dict = None,
            verify: bool = True):
        """
        対象URLに対してhttp(post)通信を行ってレスポンスを取得する。

        Args:
            target_url str : 接続するURL
            headers : 設定するheader {ヘッダー名:パラメータ}
            post_body : 設定するbody部


        Returns:
            response : gpost通信のレスポンス

        Raises:
            CaddeException: 本処理中にExceptionが発生した場合 エラーコード: 000002001E
            CaddeException: タイムアウトが発生した場合 エラーコード: 000002002E

        """

        if not headers:
            headers = {}

        if not post_body:
            post_body = {}

        headers['Cache-Control'] = 'no-cache'

        req = requests
        if not verify:
            req = requests.Session()
            req.verify = False

        try:
            if 'Content-Type' in headers and headers['Content-Type'] == 'application/x-www-form-urlencoded':
                response = req.post(
                    target_url,
                    headers=headers,

                    timeout=(
                        self.__HTTP_CONNECT_TIMEOUT,
                        self.__HTTP_READ_TIMEOUT),
                    data=post_body
                )
            else:
                response = req.post(
                    target_url,
                    headers=headers,

                    timeout=(
                        self.__HTTP_CONNECT_TIMEOUT,
                        self.__HTTP_READ_TIMEOUT),
                    json=post_body
                )
        except Timeout:
            raise CaddeException('000002001E')

        except Exception as e:
            raise CaddeException(
                '000002002E',
                status_code=None,
                replace_str_list=[e])

        return response

    @timeout(60, use_signals=False)
    def ftp_get(
            self,
            parsed_resource_url: dict,
            ftp_id: str,
            ftp_pass: str) -> BytesIO:
        """
        対象URLに対してftp通信を行ってレスポンスを取得する。

        Args:
            parsed_resource_url dict : 解析後リソースURL {
                'access_point':(接続先),
                'port_no':(ポート番号),
                'directory':(ディレクトリ),
                'file_name':(ファイル名)
                 }
            ftp_id : FTP接続時に利用するID
            ftp_pass : FTP接続時に利用するパスワード

        Returns:
            BytesIO : FTP通信で取得したファイル情報

        Raises:
            Exception: 本処理内でエラーが発生した場合
        """

        file_byte = BytesIO()

        with FTP_IgnoreHost() as ftp:
            ftp.connect(
                parsed_resource_url['access_point'],
                parsed_resource_url['port_no'],
                self.__FTP_TIMEOUT)
            ftp.login(user=ftp_id, passwd=ftp_pass)

            if len(parsed_resource_url['directory']) > 0:
                ftp.cwd(parsed_resource_url['directory'])
            ftp.retrbinary(
                'RETR ' + parsed_resource_url['file_name'],
                file_byte.write)

        file_byte.seek(0)

        return file_byte
