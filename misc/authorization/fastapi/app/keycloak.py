# keycloak.py
# Keycloakへのアクセス処理

# External packages
import logging
import sys
import os
import copy
import requests
import json
import traceback
#import re
#import ast
from fastapi.responses import JSONResponse
from urllib.parse import quote

# Internal packages
from settings import settings

logger = logging.getLogger(__name__)

logging.getLogger("urllib3").setLevel(logging.CRITICAL)
os.environ['no_proxy'] = '*'


def get_token_using_authorization_code(authorization_header_value: str, code: str, redirect_uri: str) -> requests.models.Response:
    """
    service.get_token_using_authorization_codeから呼び出し
    認可コードを使ってトークンを取得する
    https://openid.net/specs/openid-connect-core-1_0.html#TokenRequest
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authn_keycloak_url + f'/realms/{settings.authn_realm_name}/protocol/openid-connect/token'
    headers = {
        'Authorization': f'{authorization_header_value}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }

    return requests.post(url, headers=headers, data=data)


def federate(authorization_header_value: str, realm_name: str, access_token: str) -> requests.models.Response:
    """
    service.federateから呼び出し
    トークン交換する
    https://www.keycloak.org/docs/latest/securing_apps/#external-token-to-internal-token-exchange
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/realms/{realm_name}/protocol/openid-connect/token'
    headers = {
        'Authorization': f'{authorization_header_value}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'subject_token': access_token,
        'subject_issuer': settings.subject_issuer,
        'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
        'subject_token_type': 'urn:ietf:params:oauth:token-type:access_token',
        'requested_token_type': 'urn:ietf:params:oauth:token-type:access_token'
    }

    return requests.post(url, headers=headers, data=data)


def obtain_pat(authorization_header_value: str, realm_name: str) -> requests.models.Response:
    """
    service.confirm_authorizationから呼び出し
    Client Credentials GrantによりProtection API Token(PAT)を取得
    https://www.keycloak.org/docs/latest/authorization_services/index.html#_service_protection_whatis_obtain_pat
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/realms/{realm_name}/protocol/openid-connect/token'
    headers = {
        'Authorization': f'{authorization_header_value}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
    }

    return requests.post(url, headers=headers, data=data)


def get_resource_id(pat: str, realm_name: str, resource_url: str) -> requests.models.Response:
    """
    service.confirm_authorizationから呼び出し
    リソースIDを取得
    Protectin API
    https://www.keycloak.org/docs/latest/authorization_services/index.html#querying-resources
    """
    logger.debug(sys._getframe().f_code.co_name)

    # URLエンコードしたものをさらにURLエンコードする
    # %を%25にする
    resource_url = quote(resource_url, safe='')

    logger.info(resource_url)
    url = settings.authz_keycloak_url + f'/realms/{realm_name}/authz/protection/resource_set?uri={resource_url}'
    headers = {
        'Authorization': f'Bearer {pat}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    return requests.get(url, headers=headers)


def confirm_authorization(access_token: str, realm_name: str, client_id: str, resource_id: str) -> requests.models.Response:
    """
    service.confirm_authorizationから呼び出し
    認可確認
    https://www.keycloak.org/docs/latest/authorization_services/index.html#_service_obtaining_permissions
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/realms/{realm_name}/protocol/openid-connect/token'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:uma-ticket',
        'permission': resource_id,
        'audience': client_id
    }

    return requests.post(url, headers=headers, data=data)


def evaluate_authorization(admin_access_token: str, realm_name: str, client_uuid: str, user_uuid: str, resource_url: str, resource_id: str) -> requests.models.Response:
    """
    service.confirm_authorizationから呼び出し
    認可確認時に適用されたポリシーの説明(契約関連情報)を取得するために認可を評価する
    https://www.keycloak.org/docs/latest/authorization_services/index.html#_policy_evaluation_overview

    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/policy/evaluate'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {admin_access_token}'
    }
    json = {
        'clientId': client_uuid,
        'userId': user_uuid,
        'resources': [
            {
                'name': resource_url,
                '_id': resource_id
            }
        ]
    }

    return requests.post(url, headers=headers, json=json)


def get_admin_access_token() -> requests.models.Response:
    """
    Adminのアクセストークンを取得
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + '/realms/master/protocol/openid-connect/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'client_id': settings.admin_client_id,
        'username': settings.admin_username,
        'password': settings.admin_password,
        'grant_type': 'password'
    }

    return requests.post(url, headers=headers, data=data)


def get_clients(admin_access_token: str, realm_name: str) -> requests.models.Response:
    """
    service.get_client_uuidから呼び出し
    レルム内のクライアント一覧を取得
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients'

    return requests.get(url, headers=headers)


def get_permissions(admin_access_token:str, realm_name: str, client_uuid: str) -> requests.models.Response:
    """
    service.get_authorization_listから呼び出し
    service.get_authorizationから呼び出し
    パーミッション一覧を取得
    """
    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/permission'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }

    params = {'max': 10000}

    return requests.get(url, headers=headers, params=params)


def get_realm_settings(admin_access_token: str, realm_name: str) -> requests.models.Response:
    """
    service.get_settingsから呼び出し
    service.update_realm_settingsから呼び出し
    レルムの情報を取得する
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }

    return requests.get(url, headers=headers)


def update_realm_settings(admin_access_token: str, realm_name: str, realm_settings: dict) -> requests.models.Response:
    """
    service.update_realm_settingsから呼び出し
    レルムの情報を更新する
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}'

    return requests.put(url, headers=headers, json=realm_settings)


def get_client_secret(admin_access_token: str, realm_name: str, client_uuid: str) -> requests.models.Response:
    """
    クライアントシークレット取得
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/client-secret'

    return requests.get(url, headers=headers)


def get_idp_settings(access_token: str, realm_name: str) -> requests.models.Response:
    """
    アイデンティティプロバイダー設定を取得
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/identity-provider/instances/authentication'

    return requests.get(url, headers=headers)


def update_idp_settings(admin_access_token: str, realm_name: str, idp_settings: dict) -> requests.models.Response:
    """
    service.update_idp_settingsから呼び出し
    アイデンティティプロバイダー設定を更新
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }

    url  = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/identity-provider/instances/authentication'

    return requests.put(url, headers=headers, json=idp_settings)


def update_client_secret(admin_access_token: str, realm_name: str, client_uuid: str) -> requests.models.Response:
    """
    service.update_client_secretから呼び出し
    クライアントシークレットを更新
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    json = {
        'realm': realm_name,
        'client': client_uuid
    }
    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/client-secret'

    return requests.post(url, headers=headers, json=json)


def search_resources(admin_access_token:str, realm_name: str, client_uuid: str, resource_url:str) -> requests.models.Response:
    """
    service.register_authorizationから呼び出し
    リソースURLでリソースを検索する
    URLエンコードでパーセントもURLエンコードするようにする
    """
    logger.debug(sys._getframe().f_code.co_name)

    # URLエンコードしたものをさらにURLエンコードする
    # %を%25にする
    resource_url = quote(resource_url, safe='')

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/resource?uri={resource_url}'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }

    return requests.get(url, headers=headers)


def create_resource(admin_access_token:str, realm_name:str, client_uuid:str, resource_url:str) -> requests.models.Response:
    """
    service.register_authorizationから呼び出し
    リソース作成
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/resource'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    json = {
        'name': resource_url,
        'uris': [resource_url]
    }

    return requests.post(url, headers=headers, json=json)


def search_policy(admin_access_token: str, realm_name: str, client_uuid: str, policy_type: str, policy_name: str) -> requests.models.Response:
    """
    service.register_authorizationから呼び出し
    ポリシーのUUIDを取得
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/policy/{policy_type}?name={policy_name}'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }

    return requests.get(url, headers=headers)


def create_regex_policy(admin_access_token: str, realm_name: str, client_uuid: str, policy_name: str, policy_claim: str, policy_pattern: str) -> requests.models.Response:
    """
    service.register_authorizationから呼び出し
    Regexポリシー作成
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/policy/regex'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    json = {
        'name': policy_name,
        'description': '',
        'type': 'regex',
        'targetClaim': policy_claim,
        'pattern': policy_pattern,
        'decisionStrategy': 'UNANIMOUS', # 論理積
        'logic': 'POSITIVE'
    }

    return requests.post(url, headers=headers, json=json)


def create_aggregated_policy(admin_access_token: str, realm_name: str, client_uuid: str, policy_uuid_list: list, aggregated_policy_name: str, policies: dict, contract: str) -> requests.models.Response:
    """
    service.register_authorizationから呼び出し
    Aggregatedポリシー作成
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/policy/aggregate'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    json = {
        'name': aggregated_policy_name,
        'description': contract,
        'type': 'aggregate',
        'policies': policy_uuid_list,
        'decisionStrategy': 'UNANIMOUS', # 論理積
        'logic': 'POSITIVE'
    }

    return requests.post(url, headers=headers, json=json)


def search_permission(admin_access_token: str, realm_name: str, client_uuid: str, resource_url: str) -> requests.models.Response:
    """
    service.register_authorizationから呼び出し
    service.delete_authorization_by_trade_id
    service.delete_authorization_by_policies
    名前指定によるパーミッション取得
    URLエンコードでパーセントもURLエンコードするようにする
    """
    logger.debug(sys._getframe().f_code.co_name)

    # リソースURLのURLエンコード
    resource_url = quote(resource_url, safe='')

    # パーミッション名 = リソースURLであることに注意
    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/permission/resource?name={resource_url}'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }

    return requests.get(url, headers=headers)


def get_policies_in_permission(admin_access_token: str, realm_name: str, client_uuid: str, permission_uuid: str) -> requests.models.Response:
    """
    service.get_authorization_listから呼び出し
    service.get_authorizationから呼び出し
    service.register_authorizationから呼び出し
    service.delete_authorization_by_trade_id
    service.delete_authorization_by_policies
    パーミッション内のポリシーを取得

    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/policy/{permission_uuid}/associatedPolicies'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }

    return requests.get(url, headers=headers)


def get_policies_in_policy(admin_access_token: str, realm_name: str, client_uuid: str, policy_uuid: str) -> requests.models.Response:
    """
    service.delete_aggregated_policyから呼び出し
    ポリシー(Aggregatedポリシー)内のポリシー(RegExポリシー)を取得

    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/policy/{policy_uuid}/associatedPolicies'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }

    return requests.get(url, headers=headers)


def get_resource_in_permission(admin_access_token: str, realm_name: str, client_uuid: str, permission_uuid: str) -> requests.models.Response:
    """
    service.register_authzから呼び出し
    service.delete_authorization_by_trade_id
    service.delete_authorization_by_policies
    パーミッション内のリソースオブジェクトを取得
    パーミッションとリソースは1:1の関係

    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/permission/{permission_uuid}/resources'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }

    return requests.get(url, headers=headers)


def create_permission(admin_access_token: str, realm_name: str, client_uuid: str, resource_url: str, resource_uuid: str, policy_uuid: str) -> requests.models.Response:
    """
    service.register_authorizationから呼び出し
    パーミッション作成
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/permission'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    json = {
        'name': resource_url,
        'resources': [resource_uuid],
        'policies': [policy_uuid],
        'type': 'resource',
        'logic': 'POSITIVE',
        'decisionStrategy': 'AFFIRMATIVE' # 論理和
    }

    return requests.post(url, headers=headers, json=json)


def update_permission(admin_access_token: str, realm_name: str, client_uuid: str, permission_uuid: str, resource_url: str, resource_id: str, policies: list) -> requests.models.Response:
    """
    service.register_authorizationから呼び出し
    service.delete_authorization_by_trade_id
    service.delete_authorization_by_policies
    パーミッション更新
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/permission/resource/{permission_uuid}'
    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    json = {
        'id': permission_uuid,
        'name': resource_url,
        'resources': [resource_id],
        'policies': policies,
        'type': 'resource',
        'logic': 'POSITIVE',
        'decisionStrategy': 'AFFIRMATIVE' # 論理和
    }

    return requests.put(url, headers=headers, json=json)


def confirm_policy_dependency(admin_access_token:str, realm_name:str, client_uuid:str, policy_uuid:str) -> requests.models.Response:
    """
    service.delete_aggregated_policyから呼び出し
    削除しようとしているポリシーに依存しているパーミッションなどがないかを確認する
    依存しているパーミッションがないと、空配列が得られる
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    url =  settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/policy/{policy_uuid}/dependentPolicies'

    return requests.get(url, headers=headers)


def confirm_resource_dependency(admin_access_token:str, realm_name:str, client_uuid:str, resource_uuid:str) -> requests.models.Response:
    """
    service.delete_authz_resourceから呼び出し
    削除しようとしているリソースに依存しているパーミッションを確認する
    依存しているパーミッションがないと、空配列が得られる
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    url =  settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/resource/{resource_uuid}/permissions'

    return requests.get(url, headers=headers)


def delete_permission(admin_access_token:str, realm_name:str, client_uuid:str, permission_uuid:str) -> requests.models.Response:
    """
    パーミッションを削除する
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    url =  settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/policy/{permission_uuid}'

    return requests.delete(url, headers=headers)


def delete_policy(admin_access_token:str, realm_name:str, client_uuid:str, policy_uuid:str) -> requests.models.Response:
    """
    ポリシーを削除する
    service.delete_aggregated_policyから呼び出し
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    url =  settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/policy/{policy_uuid}'

    return requests.delete(url, headers=headers)


def delete_resource(admin_access_token:str, realm_name:str, client_uuid:str, resource_uuid: str) -> requests.models.Response:
    """
    service.delete_authorization_by_trade_idから呼び出し
    service.delete_authorization_by_policiesから呼び出し
    リソースUUIDを指定してリソースを削除する
    リソースを削除すると、そのリソースに紐づいたパーミッションも自動的に削除される
    """
    logger.debug(sys._getframe().f_code.co_name)

    headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    url = settings.authz_keycloak_url + f'/admin/realms/{realm_name}/clients/{client_uuid}/authz/resource-server/resource/{resource_uuid}'

    return requests.delete(url, headers=headers)


def logout_from_keycloak(authorization_header_value: str, refresh_token: str) -> requests.models.Response:
    """
    service.logout_from_keycloakから呼び出し
    """
    logger.debug(sys._getframe().f_code.co_name)

    url = settings.authn_keycloak_url + f'/realms/{settings.authn_realm_name}/protocol/openid-connect/logout'
    headers = {
        'Authorization': authorization_header_value,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'refresh_token': refresh_token
    }

    return requests.post(url, headers=headers, data=data)
