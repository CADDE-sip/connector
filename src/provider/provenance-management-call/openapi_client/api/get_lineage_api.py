"""
    Chain Data Lineage API

    CDLv2 API  # noqa: E501

    The version of the OpenAPI document: 2.1.0
    Generated by: https://openapi-generator.tech
"""


import re  # noqa: F401
import sys  # noqa: F401

from openapi_client.api_client import ApiClient, Endpoint as _Endpoint
from openapi_client.model_utils import (  # noqa: F401
    check_allowed_values,
    check_validations,
    date,
    datetime,
    file_type,
    none_type,
    validate_and_convert_types
)
from openapi_client.model.cdl_event_list import CDLEventList


class GetLineageApi(object):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

        def __lineage(
            self,
            cdleventid,
            **kwargs
        ):
            """get CDL lineage  # noqa: E501

            Returns CDL lineage information starting from the given cdleventid   # noqa: E501
            This method makes a synchronous HTTP request by default. To make an
            asynchronous HTTP request, please pass async_req=True

            >>> thread = api.lineage(cdleventid, async_req=True)
            >>> result = thread.get()

            Args:
                cdleventid (str): cdl event id of starting entity

            Keyword Args:
                direction (str): lineage direction from the starting point [BACKWARD(=default), FORWARD, BOTH]. [optional] if omitted the server will use the default value of "BACKWARD"
                depth (int): lineage depth from the event specified by cdleventid: 0 indicates that you request the single event specified by cdleventid. A positive integer indicates that you request all the events whose distance from the specified record is not greater than the given depth. -1 indicates that you request all the events which can be reached  from the specified event.. [optional] if omitted the server will use the default value of -1
                _return_http_data_only (bool): response data without head status
                    code and headers. Default is True.
                _preload_content (bool): if False, the urllib3.HTTPResponse object
                    will be returned without reading/decoding response data.
                    Default is True.
                _request_timeout (float/tuple): timeout setting for this request. If one
                    number provided, it will be total request timeout. It can also
                    be a pair (tuple) of (connection, read) timeouts.
                    Default is None.
                _check_input_type (bool): specifies if type checking
                    should be done one the data sent to the server.
                    Default is True.
                _check_return_type (bool): specifies if type checking
                    should be done one the data received from the server.
                    Default is True.
                _host_index (int/None): specifies the index of the server
                    that we want to use.
                    Default is read from the configuration.
                async_req (bool): execute request asynchronously

            Returns:
                CDLEventList
                    If the method is called asynchronously, returns the request
                    thread.
            """
            kwargs['async_req'] = kwargs.get(
                'async_req', False
            )
            kwargs['_return_http_data_only'] = kwargs.get(
                '_return_http_data_only', True
            )
            kwargs['_preload_content'] = kwargs.get(
                '_preload_content', True
            )
            kwargs['_request_timeout'] = kwargs.get(
                '_request_timeout', None
            )
            kwargs['_check_input_type'] = kwargs.get(
                '_check_input_type', True
            )
            kwargs['_check_return_type'] = kwargs.get(
                '_check_return_type', True
            )
            kwargs['_host_index'] = kwargs.get('_host_index')
            kwargs['cdleventid'] = \
                cdleventid
            return self.call_with_http_info(**kwargs)

        self.lineage = _Endpoint(
            settings={
                'response_type': (CDLEventList,),
                'auth': [],
                'endpoint_path': '/lineage/{cdleventid}',
                'operation_id': 'lineage',
                'http_method': 'GET',
                'servers': None,
            },
            params_map={
                'all': [
                    'cdleventid',
                    'direction',
                    'depth',
                ],
                'required': [
                    'cdleventid',
                ],
                'nullable': [
                ],
                'enum': [
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                },
                'openapi_types': {
                    'cdleventid':
                        (str,),
                    'direction':
                        (str,),
                    'depth':
                        (int,),
                },
                'attribute_map': {
                    'cdleventid': 'cdleventid',
                    'direction': 'direction',
                    'depth': 'depth',
                },
                'location_map': {
                    'cdleventid': 'path',
                    'direction': 'query',
                    'depth': 'query',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/json'
                ],
                'content_type': [],
            },
            api_client=api_client,
            callable=__lineage
        )