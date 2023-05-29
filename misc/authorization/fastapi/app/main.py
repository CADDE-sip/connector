# main.py
# API定義
# 主な処理ロジックはservice.pyに記述

# External packages
import sys
import logging
import json
from fastapi import FastAPI, status, Header, Request, Body, Depends, HTTPException, Cookie
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import List, Union
import uvicorn
import requests
import base64
import string
import random
import urllib
import traceback

# Internal packages
from settings import settings
import schemas
import service

# Logging settings
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# キー: {認可コード}
# バリュー: {'access_token': '{アクセストークン}', 'refresh_token': '{リフレッシュトークン}', 'id_token': {IDトークン}}
token_dict = {}

# state list
auth_state_list = []

# FastAPI instance
app = FastAPI(
    title = settings.title,
    description = settings.description,
    version = settings.version,
    openapi_tags = settings.tags_metadata
)

@app.exception_handler(HTTPException)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=403,
        content={'message': 'Forbidden access'}
    )


# 共通処理
# common_processes

def verify_access_token(authorization: str = Header(...)):
    """
    認可API(Authorization)共通処理
    アクセストークン(契約管理トークン)が有効かをチェックする
    """
    logger.info(sys._getframe().f_code.co_name)

    url = settings.authn_url + '/token/introspect'

    credential = f'{settings.client_id}:{settings.client_secret}'
    basic = base64.b64encode(credential.encode()).decode()
    headers = {
        'Authorization': f'Basic {basic}',
        'Content-Type': 'application/json'
    }
    json = {
        'access_token': authorization[len('Bearer '):]
    }
    try:
        response = requests.post(url, headers=headers, json=json)
        response.raise_for_status()
        return
    except requests.exceptions.RequestException as e:
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=403)


def verify_session(request: Request):
    """
    認可画面用API(ProviderUI)共通処理
    Webブラウザがヘッダで渡してくるセッションCookieが有効かをチェックする
    有効だった場合、CADDEユーザID(提供者)を返す
    """
    logger.info(sys._getframe().f_code.co_name)

    session_id = request.cookies.get('session_id')
    if access_token := token_dict.get(session_id, {}).get('access_token', ''):
        logger.debug("access_token: {}".format(access_token))
        return get_cadde_user_id_from_token(access_token)

    raise HTTPException(status_code=403)


def get_cadde_user_id_from_token(token):
    """
    verify_sessionから呼び出し
    トークンをデコードしてCADDEユーザID(提供者)を取得する
    """

    splitted_token = token.split('.')
    encoded_payload = splitted_token[1] # [0]: header, [1]: payload, [2]: signature
    encoded_payload += '=' * ((4 - len(encoded_payload) % 4) % 4) # 長さ調整"="で埋める
    decoded_payload = json.loads(base64.urlsafe_b64decode(encoded_payload).decode())
    cadde_user_id = decoded_payload['preferred_username']
    logger.debug(json.dumps(decoded_payload, indent=2, ensure_ascii=False))

    return cadde_user_id


# 外部API
# external_api

@app.post(
    settings.api_prefix + '/token/federate',
    tags=["Data"],
    include_in_schema=settings.public_api_docs_enabled,
    responses={
        200: {'model': schemas.FederateResponse},
        403: {'model': schemas.ErrorResponse}
    }
)
async def federate(request: schemas.FederateRequest, authorization: str = Header(...)):
    """
    # 認証機能連携(トークン交換)API\n
    提供者コネクタからアクセス\n
    認証機能と連携し、認証トークンと引き換えに認可トークンを取得する\n
    ## API利用説明\n
    クライアント認証はBasic認証により行う\n
    ## APIリクエスト／レスポンス\n
    リクエストヘッダ\n
    Authorizationヘッダ\n
        - Basic {クライアントID}:{クライアントシークレット}をBase64エンコードした文字列\n
    リクエストボディ\n
        - アクセストークン(認証トークン)\n
        - CADDEユーザID(提供者)(=認可機能のレルム名)\n
    """
    logger.info(sys._getframe().f_code.co_name)

    realm_name = request.provider_id
    access_token = request.access_token

    result = service.federate(authorization, realm_name, access_token)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )


@app.post(
    settings.api_prefix + '/authz/confirm',
    tags=["Data"],
    include_in_schema=settings.public_api_docs_enabled,
    responses={
        200: {'model': schemas.ConfirmAuthorizationResponse},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def confirm_authorization(request: schemas.ConfirmAuthorizationRequest, authorization: str = Header(...)):
    """
    # 認可確認API\n
    提供者コネクタからアクセス\n
    認可トークンによりリソースURLにアクセスしてよいかを確認する\n
    ## API利用説明\n
    クライアント認証はBasic認証により行う\n
    ## APIリクエスト／レスポンス\n
    リクエストヘッダ\n
    Authorizationヘッダ\n
        - Basic {クライアントID}:{クライアントシークレット}をBase64エンコードした文字列\n
    リクエストボディ\n
        - アクセストークン(認可トークン)\n
        - CADDEユーザID(提供者)(=認可機能のレルム名)\n
        - リソースURL\n
    """
    logger.info(sys._getframe().f_code.co_name)

    realm_name = request.provider_id
    access_token = request.access_token
    resource_url = request.resource_url
    client_data = base64.b64decode(authorization[len('Basic '):].encode()).decode().split(':')
    client_id = client_data[0]

    result = service.confirm_authorization(authorization, realm_name, client_id, resource_url, access_token)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )


@app.get(
    settings.api_prefix + '/authorization_list',
    dependencies=[Depends(verify_access_token)],
    tags=['Authorization'],
    include_in_schema=settings.public_api_docs_enabled,
    responses={
        200: {'model': List[schemas.GetAuthorizationListResponse]},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def get_authorization_list(assigner: str):
    """
    # 認可情報一覧取得API
    認可情報一覧を取得する\n
    認可情報パラメータはODRLの許可クラスより命名\n
    http://www.asahi-net.or.jp/~ax2s-kmtn/internet/rights/REC-odrl-model-20180215.html#permission\n
    ## API利用説明\n
    本APIを利用するには認証機能が発行したアクセストークンが必要\n
    ## APIリクエスト／レスポンス\n
    リクエストヘッダ\n
    Authorizationヘッダ\n
        - Bearer {アクセストークン(認証トークン)}\n
    クエリパラメータ\n
        - CADDEユーザID(提供者)(assigner)\n
    レスポンスボディ\n
        以下のデータの配列\n
            - 認可情報(permission)\n
                - リソースURL(target)\n
                - CADDEユーザID(提供者)(assigner)\n
                - 認可を与える属性(assignee)\n
                    - ユーザのCADDEユーザID(user) [オプション]\n
                    - 組織のCADDEユーザID(org) [オプション]\n
                    - 当人認証レベル(aal) [オプション] \n
                    - その他の属性(extras) [オプション] \n
            - 契約情報(contract) [オプション]\n
                - 取引ID(trade_id)\n
                - 契約管理サービスURL(contract_url)\n
                - 契約形態(contract_type)\n
    """
    logger.info(sys._getframe().f_code.co_name)

    realm_name = assigner

    result = service.get_authorization_list(realm_name)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )


@app.get(
    settings.api_prefix + '/authorization',
    dependencies=[Depends(verify_access_token)],
    tags=['Authorization'],
    include_in_schema=settings.public_api_docs_enabled,
    responses={
        200: {'model': List[schemas.GetAuthorizationResponse]},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def get_authorization(assigner: str, target: str):
    """
    # 認可情報取得API
    指定したリソースURLの認可情報を取得する\n
    認可情報パラメータはODRLの許可クラスより命名\n
    http://www.asahi-net.or.jp/~ax2s-kmtn/internet/rights/REC-odrl-model-20180215.html#permission\n
    ## API利用説明\n
    本APIを利用するには認証機能が発行したアクセストークンが必要\n
    ## APIリクエスト／レスポンス\n
    リクエストヘッダ\n
    Authorizationヘッダ\n
        - Bearer {アクセストークン(認証トークン)}\n
    クエリパラメータ\n
        - CADDEユーザID(提供者)(assigner)\n
        - リソースURL(target)\n
    レスポンスボディ\n
        以下のデータの配列\n
            - 認可情報(permission)\n
                - リソースURL(target)\n
                - CADDEユーザID(提供者)(assigner)\n
                - 認可を与える属性(assignee)\n
                    - ユーザのCADDEユーザID(user) [オプション]\n
                    - 組織のCADDEユーザID(org) [オプション]\n
                    - 当人認証レベル(aal) [オプション] \n
                    - その他の属性(extras) [オプション] \n
            - 契約情報(contract) [オプション]\n
                - 取引ID(trade_id)\n
                - 契約管理サービスURL(contract_url)\n
                - 契約形態(contract_type)\n
    """
    logger.info(sys._getframe().f_code.co_name)

    realm_name = assigner
    resource_url = target

    result = service.get_authorization(realm_name, resource_url)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )


@app.post(
    settings.api_prefix + '/authorization',
    dependencies=[Depends(verify_access_token)],
    tags=['Authorization'],
    include_in_schema=settings.public_api_docs_enabled,
    responses={
        200: {'model': schemas.Response},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def register_authorization(request: schemas.RegisterAuthorizationRequest):
    """
    # 認可情報登録API\n
    認可情報を登録する\n
    認可情報パラメータはODRLの許可クラスより命名\n
    http://www.asahi-net.or.jp/~ax2s-kmtn/internet/rights/REC-odrl-model-20180215.html#permission\n
    ## API利用説明\n
    本APIを利用するには認証機能が発行したアクセストークンが必要\n
    「認可を与える属性」内の属性は少なくともひとつは指定しなければならない\n
    契約あり認可を登録する場合は、「契約情報」パラメータを付与する\n
    契約なし認可を登録する場合は、「契約情報」パラメータは省略する\n
    ## APIリクエスト／レスポンス\n
    リクエストヘッダ\n
    Authorizationヘッダ\n
        - Bearer {アクセストークン(認証トークン)}\n
    リクエストボディ\n
        - 認可情報(permission)\n
            - リソースURL(target)\n
            - CADDEユーザID(提供者)(assigner)\n
            - 認可を与える属性(assignee)\n
                - ユーザのCADDEユーザID(user) [オプション]\n
                - 組織のCADDEユーザID(org) [オプション]\n
                - 当人認証レベル(aal) [オプション] \n
                - その他の属性(extras) [オプション] \n
        - 契約情報(contract) [オプション]\n
            - 取引ID(trade_id)\n
            - 契約管理サービスURL(contract_url)\n
            - 契約形態(contract_type)\n
    """
    logger.info(sys._getframe().f_code.co_name)

    realm_name = request.permission.assigner
    resource_url = request.permission.target
    policies = request.permission.assignee.dict()

    # 認可を与える属性が少なくともひとつは指定されていることを確認
    if policies['user'] is None and policies['org'] is None and policies['aal'] is None:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({'message': 'attributes for authorization required'})
        )
    else:
        # 契約あり
        if request.contract:
            contract = f'{request.contract.trade_id}, {request.contract.contract_url}, {request.contract.contract_type}'
        # 契約なし
        else:
            contract = ''

        result = service.register_authorization(realm_name, resource_url, policies, contract)

        return JSONResponse(
            status_code=result['status_code'],
            content=jsonable_encoder(result['content'])
        )


@app.delete(
    settings.api_prefix + '/authorization',
    dependencies=[Depends(verify_access_token)],
    tags=['Authorization'],
    include_in_schema=settings.public_api_docs_enabled,
    responses={
        200: {'model': schemas.Response},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def delete_authorization(request: schemas.DeleteAuthorizationRequest):
    """
    # 認可情報削除API
    認可情報を削除する\n
    認可情報パラメータはODRLの許可クラスより命名\n
    http://www.asahi-net.or.jp/~ax2s-kmtn/internet/rights/REC-odrl-model-20180215.html#permission\n
    ## API利用説明
    本APIを利用するには認証機能が発行したアクセストークンが必要\n
    契約あり認可を削除する場合は、「契約情報」パラメータを付与し、「認可を与える属性」パラメータは省略する\n
    契約なし認可を削除する場合は、「契約情報」パラメータを省略し、「認可を与える属性」パラメータを付与する\n
    ## APIリクエスト／レスポンス\n
    リクエストヘッダ\n
    Authorizationヘッダ\n
        - Bearer {アクセストークン(認証トークン)}\n
    リクエストボディ\n
        - 認可情報(permission)\n
            - リソースURL(target)\n
            - CADDEユーザID(提供者)(=認可機能のレルム名)(assigner)\n
            - 認可を与える属性(assignee) [オプション]\n
                - ユーザのCADDEユーザID(user) [オプション]\n
                - 組織のCADDEユーザID(org) [オプション]\n
                - 当人認証レベル(aal) [オプション] \n
                - その他の属性(extras) [オプション] \n
        - 契約情報(contract) [オプション]\n
            - 取引ID(trade_id)\n
    """

    logger.info(sys._getframe().f_code.co_name)

    # リクエストパラメータを内部の変数名に置き換える
    realm_name = request.permission.assigner
    resource_url = request.permission.target

    # 契約なし認可の削除
    if request.contract is None:
        policies = request.permission.assignee.dict()
        result = service.delete_authorization_by_policies(realm_name, resource_url, policies)
    # 契約あり認可の削除
    else:
        trade_id = request.contract.trade_id
        result = service.delete_authorization_by_trade_id(realm_name, resource_url, trade_id)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )

# 内部API
# internal_api

@app.post(
    settings.api_prefix + '/ui/authenticationUrl',
    include_in_schema=settings.private_api_docs_enabled,
    tags=['ProviderUI'],
    responses={
        200: {'model': schemas.GetAuthenticationRequestUrlResponse},
        400: {'model': schemas.ErrorResponse},
        401: {'model': schemas.ErrorResponse}
    }
)
async def ui_get_authentication_request_url(request: schemas.GetAuthenticationRequestUrlRequest):
    """
    # 認証リクエストURL取得API\n
    認可画面からアクセス\n
    認証リクエストURLを取得する\n
    ## APIリクエスト／レスポンス\n
    リクエストボディ\n
        - 認可画面URL\n
    レスポンスボディ\n
        - 認証リクエストURL\n
    """
    logger.info(sys._getframe().f_code.co_name)

    result = {
      'content': {
        'url': ''
      }
    }

    try:
        # コンフィグからkeycloak情報を取得
        keycloak_url = settings.authn_keycloak_url
        keycloak_client_id = settings.client_id

        # keycloakログイン画面からリダイレクトする認証画面のURLをエンコーディングして設定
        redirect_uri = urllib.parse.quote(request.url + settings.ui_redirect_path, safe='')

        # UUID生成
        string_figure = 36
        dat = string.digits + string.ascii_lowercase + string.ascii_uppercase
        authentication_uuid = ''.join([random.choice(dat) for i in range(string_figure)])
        print('authentication_uuid', authentication_uuid)

        # 生成したUUIDを保存
        auth_state_list.append(authentication_uuid)

        # 認証リクエストURLを作成
        result['content']['url'] = keycloak_url + '/realms/' + settings.authn_realm_name + '/protocol/openid-connect/auth?client_id=' + keycloak_client_id \
            + '&redirect_uri=' + redirect_uri + '&response_mode=fragment&response_type=code&scope=openid&state=' + authentication_uuid

    except Exception:
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={'message': 'create_keycloak_redirect_uri_Exception'})

    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(result['content'])
    )

@app.post(
    settings.api_prefix + '/ui/token/authorizationCode',
    include_in_schema=settings.private_api_docs_enabled,
    tags=['ProviderUI'],
    responses={
        200: {'model': schemas.GetTokenUsingAuthorizationCodeResponse},
        403: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def ui_get_token_using_authorization_code(request: schemas.GetTokenUsingAuthorizationCodeRequest):
    """
    # 認可コードグラントによるトークン取得API\n
    認可機能画面からアクセス\n
    state検証を行い、認可コードを使ってアクセストークンを取得する\n
    取得したアクセストークンはAPIで保持する\n
    ## APIリクエスト／レスポンス\n
    リクエストボディ\n
        - 認可コード\n
        - リダイレクトURI\n
        - state\n
    レスポンスボディ\n
        - CADDEユーザID(提供者)\n
    """
    logger.info(sys._getframe().f_code.co_name)

    # state検証
    state = request.state
    if state in auth_state_list:
        auth_state_list.remove(state)
    else:
        return JSONResponse(
            status_code = 400,
            content = {'message': 'Request parameter error (state)'}
        )

    # Authorizationヘッダの値を作成
    client_id = settings.client_id
    client_secret = settings.client_secret
    credentials = f'{client_id}:{client_secret}'
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    authorization_header_value = f'Basic {encoded_credentials}'

    # トークンを取得
    code = request.code
    redirect_uri = request.url + settings.ui_redirect_path
    try:
        result = service.get_token_using_authorization_code(authorization_header_value, request.code, redirect_uri)
    except requests.exceptions.RequestException as e:
        return JSONResponse(
            status_code=result['status_code'],
            content=jsonable_encoder(result['content'])
        )

    # トークンを保持
    tokens = {
        'id_token': result['tokens']['id_token'],
        'access_token': result['tokens']['access_token'],
        'refresh_token': result['tokens']['refresh_token']
    }
    logger.debug(json.dumps(token_dict, indent=2, ensure_ascii=False))
    token_dict[code] = tokens

    result['content']['cadde_user_id'] = get_cadde_user_id_from_token(result['tokens']['access_token'])

    # レスポンス
    response = JSONResponse(
        status_code=result['status_code'],
        content=result['content']
    )
    response.set_cookie(key='session_id', value=code)

    return response


@app.get(
    settings.api_prefix + '/ui/logout',
    tags=['ProviderUI'],
    include_in_schema=settings.private_api_docs_enabled,
    responses={
        200: {'model': schemas.Response},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def ui_logout(request: Request):
    """
    # データ提供者用 ログアウトAPI
    """

    session_id = request.cookies.get('session_id')

    result = service.logout_from_keycloak(session_id)

    response = JSONResponse(
        status_code=result['status_code'],
        content=result['content']
    )

    # Cookieクリア
    response.set_cookie(key='session_id', value='')

    return response


@app.get(
    settings.api_prefix + '/ui/settings',
    tags=["ProviderUI"],
    include_in_schema=settings.private_api_docs_enabled,
    responses={
        200: {'model': schemas.GetSettingsResponse},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def ui_get_settings(cadde_user_id: str = Depends(verify_session)):
    """
    # データ提供者用 設定取得API\n
    認可機能画面からアクセス\n
    ## API利用説明\n
    本APIを利用するにはセッションCookieが必要\n
    """
    logger.info(sys._getframe().f_code.co_name)

    result = service.get_settings(cadde_user_id)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )


@app.put(
    settings.api_prefix + '/ui/settings/realm',
    tags=["ProviderUI"],
    include_in_schema=settings.private_api_docs_enabled,
    responses={
        200: {'model': schemas.Response},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def ui_update_realm_settings(request: schemas.UpdateRealmSettingsRequest, cadde_user_id: str = Depends(verify_session)):
    """
    # 提供者用 レルム設定更新API
    認可機能画面からアクセス\n
    レルム設定を更新する\n
    ## API利用説明\n
    本APIを利用するにはセッションCookieが必要\n
    ## APIリクエスト／レスポンス\n
    リクエストボディ\n
        - アクセストークン有効期限
    """
    logger.info(sys._getframe().f_code.co_name)

    result = service.update_realm_settings(cadde_user_id, request.dict())

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )


@app.put(
    settings.api_prefix + '/ui/settings/idp',
    tags=["ProviderUI"],
    include_in_schema=settings.private_api_docs_enabled,
    responses={
        200: {'model': schemas.Response},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def ui_update_idp_settings(request: schemas.UpdateIdpSettingsRequest, cadde_user_id: str = Depends(verify_session)):
    """
    # データ提供者用 アイデンティティプロバイダー設定更新API
    認可機能画面からアクセス\n
    アイデンティティプロバイダー(認証サーバ)の設定更新\n
    ## API利用説明\n
    本APIを利用するにはセッションCookieが必要\n
    ## APIリクエスト／レスポンス\n
    リクエストボディ\n
        - UserInfo URL\n
    """
    logger.info(sys._getframe().f_code.co_name)

    idp_settings_request = request.dict()
    if (not 'userinfo_url' in idp_settings_request) or (not idp_settings_request['userinfo_url']):
        return JSONResponse(
            status_code = 400,
            content = {'message': 'Request parameter error (userinfo_url)'}
        )

    result = service.update_idp_settings(cadde_user_id, idp_settings_request)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )


@app.put(
    settings.api_prefix + '/ui/settings/client_secret',
    tags=["ProviderUI"],
    include_in_schema=settings.private_api_docs_enabled,
    responses={
        200: {'model': schemas.Response},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def ui_update_client_secret(cadde_user_id: str = Depends(verify_session)):
    """
    # データ提供者用 クライアントシークレット更新API
    認可機能画面からアクセス\n
    提供者コネクタのクライアントシークレットを更新する\n
    ## API利用説明\n
    本APIを利用するにはセッションCookieが必要\n
    """
    logger.info(sys._getframe().f_code.co_name)

    result = service.update_client_secret(cadde_user_id)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )


@app.get(
    settings.api_prefix + '/ui/authorization_list',
    tags=["ProviderUIAuthorization"],
    include_in_schema=settings.private_api_docs_enabled,
    responses={
        200: {'model': List[schemas.GetAuthorizationResponse]},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def ui_get_authorization_list(cadde_user_id: str = Depends(verify_session)):
    """
    # 認可情報一覧取得API
    認可情報一覧を取得する\n
    認可情報パラメータはODRLの許可クラスより命名\n
    http://www.asahi-net.or.jp/~ax2s-kmtn/internet/rights/REC-odrl-model-20180215.html#permission\n
    ## API利用説明\n
    本APIを利用するにはセッションCookieが必要\n
    ## APIリクエスト／レスポンス\n
    クエリパラメータ\n
        - CADDEユーザID(提供者)(assigner)\n
    レスポンスボディ\n
        以下のデータの配列\n
            - 認可情報(permission)\n
                - リソースURL(target)\n
                - CADDEユーザID(提供者)(assigner)\n
                - 認可を与える属性(assignee)\n
                    - ユーザのCADDEユーザID(user) [オプション]\n
                    - 組織のCADDEユーザID(org) [オプション]\n
                    - 当人認証レベル(aal) [オプション] \n
                    - その他の属性(extras) [オプション] \n
            - 契約情報(contract) [オプション]\n
                - 取引ID(trade_id)\n
                - 契約管理サービスURL(contract_url)\n
                - 契約形態(contract_type)\n
    """
    logger.info(sys._getframe().f_code.co_name)

    realm_name = cadde_user_id

    result = service.get_authorization_list(realm_name)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )


@app.get(
    settings.api_prefix + '/ui/authorization',
    tags=["ProviderUIAuthorization"],
    include_in_schema=settings.private_api_docs_enabled,
    responses={
        200: {'model': List[schemas.GetAuthorizationResponse]},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def ui_get_authorization(target: str, cadde_user_id: str = Depends(verify_session)):
    """
    # 認可情報取得API
    指定したリソースURLの認可情報を取得する\n
    認可情報パラメータはODRLの許可クラスより命名\n
    http://www.asahi-net.or.jp/~ax2s-kmtn/internet/rights/REC-odrl-model-20180215.html#permission\n
    ## API利用説明\n
    本APIを利用するにはセッションCookieが必要\n
    ## APIリクエスト／レスポンス\n
    クエリパラメータ\n
        - CADDEユーザID(提供者)(assigner)\n
        - リソースURL(target)\n
    レスポンスボディ\n
        以下のデータの配列\n
            - 認可情報(permission)\n
                - リソースURL(target)\n
                - CADDEユーザID(提供者)(assigner)\n
                - 認可を与える属性(assignee)\n
                    - ユーザのCADDEユーザID(user) [オプション]\n
                    - 組織のCADDEユーザID(org) [オプション]\n
                    - 当人認証レベル(aal) [オプション] \n
                    - その他の属性(extras) [オプション] \n
            - 契約情報(contract) [オプション]\n
                - 取引ID(trade_id)\n
                - 契約管理サービスURL(contract_url)\n
                - 契約形態(contract_type)\n
    """
    logger.info(sys._getframe().f_code.co_name)

    realm_name = cadde_user_id
    resource_url = target

    result = service.get_authorization(realm_name, resource_url)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )


@app.post(
    settings.api_prefix + '/ui/authorization',
    tags=["ProviderUIAuthorization"],
    include_in_schema=settings.private_api_docs_enabled,
    responses={
        200: {'model': schemas.Response},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def ui_register_authorization(request: schemas.RegisterAuthorizationRequest, cadde_user_id: str = Depends(verify_session)):
    """
    # 認可情報登録API\n
    認可情報を登録する\n
    認可情報パラメータはODRLの許可クラスより命名\n
    http://www.asahi-net.or.jp/~ax2s-kmtn/internet/rights/REC-odrl-model-20180215.html#permission\n
    ## API利用説明\n
    本APIを利用するにはセッションCookieが必要\n
    「認可を与える属性」内の属性は少なくともひとつは指定しなければならない\n
    契約あり認可を登録する場合は、「契約情報」パラメータを付与する\n
    契約なし認可を登録する場合は、「契約情報」パラメータは省略する\n
    ## APIリクエスト／レスポンス\n
    リクエストボディ\n
        - 認可情報(permission)\n
            - リソースURL(target)\n
            - CADDEユーザID(提供者)(assigner)\n
            - 認可を与える属性(assignee)\n
                - ユーザのCADDEユーザID(user) [オプション]\n
                - 組織のCADDEユーザID(org) [オプション]\n
                - 当人認証レベル(aal) [オプション] \n
                - その他の属性(extras) [オプション] \n
        - 契約情報(contract) [オプション]\n
            - 取引ID(trade_id)\n
            - 契約管理サービスURL(contract_url)\n
            - 契約形態(contract_type)\n
    """
    logger.info(sys._getframe().f_code.co_name)

    realm_name = request.permission.assigner
    resource_url = request.permission.target
    policies = request.permission.assignee.dict()

    # 認可を与える属性が少なくともひとつは指定されていることを確認
    if policies['user'] is None and policies['org'] is None and policies['aal'] is None:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({'message': 'attributes for authorization required'})
        )
    else:
        # 契約あり
        if request.contract:
            contract = f'{request.contract.trade_id}, {request.contract.contract_url}, {request.contract_contract.type}'
        # 契約なし
        else:
            contract = ''

        result = service.register_authorization(realm_name, resource_url, policies, contract)

        return JSONResponse(
            status_code=result['status_code'],
            content=jsonable_encoder(result['content'])
        )


@app.delete(
    settings.api_prefix + '/ui/authorization',
    tags=["ProviderUIAuthorization"],
    include_in_schema=settings.private_api_docs_enabled,
    responses={
        200: {'model': schemas.Response},
        403: {'model': schemas.ErrorResponse},
        404: {'model': schemas.ErrorResponse},
        500: {'model': schemas.ErrorResponse}
    }
)
async def ui_delete_authorization(request: schemas.DeleteAuthorizationRequest, cadde_user_id: str = Depends(verify_session)):
    """
    # 認可情報削除API
    認可情報を削除する\n
    認可情報パラメータはODRLの許可クラスより命名\n
    http://www.asahi-net.or.jp/~ax2s-kmtn/internet/rights/REC-odrl-model-20180215.html#permission\n
    ## API利用説明\n
    本APIを利用するにはセッションCookieが必要\n
    契約あり認可を削除する場合は、「契約情報」パラメータを付与し、「認可を与える属性」パラメータは省略する\n
    契約なし認可を削除する場合は、「契約情報」パラメータを省略し、「認可を与える属性」パラメータを付与する\n
    ## APIリクエスト\n
    リクエストボディ\n
        - 認可情報(permission)\n
            - リソースURL(target)\n
            - CADDEユーザID(提供者)(=認可機能のレルム名)(assigner)\n
            - 認可を与える属性(assignee) [オプション]\n
                - ユーザのCADDEユーザID(user) [オプション]\n
                - 組織のCADDEユーザID(org) [オプション]\n
                - 当人認証レベル(aal) [オプション] \n
                - その他の属性(extras) [オプション] \n
        - 契約情報(contract) [オプション]\n
            - 取引ID(trade_id)\n
    """

    logger.info(sys._getframe().f_code.co_name)

    # リクエストパラメータを内部の変数名に置き換える
    realm_name = request.permission.assigner
    resource_url = request.permission.target

    # 契約あり認可の削除
    if request.contract is None:
        policies = request.permission.assignee.dict()
        result = service.delete_authorization_by_policies(realm_name, resource_url, policies)
    # 契約なし認可の削除
    else:
        trade_id = request.contract.trade_id
        result = service.delete_authorization_by_trade_id(realm_name, resource_url, trade_id)

    return JSONResponse(
        status_code=result['status_code'],
        content=jsonable_encoder(result['content'])
    )
