# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server import util


class ErrorResponse(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, detail: str = None, status: float = None, title: str = None, type: str = None):  # noqa: E501
        """ErrorResponse - a model defined in Swagger

        :param detail: The detail of this ErrorResponse.  # noqa: E501
        :type detail: str
        :param status: The status of this ErrorResponse.  # noqa: E501
        :type status: float
        :param title: The title of this ErrorResponse.  # noqa: E501
        :type title: str
        :param type: The type of this ErrorResponse.  # noqa: E501
        :type type: str
        """
        self.swagger_types = {
            'detail': str,
            'status': float,
            'title': str,
            'type': str
        }

        self.attribute_map = {
            'detail': 'detail',
            'status': 'status',
            'title': 'title',
            'type': 'type'
        }
        self._detail = detail
        self._status = status
        self._title = title
        self._type = type

    @classmethod
    def from_dict(cls, dikt) -> 'ErrorResponse':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ErrorResponse of this ErrorResponse.  # noqa: E501
        :rtype: ErrorResponse
        """
        return util.deserialize_model(dikt, cls)

    @property
    def detail(self) -> str:
        """Gets the detail of this ErrorResponse.

        エラーメッセージ  # noqa: E501

        :return: The detail of this ErrorResponse.
        :rtype: str
        """
        return self._detail

    @detail.setter
    def detail(self, detail: str):
        """Sets the detail of this ErrorResponse.

        エラーメッセージ  # noqa: E501

        :param detail: The detail of this ErrorResponse.
        :type detail: str
        """
        if detail is None:
            raise ValueError("Invalid value for `detail`, must not be `None`")  # noqa: E501

        self._detail = detail

    @property
    def status(self) -> float:
        """Gets the status of this ErrorResponse.

        HTTPステータスコード  # noqa: E501

        :return: The status of this ErrorResponse.
        :rtype: float
        """
        return self._status

    @status.setter
    def status(self, status: float):
        """Sets the status of this ErrorResponse.

        HTTPステータスコード  # noqa: E501

        :param status: The status of this ErrorResponse.
        :type status: float
        """
        if status is None:
            raise ValueError("Invalid value for `status`, must not be `None`")  # noqa: E501

        self._status = status

    @property
    def title(self) -> str:
        """Gets the title of this ErrorResponse.

        タイトル  # noqa: E501

        :return: The title of this ErrorResponse.
        :rtype: str
        """
        return self._title

    @title.setter
    def title(self, title: str):
        """Sets the title of this ErrorResponse.

        タイトル  # noqa: E501

        :param title: The title of this ErrorResponse.
        :type title: str
        """

        self._title = title

    @property
    def type(self) -> str:
        """Gets the type of this ErrorResponse.

        タイプ  # noqa: E501

        :return: The type of this ErrorResponse.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type: str):
        """Sets the type of this ErrorResponse.

        タイプ  # noqa: E501

        :param type: The type of this ErrorResponse.
        :type type: str
        """

        self._type = type
