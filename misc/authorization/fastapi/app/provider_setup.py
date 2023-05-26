import sys
import os
import json
import urllib.request
from settings import settings

os.environ['NO_PROXY'] = '*'
keycloak_url = f'http://keycloak:8080/keycloak'

###################################################
# Admin APIを利用するためにアドミントークンを取得 #
###################################################

# masterレルムのadmin-cliに対してリソースオーナーパスワードクレデンシャルズグラントでAdminトークンを取得
data = f'username={settings.admin_username}&password={settings.admin_password}&grant_type=password&client_id=admin-cli'
req = urllib.request.Request(url=keycloak_url + '/realms/master/protocol/openid-connect/token',
    data=data.encode()
)
try:
    with urllib.request.urlopen(req) as res:
        res_body = json.load(res)
    token = res_body['access_token']
except urllib.error.HTTPError as err:
    print('×セットアップする権限がありません(アドミンのアクセストークン取得に失敗しました)')
    sys.exit()

# Admin APIのヘッダを定義
headers = {
    'Content-Type' : 'application/json',
    'Authorization': f'Bearer {token}'
}

################
# レルムの作成 #
################

realm_name = settings.realm
realm_settings = {
    "enabled": True,
    "id": f"{realm_name}",
    "realm": f"{realm_name}"
}
req = urllib.request.Request(url=keycloak_url + '/admin/realms',
    data=json.dumps(realm_settings).encode(),
    method='POST',
    headers=headers
)
try:
    with urllib.request.urlopen(req) as res:
        print('〇レルム{}の作成に成功しました'.format(realm_name))
except urllib.error.HTTPError as err:
    if err.code == 409:
        print('〇レルム{}の作成に成功しました'.format(realm_name))
    else:
        print('×レルム{}が作成できませんでした。レルム名を確認してください。'.format(realm_name))
        sys.exit()

######################
# クライアントの作成 #
######################

provider_connector = {
    'client_id': settings.client
}
client_init_settings = {
    'attributes': {},
    'clientId': f'{provider_connector["client_id"]}',
    'enabled':'true',
    'protocol': 'openid-connect',
    'redirectUris': []
}
req = urllib.request.Request(url=keycloak_url + f'/admin/realms/{realm_name}/clients',
    data=json.dumps(client_init_settings).encode(),
    method='POST',
    headers=headers
)
try:
    with urllib.request.urlopen(req) as res:
        pass # クライアントを作成成功
except urllib.error.HTTPError as err:
    if err.code == 409:
        pass # クライアント作成済み
    else:
        print('×クライアント{}を作成できませんでした(作成要求に失敗しました。クライアントIDを確認してください。)'.format(provider_connector["client_id"]))
        sys.exit()

# 提供者コネクタクライアントUUIDとレルムマネジメントクライアントのUUIDを取得
req = urllib.request.Request(url=keycloak_url + f'/admin/realms/{realm_name}/clients',
    method='GET',
    headers=headers
)
try:
    with urllib.request.urlopen(req) as res:
        clients = json.load(res)
except urllib.error.HTTPError as err:
    print('×クライアント{}を作成できませんでした(クライアント一覧を取得できませんでした)'.format(provider_connector["client_id"]))
    sys.exit()

provider_connector_client_uuid = ''
realm_management_client_uuid = ''
for client in clients:
    if client['clientId'] == provider_connector['client_id']:
        provider_connector_client_uuid = client['id']

    # Token Exchange関係の設定で必要になる
    if client['clientId'] == 'realm-management':
        realm_management_client_uuid = client['id']

if not provider_connector_client_uuid:
    print('×クライアント{}を作成できませんでした(提供者コネクタクライアントのUUIDを取得できませんでした)'.format(provider_connector["client_id"]))
    sys.exit()


#print(f'提供者コネクタのクライアントUUID: {provider_connector_client_uuid}')

client_settings = {"id":f"{provider_connector_client_uuid}","clientId":f"{provider_connector['client_id']}","surrogateAuthRequired":False,"enabled":True,"alwaysDisplayInConsole":False,"clientAuthenticatorType":"client-secret","redirectUris":[],"webOrigins":[],"notBefore":0,"bearerOnly":False,"consentRequired":False,"standardFlowEnabled":False,"implicitFlowEnabled":False,"directAccessGrantsEnabled":False,"serviceAccountsEnabled":True,"publicClient":False,"frontchannelLogout":False,"protocol":"openid-connect","attributes":{"backchannel.logout.session.required":"true","backchannel.logout.revoke.offline.tokens":"false","request.uris":None,"frontchannel.logout.url":None,"saml.artifact.binding":"false","saml.server.signature":"false","saml.server.signature.keyinfo.ext":"false","saml.assertion.signature":"false","saml.client.signature":"false","saml.encrypt":"false","saml.authnstatement":"false","saml.onetimeuse.condition":"false","saml_force_name_id_format":"false","saml.multivalued.roles":"false","saml.force.post.binding":"false","exclude.session.state.from.auth.response":"false","oauth2.device.authorization.grant.enabled":"false","oidc.ciba.grant.enabled":"false","use.refresh.tokens":"true","id.token.as.detached.signature":"false","tls.client.certificate.bound.access.tokens":"false","require.pushed.authorization.requests":"false","client_credentials.use_refresh_token":"false","token.response.type.bearer.lower-case":"false","display.on.consent.screen":"false","acr.loa.map":"{}","oauth2.device.polling.interval":None},"authenticationFlowBindingOverrides":{},"fullScopeAllowed":True,"nodeReRegistrationTimeout":-1,"defaultClientScopes":["web-origins","profile","roles","email"],"optionalClientScopes":["address","phone","offline_access","microprofile-jwt"],"access":{"view":True,"configure":True,"manage":True},"authorizationServicesEnabled":True}

req = urllib.request.Request(url=keycloak_url + f'/admin/realms/{realm_name}/clients/{provider_connector_client_uuid}',
    data=json.dumps(client_settings).encode(),
    method='PUT',
    headers=headers
)
try:
    with urllib.request.urlopen(req) as res:
        pass # クライアントの作成に成功
except urllib.error.HTTPError as err:
    print('×クライアント{}の作成に失敗しました(クライアントの設定に失敗しました)'.format(provider_connector['client_id']))

# Client > Mappers

mappers = [
    {"protocol":"openid-connect","config":{"id.token.claim":"false","access.token.claim":"true","userinfo.token.claim":"false","multivalued":"","aggregate.attrs":"","user.attribute":"user","claim.name":"user","jsonType.label":"String"},"name":"user","protocolMapper":"oidc-usermodel-attribute-mapper"},
    {"protocol":"openid-connect","config":{"id.token.claim":"false","access.token.claim":"true","userinfo.token.claim":"false","multivalued":"","aggregate.attrs":"","user.attribute":"org","claim.name":"org","jsonType.label":"String"},"name":"org","protocolMapper":"oidc-usermodel-attribute-mapper"},
    {"protocol":"openid-connect","config":{"id.token.claim":"false","access.token.claim":"true","userinfo.token.claim":"false","multivalued":"","aggregate.attrs":"","user.attribute":"aal","claim.name":"aal","jsonType.label":"String"},"name":"aal","protocolMapper":"oidc-usermodel-attribute-mapper"},
    {"protocol":"openid-connect","config":{"id.token.claim":"false","access.token.claim":"true","userinfo.token.claim":"false","multivalued":"","aggregate.attrs":"","user.attribute":"extras","claim.name":"extras","jsonType.label":"String"},"name":"extras","protocolMapper":"oidc-usermodel-attribute-mapper"}
]

for mapper in mappers:
    req = urllib.request.Request(url=keycloak_url + f'/admin/realms/{realm_name}/clients/{provider_connector_client_uuid}/protocol-mappers/models',
    data=json.dumps(mapper).encode(),
    method='POST',
    headers=headers
)
    try:
        with urllib.request.urlopen(req) as res:
            pass # マッパーの作成に成功
    except urllib.error.HTTPError as err:
        if err.code == 409:
            pass # マッパーがすでに存在
        else:
            print('×クライアント{}の作成に失敗しました(マッパー{}の作成に失敗しました)'.format(provider_connector['client_id']), mapper["name"])
            sys.exit()

print('〇クライアント{}の作成に成功しました'.format(provider_connector['client_id']))


####################################
# アイデンティティプロバイダの作成 #
####################################

idp = {
    'alias': settings.subject_issuer,
    'authorization_url':  'https:',
    'token_url': 'https:',
    'userinfo_url': settings.identity_provider + f'/realms/{settings.authn_realm_name}/protocol/openid-connect/userinfo',
    'client_id': 'xxxxxx',
    'client_secret': 'xxxxxx'
}
idp_settings = {"config":{"useJwksUrl":"true","syncMode":"IMPORT","authorizationUrl":f"{idp['authorization_url']}","hideOnLoginPage":"","loginHint":"","uiLocales":"","backchannelSupported":"","disableUserInfo":"","acceptsPromptNoneForwardFromClient":"","validateSignature":"","pkceEnabled":"","tokenUrl":f"{idp['token_url']}","userInfoUrl":f"{idp['userinfo_url']}","clientAuthMethod":"client_secret_post","clientId":f"{idp['client_id']}","clientSecret":f"idp['client_secret']"},"alias":f"{idp['alias']}","providerId":"oidc","enabled":True,"authenticateByDefault":False,"firstBrokerLoginFlowAlias":"first broker login","postBrokerLoginFlowAlias":"","storeToken":"","addReadTokenRoleOnCreate":"","trustEmail":"","linkOnly":""}

idp_exists = False
req = urllib.request.Request(url=keycloak_url + '/admin/realms/{}/identity-provider/instances'.format(realm_name),
    data=json.dumps(idp_settings).encode(),
    method='POST',
    headers=headers
)
try:
    with urllib.request.urlopen(req) as res:
        pass # アイデンティティプロバイダー作成成功
except urllib.error.HTTPError as err:
    if err.code == 409:
        idp_exists = True
    else:
        print('×アイデンティティプロバイダーが作成できませんでした(アイデンティティプロバイダー作成要求に失敗しました。URLを確認してください。{})'.format(idp['userinfo_url']))
        sys.exit()

# すでにアイデンティティプロバイダが存在している場合
if idp_exists:
    req = urllib.request.Request(url=keycloak_url + '/admin/realms/{}/identity-provider/instances/{}'.format(realm_name, idp['alias']),
        data=json.dumps(idp_settings).encode(),
        method='PUT',
        headers=headers
    )
    try:
        with urllib.request.urlopen(req) as res:
            pass
    except urllib.error.HTTPError as err:
        print('×アイデンティティプロバイダーが作成できませんでした(アイデンティティプロバイダーの更新ができませんでした。URLを確認してください。{})'.format(idp['userinfo_url']))


# Identity Providers > Mappers

# user, org, aalのマッパーを作成する
mappers = [
    {"identityProviderAlias":"authentication","config":{"syncMode":"FORCE","claim":"user","user.attribute":"user"},"name":"user","identityProviderMapper":"oidc-user-attribute-idp-mapper"},
    {"identityProviderAlias":"authentication","config":{"syncMode":"FORCE","claim":"org","user.attribute":"org"},"name":"org","identityProviderMapper":"oidc-user-attribute-idp-mapper"},
    {"identityProviderAlias":"authentication","config":{"syncMode":"FORCE","claim":"aal","user.attribute":"aal"},"name":"aal","identityProviderMapper":"oidc-user-attribute-idp-mapper"},
    {"identityProviderAlias":"authentication","config":{"syncMode":"FORCE","claim":"extras","user.attribute":"extras"},"name":"extras","identityProviderMapper":"oidc-user-attribute-idp-mapper"}
]
for mapper in mappers:
    req = urllib.request.Request(url=keycloak_url + f'/admin/realms/{realm_name}/identity-provider/instances/{idp["alias"]}/mappers',
        data=json.dumps(mapper).encode(),
        method='POST',
        headers=headers
    )
    try:
        with urllib.request.urlopen(req) as res:
            pass # アイデンティティプロバイダのマッパーを作成
    except urllib.error.HTTPError as err:
        pass # アイデンティティプロバイダのマッパー作成済み。マッパーが作成済みの場合にも400が返ってくる

# Identity Providers > Permissions

# 設定するためには、パーミッションのUUID, リソースのUUID, realm-managementのUUID, クライアントポリシーのUUID, token-exchangeスコープのUUID, アイデンティティプロバイダのUUIDが必要

# パーミッションのUUID, リソースのUUID

permissions_settings = {"enabled":True}
req = urllib.request.Request(
    url=keycloak_url + f'/admin/realms/{realm_name}/identity-provider/instances/{idp["alias"]}/management/permissions',
    data=json.dumps(permissions_settings).encode(),
    method='PUT',
    headers=headers
)
try:
    with urllib.request.urlopen(req) as res:
        permissions = json.load(res)
        permission_uuid = permissions['scopePermissions']['token-exchange']
        resource_uuid = permissions['resource']
        #print(f'パーミッションのUUID: {permission_uuid}')
        #print(f'リソースのUUID: {resource_uuid}')
except urllib.error.HTTPError as err:
    print('×アイデンティティプロバイダが作成できませんでした(パーミッションのUUID, リソースのUUIDの取得ができませんでした)')
    sys.exit()

# realm-managementのUUID

if not realm_management_client_uuid:
    print('×アイデンティティプロバイダが作成できませんでした(realm-managementのUUIDの取得ができませんでした)')
    sys.exit()
#print(f'realm-managementのクライアントUUID: {realm_management_client_uuid}')

# クライアントポリシーのUUID

client_policy_name = "token_exchange_client_policy"
client_policy_settings = {"type":"client","logic":"POSITIVE","decisionStrategy":"UNANIMOUS","name":client_policy_name,"clients":[provider_connector_client_uuid]}
req = urllib.request.Request(
    url=keycloak_url + f'/admin/realms/{realm_name}/clients/{realm_management_client_uuid}/authz/resource-server/policy/client',
    data=json.dumps(client_policy_settings).encode(),
    method='POST',
    headers=headers
)
client_policy_exists = False
try:
    with urllib.request.urlopen(req) as res:
        pass # クライアントポリシー作成成功
except urllib.error.HTTPError as err:
    if err.code == 409:
        client_policy_exists = True
        pass # クライアントポリシー作成済み
    else:
        print('×アイデンティティプロバイダのパーミッションが作成できませんでした(クライアントポリシーが作成できませんでした)')
        sys.exit()

req = urllib.request.Request(
    url=keycloak_url + f'/admin/realms/{realm_name}/clients/{realm_management_client_uuid}/authz/resource-server/policy',
    method='GET',
    headers=headers
)
try:
    with urllib.request.urlopen(req) as res:
        client_policies = json.load(res)
except urllib.error.HTTPError as err:
    print('×アイデンティティプロバイダのパーミッションが作成できませんでした(クライアントポリシー一覧を取得できませんでした)')
    sys.exit()
client_policy_uuid = ''
for client_policy in client_policies:
    if client_policy['name'] == client_policy_name:
        client_policy_uuid = client_policy['id']
if not client_policy_uuid:
    print('×アイデンティティプロバイダのパーミッションが作成できませんでした(クライアントポリシーのUUIDの取得ができませんでした)')
    sys.exit()

# クライアントポリシーを更新

if client_policy_exists:
    client_policy_settings = {"id":client_policy_uuid, "type":"client","logic":"POSITIVE","decisionStrategy":"UNANIMOUS","name":client_policy_name,"clients":[provider_connector_client_uuid]}
    req = urllib.request.Request(
        url=keycloak_url + f'/admin/realms/{realm_name}/clients/{realm_management_client_uuid}/authz/resource-server/policy/client/{client_policy_uuid}',
        data=json.dumps(client_policy_settings).encode(),
        method='PUT',
        headers=headers
    )
try:
    with urllib.request.urlopen(req) as res:
        pass
except urllib.error.HTTPError as err:
        print('×アイデンティティプロバイダのパーミッションが作成できませんでした(クライアントポリシーが更新できませんでした)')
        sys.exit()


# token-exchangeスコープのUUID

req = urllib.request.Request(
    url=keycloak_url + f'/admin/realms/{realm_name}/clients/{realm_management_client_uuid}/authz/resource-server/resource/{resource_uuid}/scopes',
    method='GET',
    headers=headers
)
scope_uuid = ''
try:
    with urllib.request.urlopen(req) as res:
        scopes = json.load(res)
except urllib.error.HTTPError as err:
        print(err)
for scope in scopes:
    if scope['name'] == 'token-exchange': # Keycloakの仕様
        scope_uuid = scope['id']
if not scope_uuid:
    print('×アイデンティティプロバイダのパーミッションが作成できませんでした(token-exchangeスコープのUUIDの取得ができませんでした)')
    sys.exit()

# アイデンティティプロバイダのUUID

req = urllib.request.Request(
    url=keycloak_url+f'/admin/realms/{realm_name}',
    method='GET',
    headers=headers
)
try:
    with urllib.request.urlopen(req) as res:
        identity_provider_uuid = json.load(res)['identityProviders'][0]['internalId']
except urllib.error.HTTPError as err:
    print('×アイデンティティプロバイダーの作成に失敗しました(アイデンティティプロバイダのUUIDの取得ができませんでした)')
    sys.exit()

# アイデンティティプロバイダーのパーミッションを設定
# 設定するためには、パーミッションのUUID, リソースのUUID, realm-managementのUUID, クライアントポリシーのUUID, token-exchangeスコープのUUID, アイデンティティプロバイダのUUIDが必要

permission_settings = {
    "id":permission_uuid,
    "name":f"token-exchange.permission.idp.{identity_provider_uuid}",
    "type":"scope",
    "logic":"POSITIVE",
    "decisionStrategy":"UNANIMOUS",
    "resources":[resource_uuid],
    "scopes":[scope_uuid],
    "policies":[client_policy_uuid]
}
req = urllib.request.Request(
    url=keycloak_url+f'/admin/realms/{realm_name}/clients/{realm_management_client_uuid}/authz/resource-server/permission/scope/{permission_uuid}',
    data=json.dumps(permission_settings).encode(),
    method='PUT',
    headers=headers
)
try:
    with urllib.request.urlopen(req) as res:
        print('〇アイデンティティプロバイダーの作成に成功しました　Userinfo URL: {}'.format(idp['userinfo_url']))
except urllib.error.HTTPError as err:
    print('×アイデンティティプロバイダーの作成に失敗しました(アイデンティティプロバイダーのパーミッションを設定できませんでした)')
