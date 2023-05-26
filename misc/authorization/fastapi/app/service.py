# service.py
# 処理ロジック
# Keycloakへのアクセスはkeycloak.pyに記述

# External packages
import sys
import logging
import json
import re
import datetime
import requests
import base64
from requests.models import Response
from fastapi.responses import JSONResponse
from typing import List, Any, Optional, Union
from urllib.parse import quote, unquote

# Internal packages
from settings import settings
import main
import keycloak

logger = logging.getLogger(__name__)

def federate(authorization_header_value: str, realm_name: str, access_token: str) -> dict:
    """
    main.federate_tokenから呼び出し
    認証トークンと引き換えに認可トークン取得
    属性を同期させるために、2回トークン交換を行う
    """
    logger.debug(sys._getframe().f_code.co_name)

    result = {
        'status_code': 200,
        'content': {'access_token': ''}
    }

    # 1回目
    response = initialization_response()
    try:
        logger.info("1st token exchange")
        response = keycloak.federate(authorization_header_value, realm_name, access_token)
        response.raise_for_status()
        if not response.json().get('access_token', ''):
            requests.exceptions.RequestException
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message':  'federate error',
            'detail':  f'{response.status_code}: {text}'
        }

    # 2回目
    response = initialization_response()
    try:
        logger.info("2nd token exchange")
        response = keycloak.federate(authorization_header_value, realm_name, access_token)
        response.raise_for_status()
        if authz_token := response.json().get('access_token', ''):
            result['content']['access_token'] = authz_token
        else:
            requests.exceptions.RequestException
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message':  'federate token error',
            'detail':  f'{response.status_code}: {text}'
        }

    return result


def confirm_authorization(authorization_header_value: str, realm_name: str, client_id: str, resource_url: str, authz_token: str) -> dict:
    """
    main.conrim_authorizationから呼び出し
    認可確認
    - PAT(Protection API Token)を取得
        - Client CredentialsによってProtection API Tokenを取得
    - リソースIDを取得
        - Protection API(with PAT)によって、リソースURLからリソースIDを検索する
    - 認可を確認
        - 認可トークンを使う
    - 契約情報を取得
        - ポリシーの説明に記載してある
    """

    result = {
        'status_code': 200,
        'content': {
            "contract": {
                "trade_id": "",
                "contract_url": "",
                "contract_type": ""
            }
        }
    }

    # リソースURLのURLエンコード
    resource_url = quote(resource_url, safe='')

    # PAT取得
    response = initialization_response()
    try:
        response = keycloak.obtain_pat(authorization_header_value, realm_name)
        response.raise_for_status()
        if access_token := response.json().get('access_token', ''):
            pat = access_token
        else:
            requests.exceptions.RequestException
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'obtain pat error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # PATのデバッグログ
    splitted_jwt = pat.split('.')
    encoded_payload = splitted_jwt[1] # [0]: header, [1]: payload, [2]: signature
    encoded_payload += '=' * ((4 - len(encoded_payload) % 4) % 4) # 長さ調整"="で埋める
    decoded_payload = json.loads(base64.urlsafe_b64decode(encoded_payload).decode())
    logger.debug(decoded_payload)

    # リソースID取得
    response = initialization_response()
    try:
        response = keycloak.get_resource_id(pat, realm_name, resource_url)
        response.raise_for_status()
        logger.info(response.json())
        if response.json():
            resource_id = response.json()[0]
        else:
            raise requests.exceptions.RequestException
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 404
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get resource id error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # 認可確認
    response = initialization_response()
    try:
        response = keycloak.confirm_authorization(authz_token, realm_name, client_id, resource_id)
        response.raise_for_status()
        rpt = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'confirm authorization error',
            'detail':  f'{response.status_code}: {text}'
        }
        return result

    # RPTからユーザのUUIDを取得
    try:
        user_uuid = get_subject_id_from_token(rpt)
        if not user_uuid:
            raise requests.exceptions.RequestException
    except requests.exceptions.RequestException as e:
        result['status_code'] = 403
        result['content'] = {
            'message': 'invalid RPT',
            'detail': f'{response.status_code}: {response.text}'
        }
        return result

    # アドミンのアクセストークン取得(クライアント一覧取得、評価実行のため)
    response = initialization_response()
    try:
        response = keycloak.get_admin_access_token()
        response.raise_for_status()
        if access_token := response.json().get('access_token', ''):
            admin_access_token = access_token
        else:
            raise requests.exceptions.RequestException
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get admin token error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # クライアントUUID取得
    get_client_uuid_result = get_client_uuid(admin_access_token, realm_name)
    if isinstance(get_client_uuid_result, dict):
        return get_client_uuid_result
    else:
        client_uuid = get_client_uuid_result

    # 評価実行(契約情報取得のため)
    response = initialization_response()
    try:
        response = keycloak.evaluate_authorization(admin_access_token, realm_name, client_uuid, user_uuid, resource_url, resource_id)
        response.raise_for_status()

        # 認可を受けるユーザの属性
        user_attribute = response.json()['rpt']['user']
        logger.info("user_attribute: {}".format(user_attribute))
        org_attribute = response.json()['rpt']['org']
        logger.info("org_attribute: {}".format(org_attribute))
        orgs = [x.strip() for x in org_attribute.split(',')]
        aal_attribute = response.json()['rpt']['aal']
        logger.info("aal_attribute: {}".format(aal_attribute))

        # ヒットしたポリシー
        associated_policies = response.json()['results'][0]['policies'][0]['associatedPolicies'] # results = リソース, policies = パーミッション: リソースを指定しているのでそれぞれ1つのみ取れる
        contracts = {}
        for associated_policy in associated_policies:
            # 許可したポリシーかつ契約有ポリシー
            if associated_policy['status'] == 'PERMIT' and "#" in associated_policy['policy']['name']:

                authorized_user = associated_policy['policy']['name'].split('|')[1].strip()
                if user_attribute != authorized_user and authorized_user != 'None':
                    continue
                authorized_org = associated_policy['policy']['name'].split('|')[3].strip()
                if not (authorized_org in orgs) and authorized_org != 'None':
                    continue
                authorized_aal = associated_policy['policy']['name'].split('|')[5].split('#')[0].strip()
                if authorized_aal != 'None':
                    if int(aal_attribute) < int(authorized_aal):
                        continue

                # "タイムスタンプ": "Aggregatedポリシーの説明"
                if len(associated_policy['policy']['description'].split(',')) > 3:
                    contracts[associated_policy['policy']['description'].split(',')[3].strip()] = associated_policy['policy']['description']
                else:
                    contracts['19700101000000000000'] = associated_policy['policy']['description']

        logger.info("contracts: {}".format(contracts))

        contract = ''
        if len(contracts) > 0:
            # 最近の契約を取得
            latest_key = max(contracts)
            contract = contracts[latest_key]

        if contract:
            result['content']['contract']['trade_id'] = contract.split(',')[0].strip()
            result['content']['contract']['contract_url'] = contract.split(',')[1].strip()
            result['content']['contract']['contract_type'] = contract.split(',')[2].strip()
        else:
            result['content']['contract']['trade_id'] = ''
            result['content']['contract']['contract_url'] = ''
            result['content']['contract']['contract_type'] = ''

    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 404
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'evaluate error',
            'detail': f'{response.status_code}: {text}'
        }

    return result


def get_authorization_list(realm_name: str) -> dict:
    """
    main.get_authorization_listから呼び出し
    認可情報一覧の取得

    """

    logger.debug(sys._getframe().f_code.co_name)

    authorization_list = []
    result = {
        'status_code': 200,
        'content': authorization_list
    }

    # アドミントークン取得
    response = initialization_response()
    try:
        response = keycloak.get_admin_access_token()
        response.raise_for_status()
        admin_access_token = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get admin token error',
            'detail': f'{response.status_code}: {text}'
        }
        return result
    
    # クライアントUUID取得
    get_client_uuid_result = get_client_uuid(admin_access_token, realm_name)
    if isinstance(get_client_uuid_result, dict):
        return get_client_uuid_result
    else:
        client_uuid = get_client_uuid_result
    
    # パーミッションUUID一覧を取得
    permission_list = []
    response = initialization_response()
    try:
        response = keycloak.get_permissions(admin_access_token, realm_name, client_uuid)
        response.raise_for_status()
        for permission in response.json():
            if not permission['name'] == 'Default Permission':
                permission_item = {}
                permission_item['uuid'] = permission['id']
                permission_item['resource_url'] =  unquote(permission['name'])
                permission_list.append(permission_item)
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get permissions error',
            'detail': f'{response.status_code}: {text}'
        }

    # レスポンスとなる認可情報一覧を作成
    get_policies_in_permission_response = initialization_response()
    try:
        for permission in permission_list:
            get_policies_in_permission_response = keycloak.get_policies_in_permission(admin_access_token, realm_name, client_uuid, permission['uuid'])
            for policy in get_policies_in_permission_response.json():
                authorization = {}
                authorization['permission'] = {}
                authorization['permission']['assignee'] = {}
                splitted_name = re.split('[|#]', policy['name'])
                if (user := splitted_name[1]) != 'None':
                    authorization['permission']['assignee']['user'] = user
                if (org := splitted_name[3]) != 'None':
                    authorization['permission']['assignee']['org'] = org
                if (aal := splitted_name[5]) != 'None':
                    authorization['permission']['assignee']['aal'] = aal
                authorization['permission']['target'] = permission['resource_url']
                authorization['permission']['assigner'] = realm_name
                if len(splitted_name) == 9: # 1: user_k, 2: user_v, 3: org_k, 4: org_v, 5: aal_k, 6: aal_v, 7: extras_k, 8: extras_v, 9: contract
                    splitted_description = re.split(',', policy['description'])
                    authorization['contract'] = {}
                    authorization['contract']['trade_id'] = splitted_description[0]
                    authorization['contract']['contract_url'] = splitted_description[1]
                    authorization['contract']['contract_type'] = splitted_description[2]
                authorization_list.append(authorization)

    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = get_policies_in_permission_response.text if get_policies_in_permission_response.text else get_policies_in_permission_response.code
        result['content'] = {
            'message': 'get policies error',
            'detail': f'{get_policies_in_permission_response.status_code}: {text}'
        }

    return result


def get_authorization(realm_name: str, resource_url: str) -> dict:
    """
    main.get_authorizationから呼び出し
    認可情報一覧の取得

    """

    logger.debug(sys._getframe().f_code.co_name)

    authorization_list = []
    result = {
        'status_code': 200,
        'content': authorization_list
    }

    # URLエンコードする
    encoded_resource_url = quote(resource_url, safe='')

    # アドミントークン取得
    response = initialization_response()
    try:
        response = keycloak.get_admin_access_token()
        response.raise_for_status()
        admin_access_token = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get admin token error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # クライアントUUID取得
    get_client_uuid_result = get_client_uuid(admin_access_token, realm_name)
    if isinstance(get_client_uuid_result, dict):
        return get_client_uuid_result
    else:
        client_uuid = get_client_uuid_result

    # パーミッションUUID一覧を取得
    permission_list = []
    response = initialization_response()
    try:
        response = keycloak.get_permissions(admin_access_token, realm_name, client_uuid)
        response.raise_for_status()
        for permission in response.json():
            # 所望のリソースURLのものだけを取得（パーミッション名はリソースURL）
            if permission['name'] == encoded_resource_url:
                permission_item = {}
                permission_item['uuid'] = permission['id']
                permission_item['resource_url'] =  unquote(permission['name'])
                permission_list.append(permission_item)
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get permissions error',
            'detail': f'{response.status_code}: {text}'
        }

    # レスポンスとなる認可情報一覧を作成
    get_policies_in_permission_response = initialization_response()
    try:
        for permission in permission_list:
            get_policies_in_permission_response = keycloak.get_policies_in_permission(admin_access_token, realm_name, client_uuid, permission['uuid'])
            for policy in get_policies_in_permission_response.json():
                authorization = {}
                authorization['permission'] = {}
                authorization['permission']['assignee'] = {}
                splitted_name = re.split('[|#]', policy['name'])
                if (user := splitted_name[1]) != 'None':
                    authorization['permission']['assignee']['user'] = user
                if (org := splitted_name[3]) != 'None':
                    authorization['permission']['assignee']['org'] = org
                if (aal := splitted_name[5]) != 'None':
                    authorization['permission']['assignee']['aal'] = aal
                authorization['permission']['target'] = permission['resource_url']
                authorization['permission']['assigner'] = realm_name
                if len(splitted_name) == 9: # 1: user_k, 2: user_v, 3: org_k, 4: org_v, 5: aal_k, 6: aal_v, 7: extras_k, 8: extras_v, 9: contract
                    splitted_description = re.split(',', policy['description'])
                    authorization['contract'] = {}
                    authorization['contract']['trade_id'] = splitted_description[0]
                    authorization['contract']['contract_url'] = splitted_description[1]
                    authorization['contract']['contract_type'] = splitted_description[2]
                authorization_list.append(authorization)

    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = get_policies_in_permission_response.text if get_policies_in_permission_response.text else get_policies_in_permission_response.code
        result['content'] = {
            'message': 'get policies error',
            'detail': f'{get_policies_in_permission_response.status_code}: {text}'
        }

    return result


def register_authorization(realm_name: str, resource_url: str, policies: dict, contract: str) -> dict:
    """
    main.register_authorizationから呼び出し
    main.ui_register_authorizationから呼び出し
    認可を登録する
    """
    logger.debug(sys._getframe().f_code.co_name)

    result = {
        'status_code': 200,
        'content': {'message': 'success'}
    }

    # リソースURLのURLエンコード
    resource_url = quote(resource_url, safe='')

    # アドミントークン取得
    response = initialization_response()
    try:
        response = keycloak.get_admin_access_token()
        response.raise_for_status()
        admin_access_token = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get admin token error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # クライアントUUID取得
    get_client_uuid_result = get_client_uuid(admin_access_token, realm_name)
    if isinstance(get_client_uuid_result, dict):
        return get_client_uuid_result
    else:
        client_uuid = get_client_uuid_result

    # リソースを検索
    response = initialization_response()
    try:
        response = keycloak.search_resources(admin_access_token, realm_name, client_uuid, resource_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'search resources error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # リソースがすでに存在する場合
    if response.json():
        resource_uuid = response.json()[0]['_id']
    # リソースが存在しない場合
    else:
        response = initialization_response()
        try:
            # リソース作成
            response = keycloak.create_resource(admin_access_token, realm_name, client_uuid, resource_url)
            response.raise_for_status()
            if _id := response.json().get('_id', ''):
                resource_uuid = _id
            else:
                raise requests.exceptions.RequestException
        except requests.exceptions.RequestException as e:
            result['status_code'] = 500
            text = response.text if response.text else response.code
            result['content'] = {
                'message': 'create resource error',
                'detail': f'{response.status_code}: {text}'
            }
            return result

    regex_policy_uuid_list = []
    for policy_claim, policy_pattern in policies.items():
        if policy_pattern is not None:
            policy_name = f'{policy_claim}|{policy_pattern}'
            # RegExポリシー検索
            response = initialization_response()
            try:
                response = keycloak.search_policy(admin_access_token, realm_name, client_uuid, 'regex', policy_name)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                result['status_code'] = 500
                text = response.text if response.text else response.code
                result['content'] = {
                    'message': 'search policy error',
                    'detail': f'{response.status_code}: {text}'
                }
                return result

            regex_policy_uuid = ''
            for policy in response.json():
                if policy_name == policy['name']:
                    regex_policy_uuid = policy['id']
            if not regex_policy_uuid:
                # Regexポリシー作成
                # orgの場合は部分一致の正規表現を書く
                if policy_claim == 'org':
                    # ピリオドをエスケープ
                    policy_pattern = policy_pattern.replace('.', r'\.')
                    # 正規表現(例: ^.*cadde\.aaa\.aa.*$)
                    policy_pattern = '^.*' + policy_pattern + '.*$'

                # aalの場合はそのレベル以上のものを許可する
                if policy_claim == 'aal':
                    if policy_pattern == 1:
                        policy_pattern = '[123]'
                    elif policy_pattern == 2:
                        policy_pattern = '[23]'
                    elif policy_pattern == 3:
                        policy_pattern = '[3]'
                    else:
                        logger.info(policy_pattern)
                        result['status_code'] = 400
                        result['content'] = {
                            'message': 'specify aal 1～3',
                            'detail': f''
                        }
                        return result
                response = initialization_response()
                try:
                    response = keycloak.create_regex_policy(admin_access_token, realm_name, client_uuid, policy_name, policy_claim, policy_pattern)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    result['status_code'] = 500
                    text = response.text if response.text else response.code
                    result['content'] = {
                        'message': 'create regex policy error',
                        'detail': f'{response.status_code}: {text}'
                    }
                    return result
                else:
                    regex_policy_uuid = response.json()['id']
            regex_policy_uuid_list.append(regex_policy_uuid)

    # Aggregatedポリシー名を構築
    # Aggregatedポリシー名形式: user|{user}|org|{org}|aal|{aal}#trade_id
    policy_name = ''
    for policy_claim, policy_pattern in policies.items():
        policy_name += f'{policy_claim}|{policy_pattern}|'
    policy_name = policy_name.rstrip('|')
    # 契約有の場合
    if contract:
        policy_name += '#' + contract.split(',')[0]
    else:
        contract = ',,'

    # タイムスタンプを追加
    contract = contract + ', ' + datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')

    # Aggregatedポリシー検索
    aggregated_policy_uuid = ''
    response = initialization_response()
    try:
        response = keycloak.search_policy(admin_access_token, realm_name, client_uuid, 'aggregate', policy_name)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'search policy error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    for policy in response.json():
        # Aggregatedポリシーがすでにある場合はUUID取得
        if policy_name == policy['name']:
            aggregated_policy_uuid = policy['id']
    if not aggregated_policy_uuid:
        # Aggregatedポリシーがない場合は作成
        response = initialization_response()
        try:
            response = keycloak.create_aggregated_policy(admin_access_token, realm_name, client_uuid, regex_policy_uuid_list, policy_name, policies, contract)
            response.raise_for_status()
            if response.json():
                aggregated_policy_uuid = response.json()['id']
        except requests.exceptions.RequestException as e:
            result['status_code'] = 500
            text = response.text if response.text else response.code
            result['content'] = {
                'message': 'create aggregated policy error',
                'detail': f'{response.status_code}: {text}'
            }
            return result

    # パーミッションを検索
    # パーミッション名 = リソースURL
    response = initialization_response()
    try:
        response = keycloak.search_permission(admin_access_token, realm_name, client_uuid, resource_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'search permission error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    permission_uuid = ''
    if response.json():
        for permission in response.json():
            if permission['name'] == resource_url:
                permission_uuid = permission['id']

    # パーミッション更新
    if permission_uuid:
        response = initialization_response()
        try:
            response = keycloak.get_policies_in_permission(admin_access_token, realm_name, client_uuid, permission_uuid)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            result['status_code'] = 500
            text = response.text if response.text else response.code
            result['content'] = {
                'message': 'get policies in permission error',
                'detail': f'{response.status_code}: {text}'
            }
            return result

        policy_uuid_list = []
        for policy_object in response.json():
            policy_uuid_list.append(policy_object['id'])
        policy_uuid_list.append(aggregated_policy_uuid)
        policy_list = list(set(policy_uuid_list))

        permission = initialization_response()
        try:
            permission = keycloak.update_permission(admin_access_token, realm_name, client_uuid, permission_uuid, resource_url, resource_uuid, policy_list)
        except requests.exceptions.RequestException as e:
            result['status_code'] = 500
            text = permission.text if permission.text else permission.code
            result['content'] = {
                'message': 'update permission error',
                'detail': f'{permission.status_code}: {text}'
            }
            return result
    # パーミッション新規作成
    else:
        response = initialization_response()
        try:
            response = keycloak.create_permission(admin_access_token, realm_name, client_uuid, resource_url, resource_uuid, aggregated_policy_uuid)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            result['status_code'] = 500
            text = response.text if response.text else response.code
            result['content'] = {
                'message': 'create permissions error',
                'detail': f'{response.status_code}: {text}'
            }
            return result

    return result


def delete_authorization_by_trade_id(realm_name: str, resource_url: str, trade_id: str) -> dict:
    """
    main.delete_authorizationから呼び出し
    契約ありの認可削除
    パーミッション内のAggregatedポリシーの一覧から指定のAggregatedポリシーを取り除いてパーミッションを更新し、取り除いたAggregatedポリシーと関係するRegExポリシーを削除

    """
    logger.debug(sys._getframe().f_code.co_name)

    result = {
        'status_code': 200,
        'content': {'message': 'success'}
    }

    # リソースURLのURLエンコード
    resource_url = quote(resource_url, safe='')

    # アドミントークン取得
    response = initialization_response()
    try:
        response = keycloak.get_admin_access_token()
        response.raise_for_status()
        admin_access_token = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get admin token error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # クライアントUUID取得
    get_client_uuid_result = get_client_uuid(admin_access_token, realm_name)
    if isinstance(get_client_uuid_result, dict):
        return get_client_uuid_result
    else:
        client_uuid = get_client_uuid_result

    # resource_urlでパーミッションを検索
    response = initialization_response()
    try:
        response = keycloak.search_permission(admin_access_token, realm_name, client_uuid, resource_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'search permission error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    permission_uuid = ''
    for permission in response.json():
        if permission['name'] == resource_url:
            permission_uuid = permission['id']
    if not permission_uuid:
        result['status_code'] = 404
        result['content'] = {
            'message': 'not found permission',
            'detail': f'{response.status_code}: {response.text}'
        }
        return result

    # パーミッション内のリソースを取得
    response = initialization_response()
    try:
        response = keycloak.get_resource_in_permission(admin_access_token, realm_name, client_uuid, permission_uuid)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get resource in permission error',
            'detail': f'{response.status_code}: {text}'
        }
        return result
    if response.json():
        resource_url = response.json()[0].get('name', '')
        resource_uuid = response.json()[0].get('_id', '')
    else:
        result['status_code'] = 404
        result['content'] = {
            'message': 'not found resource in permission',
            'detail': f'{response.status_code}: {response.text}'
        }
        return result

    # パーミッション内のポリシーを取得し、trade_idが付与されたポリシーを取り外す
    response = initialization_response()
    try:
        response = keycloak.get_policies_in_permission(admin_access_token, realm_name, client_uuid, permission_uuid)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get policy in permission error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    policy_uuid_list = []
    removed_policy_uuid = ''
    found_policy = False
    for policy in response.json():
        # 指定された取引IDを持つポリシーはpolicy_uuid_listに入れずスキップすることで取り外す
        if policy['name'].endswith('#' + trade_id):
            found_policy = True
            removed_policy_uuid = policy['id']
            continue
        else:
        # その他のポリシーは取り外さずそのまま
            policy_uuid_list.append(policy['id'])
    if not found_policy:
        result['status_code'] = 404
        result['content'] = {
            'message': 'not found policy in permission',
            'detail': f'{response.status_code}: {response.text}'
        }
        return result

    # Aggregatedポリシーをひとつも持たなくなったパーミッションを削除する
    # リソースを削除することで、連鎖的にパーミッションを削除する
    if not policy_uuid_list:
        response = initialization_response()
        try:
            response = keycloak.delete_resource(admin_access_token, realm_name, client_uuid, resource_uuid)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            result['status_code'] = 500
            text = response.text if response.text else response.code
            result['content'] = {
                'message': 'delete permissions error',
                'detail': f'{response.status_code}: {text}'
            }
    # Aggregatedポリシーが残っている場合はパーミッションを更新
    else:
        response = initialization_response()
        try:
            response = keycloak.update_permission(admin_access_token, realm_name, client_uuid, permission_uuid, resource_url, resource_uuid, policy_uuid_list)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            result['status_code'] = 500
            text = response.text if response.text else response.code
            result['content'] = {
                'message': 'update permissions error',
                'detail': f'{response.status_code}: {text}'
            }

    # 取り外したAggregatedポリシーを削除（その中のRegExポリシーも削除）
    delete_aggregated_policy(admin_access_token, realm_name, client_uuid, removed_policy_uuid)

    return result


def delete_authorization_by_policies(realm_name: str, resource_url: str, policies: dict) -> dict:
    """
    main.delete_authorizationから呼び出し
    契約なし認可の削除
    ポリシーから削除すべき認可を特定する

    """
    logger.debug(sys._getframe().f_code.co_name)

    result = {
        'status_code': 200,
        'content': {'message': 'success'}
    }

    # リソースURLのURLエンコード
    resource_url = quote(resource_url, safe='')

    # アドミントークン取得
    response = initialization_response()
    try:
        response = keycloak.get_admin_access_token()
        response.raise_for_status()
        admin_access_token = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        #result['status_code'] = 403
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get admin token error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # クライアントUUID取得
    get_client_uuid_result = get_client_uuid(admin_access_token, realm_name)
    if isinstance(get_client_uuid_result, dict):
        return get_client_uuid_result
    else:
        client_uuid = get_client_uuid_result

    # resource_urlでパーミッションを検索
    response = initialization_response()
    try:
        response = keycloak.search_permission(admin_access_token, realm_name, client_uuid, resource_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'search permission error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    permission_uuid = ''
    for permission in response.json():
        if permission['name'] == resource_url:
            permission_uuid = permission['id']
    if not permission_uuid:
        result['status_code'] = 404
        result['content'] = {
            'message': 'not found permission',
            'detail': f'{response.status_code}: {response.text}'
        }
        return result

    # パーミッション内のリソースを取得
    response = initialization_response()
    try:
        response = keycloak.get_resource_in_permission(admin_access_token, realm_name, client_uuid, permission_uuid)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get resource in permission error',
            'detail': f'{response.status_code}: {text}'
        }
        return result
    if response.json():
        resource_url = response.json()[0].get('name', '')
        resource_uuid = response.json()[0].get('_id', '')
    else:
        result['status_code'] = 404
        result['content'] = {
            'message': 'not found resource in permission',
            'detail': f'{response.status_code}: {response.text}'
        }
        return result

    # パーミッション内のAggregatedポリシーを取得する
    response = initialization_response()
    try:
        response = keycloak.get_policies_in_permission(admin_access_token, realm_name, client_uuid, permission_uuid)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get resource in permission error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # 削除すべきAggregatedポリシーの名前を生成
    policy_name_to_be_removed = ''
    for policy_claim, policy_pattern in policies.items():
        policy_name_to_be_removed += f'{policy_claim}|{policy_pattern}|'
    policy_name_to_be_removed = policy_name_to_be_removed.rstrip('|')

    logger.info(policy_name_to_be_removed)

    # Aggregatedポリシーを取り外す
    found_policy = False
    policy_uuid_list = []
    removed_policy_uuid = ''
    for policy in response.json():
        # 指定された取引IDを持つポリシーはpolicy_uuid_listに入れずスキップすることで取り外す
        if policy['name'] == policy_name_to_be_removed:
            found_policy = True
            removed_policy_uuid = policy['id']
            continue
        else:
        # その他のポリシーは取り外さずそのまま
            policy_uuid_list.append(policy['id'])
    if not found_policy:
        result['status_code'] = 404
        result['content'] = {
            'message': 'not found policy in permission',
            'detail': f'{response.status_code}: {response.text}'
        }
        return result

    # Aggregatedポリシーをひとつも持たなくなったパーミッションを削除する
    # リソースを削除することで、連鎖的にパーミッションを削除する
    if not policy_uuid_list:
        response = initialization_response()
        try:
            response = keycloak.delete_resource(admin_access_token, realm_name, client_uuid, resource_uuid)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            result['status_code'] = 500
            text = response.text if response.text else response.code
            result['content'] = {
                'message': 'delete permissions error',
                'detail': f'{response.status_code}: {text}'
            }
    # Aggregatedポリシーが残っている場合はパーミッションを更新
    else:
        response = initialization_response()
        try:
            response = keycloak.update_permission(admin_access_token, realm_name, client_uuid, permission_uuid, resource_url, resource_uuid, policy_uuid_list)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            result['status_code'] = 500
            text = response.text if response.text else response.code
            result['content'] = {
                'message': 'update permissions error',
                'detail': f'{response.status_code}: {text}'
            }

    # 取り外したAggregatedポリシーを削除（その中のRegExポリシーも削除）
    delete_aggregated_policy(admin_access_token, realm_name, client_uuid, removed_policy_uuid)

    return result


def get_token_using_authorization_code(authorization_header_value, code, redirect_uri) -> dict:
    """
    main.get_token_using_authorization_codeから呼び出し
    認可コードを使ってアクセストークンを取得する
    """

    result = {
        'tokens': {
            'id_token': '',
            'access_token': '',
            'refresh_token': ''
        },
        'status_code': 200,
        'content': {'message': 'success'}
    }

    response = initialization_response()
    try:
        response = keycloak.get_token_using_authorization_code(authorization_header_value, code, redirect_uri)
        response.raise_for_status()
        result['tokens']['id_token'] = response.json()['id_token']
        result['tokens']['access_token'] = response.json()['access_token']
        result['tokens']['refresh_token'] = response.json()['refresh_token']

    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get token error(type:authorization_code)',
            'detail': f'{response.status_code}: {text}'
        }

    return result


def logout_from_keycloak(session_id: str) -> dict:
    """
    main.logout_from_keycloakから呼び出し
    """
    logger.debug(sys._getframe().f_code.co_name)

    result = {
        'status_code': 200,
        'content': {'message': 'success'}
    }

    # Authorizationヘッダ
    client_id = settings.client_id
    client_secret = settings.client_secret
    credentials = f'{client_id}:{client_secret}'
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    authorization_header_value = f'Basic {encoded_credentials}'

    # リフレッシュトークン取得
    if refresh_token := main.token_dict.get(session_id, {}).get('refresh_token', ''):
        logger.debug("refresh_token: {}".format(refresh_token))
    else:
        result['status_code'] = 404
        result['content']['message'] = 'not found refresh token'
        return result

    response = initialization_response()
    try:
        response = keycloak.logout_from_keycloak(authorization_header_value, refresh_token)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'keycloak logout error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # サーバが保存しているトークン削除
    deleted_tokens = main.token_dict.pop(session_id)
    logger.debug("deleted_tokens: {}".format(deleted_tokens))

    return result


def get_settings(realm_name: str) -> dict:
    """
    認可機能の設定を取得する
        - レルムの設定
        - クライアント(提供者コネクタ)の設定
        - アイデンティティプロバイダー(認証機能)の設定
    """
    logger.debug(sys._getframe().f_code.co_name)

    fetched_settings = {}
    result = {
        'status_code': 200,
        'content': fetched_settings
    }

    # アドミントークン取得
    response = initialization_response()
    try:
        response = keycloak.get_admin_access_token()
        response.raise_for_status()
        admin_access_token = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get admin token error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # レルム設定の取得
    response = initialization_response()
    try:
        response = keycloak.get_realm_settings(admin_access_token, realm_name)
        response.raise_for_status()
        realm_settings = {}
        realm_settings['access_token_lifespan'] = response.json()['accessTokenLifespan']
        fetched_settings['realm_settings'] =  realm_settings
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 404
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get realm error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # クライアントUUID取得
    client_settings = {}
    get_client_uuid_result = get_client_uuid(admin_access_token, realm_name)
    if isinstance(get_client_uuid_result, dict):
        return get_client_uuid_result
    else:
        client_uuid = get_client_uuid_result
        client_settings['client_uuid'] = client_uuid

    client_settings['client_id'] = settings.provider_connector_id

    # クライアントシークレットの取得
    response = initialization_response()
    try:
        response = keycloak.get_client_secret(admin_access_token, realm_name, client_settings['client_uuid'])
        response.raise_for_status()
        client_settings['client_secret'] = response.json()['value']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 404
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get client secret error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    fetched_settings['client_settings'] = client_settings

    # アイデンティティプロバイダー(認証機能)設定の取得
    response = initialization_response()
    try:
        response = keycloak.get_idp_settings(admin_access_token, realm_name)
        response.raise_for_status()
        current_idp_settings = response.json()
        idp_settings = {}
        idp_settings['auth_url'] = current_idp_settings['config']['authorizationUrl']
        idp_settings['token_url'] = current_idp_settings['config']['tokenUrl']
        idp_settings['userinfo_url'] = current_idp_settings['config']['userInfoUrl']
        idp_settings['client_id'] = current_idp_settings['config']['clientId']
        idp_settings['client_secret'] = current_idp_settings['config']['clientSecret']
        fetched_settings['idp_settings'] = idp_settings
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 404
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get idp settings error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    result['content'] = fetched_settings

    return result


def update_realm_settings(realm_name: str, realm_settings_request: dict) -> dict:
    """
    main.update_realm_settingsから呼び出し
    レルムを更新
    """
    logger.debug(sys._getframe().f_code.co_name)

    result = {
        'status_code': 200,
        'content': {'message': 'success'}
    }

    # アドミントークン取得
    response = initialization_response()
    try:
        response = keycloak.get_admin_access_token()
        response.raise_for_status()
        admin_access_token = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get admin token error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # レルム設定の取得
    response = initialization_response()
    try:
        response = keycloak.get_realm_settings(admin_access_token, realm_name)
        response.raise_for_status()
        current_realm_settings = response.json()
        current_realm_settings['accessTokenLifespan'] = realm_settings_request['access_token_lifespan']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 404
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'not found realm',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # レルム設定の更新
    response = initialization_response()
    try:
        response = keycloak.update_realm_settings(admin_access_token, realm_name, current_realm_settings)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] =  {
            'message': 'update realm settings error',
            'detail': f'{response.status_code}: {text}'
        }

    return result


def update_idp_settings(realm_name: str, idp_settings_request: dict) -> dict:
    """
    アイデンティティプロバイダーを更新
    """
    logger.debug(sys._getframe().f_code.co_name)

    result = {
        'status_code': 200,
        'content': {'message': 'success'}
    }

    # アドミントークン取得
    response = initialization_response()
    try:
        response = keycloak.get_admin_access_token()
        response.raise_for_status()
        admin_access_token = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get admin token error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # アイデンティティプロバイダー設定を取得
    response = initialization_response()
    try:
        response = keycloak.get_idp_settings(admin_access_token, realm_name)
        response.raise_for_status()
        idp_settings = response.json()
        idp_settings['config']['userInfoUrl'] = idp_settings_request['userinfo_url']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 404
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'not found idp settings',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # アイデンティティプロバイダー設定を更新
    response = initialization_response()
    try:
        response = keycloak.update_idp_settings(admin_access_token, realm_name, idp_settings)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 400
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'update idp settings error',
            'detail': f'{response.status_code}: {text}'
        }

    return result


def update_client_secret(realm_name: str) -> dict:
    """
    main.update_client_secretから呼び出し
    クライアントシークレットを更新

    """
    logger.debug(sys._getframe().f_code.co_name)

    result = {
        'status_code': 200,
        'content': {'message': 'success'}
    }

    # アドミントークン取得
    response = initialization_response()
    try:
        response = keycloak.get_admin_access_token()
        response.raise_for_status()
        admin_access_token = response.json()['access_token']
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500 if response.status_code == 500 else 403
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'get admin token error',
            'detail': f'{response.status_code}: {text}'
        }
        return result

    # クライアントUUID取得
    get_client_uuid_result = get_client_uuid(admin_access_token, realm_name)
    if isinstance(get_client_uuid_result, dict):
        return get_client_uuid_result
    else:
        client_uuid = get_client_uuid_result

    # クライアントシークレット更新
    response = initialization_response()
    try:
        response = keycloak.update_client_secret(admin_access_token, realm_name, client_uuid)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        result['status_code'] = 500
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'update client secret error',
            'detail': f'{response.status_code}: {text}'
        }

    return result


def get_client_uuid(admin_access_token, realm_name) -> Union[dict, str]:
    """
    本ファイル内の関数から呼ばれるサブルーチン
    クライアントのUUIDを取得する
    """

    logger.debug(sys._getframe().f_code.co_name)

    response = initialization_response()
    try:
        response = keycloak.get_clients(admin_access_token, realm_name)
        response.raise_for_status()

        # レルムにあるクライアント一覧を取得
        clients = response.json()

        # 設定ファイル記載のクライアントIDがあるかを確認
        for client in clients:
            if client['clientId'] == settings.provider_connector_id:
                return client['id'] # Client UUID

        raise requests.exceptions.RequestException

    except requests.exceptions.RequestException as e:
        result = {}
        result['status_code'] = 500 if response.status_code == 500 else 404
        text = response.text if response.text else response.code
        result['content'] = {
            'message': 'not found client',
            'detail': f'{response.status_code}: {text}'
        }
        return result


def delete_permission(admin_access_token:str, realm_name:str, client_uuid:str, permission_uuid:str, permission_name:str, resource_uuid:str) -> None:
    """
    本ファイル内の関数から呼ばれるサブルーチン
    パーミッションおよびパーミッションの中の全てのAggregatedポリシーを削除する
    """

    logger.debug(sys._getframe().f_code.co_name)

    # パーミッションに含まれる全てのAggregatedポリシーを取得
    aggregated_policy_uuid_list = []
    response = initialization_response()
    try:
        response = keycloak.get_policies_in_permission(admin_access_token, realm_name, client_uuid, permission_uuid)
        response.raise_for_status()
        for policy_object in response.json():
            aggregated_policy_uuid_list.append(policy_object['id'])
    except requests.exceptions.RequestException as e:
        return


    # パーミッションを更新(全てのAggregatedポリシーを取り外す)
    response = initialization_response()
    try:
        response = keycloak.update_permission(admin_access_token, realm_name, client_uuid, permission_uuid, permission_name, resource_uuid, [])
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return

    # 全てのAggregatedポリシー(およびその中のRegExポリシー)を削除
    for aggregated_policy_uuid in aggregated_policy_uuid_list:
        delete_aggregated_policy(admin_access_token, realm_name, client_uuid, aggregated_policy_uuid)

    # パーミッションを削除
    keycloak.delete_permission(admin_access_token, realm_name, client_uuid, permission_uuid)

    return


def delete_aggregated_policy(admin_access_token:str, realm_name:str, client_uuid:str, aggregated_policy_uuid:str) -> None:
    """
    本ファイル内の関数から呼ばれるサブルーチン
    remove_policy_from_permission_by_providerから呼び出し
    delete_permissionから呼び出し
    Aggregatedポリシーの中のRegExポリシーを全て削除する（依存されていないもののみ）
    Aggregatedポリシー→RegExポリシーの順番に削除
    """

    logger.debug(sys._getframe().f_code.co_name)

    # Aggregatedポリシーに含まれるRegExポリシー一覧を取得する
    regex_policy_uuid_list = []
    response = initialization_response()
    try:
        response = keycloak.get_policies_in_policy(admin_access_token, realm_name, client_uuid, aggregated_policy_uuid)
        response.raise_for_status()
        for policy_object in response.json():
            regex_policy_uuid_list.append(policy_object['id'])
    except requests.exceptions.RequestException as e:
        return

    # Aggregatedポリシーを削除
    response = initialization_response()
    try:
        response = keycloak.confirm_policy_dependency(admin_access_token, realm_name, client_uuid, aggregated_policy_uuid)
        response.raise_for_status()
        # 依存関係が空配列なら削除(削除されることが期待値)
        if not response.json():
            response = keycloak.delete_policy(admin_access_token, realm_name, client_uuid, aggregated_policy_uuid)
        else:
            logger.error('not delete aggregated policy(cause: permission dependency)')
            return
    except requests.exceptions.RequestException as e:
        return

    # RegExポリシーを削除
    response = initialization_response()
    try:
        for regex_policy_uuid in regex_policy_uuid_list:
            response = keycloak.confirm_policy_dependency(admin_access_token, realm_name, client_uuid, regex_policy_uuid)
            response.raise_for_status()
            # 依存関係が空配列なら削除(RegExポリシーによって削除されるかどうかが異なる)
            if not response.json():
                keycloak.delete_policy(admin_access_token, realm_name, client_uuid, regex_policy_uuid)
            else:
                logger.error('not delete regex policy(cause: aggregated policy dependency)')
    except requests.exceptions.RequestException as e:
        return

    return


def get_subject_id_from_token(token):
    """
    トークンをデコードしてsubjectを取得する
    """

    splitted_token = token.split('.')
    encoded_payload = splitted_token[1] # [0]: header, [1]: payload, [2]: signature
    encoded_payload += '=' * ((4 - len(encoded_payload) % 4) % 4) # 長さ調整"="で埋める
    decoded_payload = json.loads(base64.urlsafe_b64decode(encoded_payload).decode())
    subject = decoded_payload.get('sub', '')
    logger.debug(json.dumps(decoded_payload, indent=2, ensure_ascii=False))

    return subject

def initialization_response():
    """
    Responseオブジェクトを初期化する
    """

    response = Response()
    response.status_code = 500
    response.code = 'Internal Server Error'
    
    return response
