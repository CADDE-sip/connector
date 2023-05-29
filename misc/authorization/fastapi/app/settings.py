import json
import yaml
import logging

class Settings():

    with open('../settings/settings.json') as f:
        api_settings = json.load(f)
    provider_connector_id = api_settings['provider_connector_id']
    client_id  = api_settings['client_id']
    client_secret = api_settings['client_secret']
    authz_keycloak_url = api_settings['authz_keycloak_url']
    authn_url = api_settings['authn_url']
    authn_keycloak_url = api_settings['authn_keycloak_url']
    authn_realm_name = api_settings['authn_realm_name']
    subject_issuer = api_settings['subject_issuer']

    with open('../settings/settings_provider_setup.json') as f:
        provider_setup_settings = json.load(f)
    realm = provider_setup_settings['realm']
    client = provider_setup_settings['client']
    identity_provider = provider_setup_settings['identity_provider']

    with open('../settings/docker-compose.yaml') as f:
        server_settings = yaml.load(f, Loader=yaml.SafeLoader)
    admin_username = server_settings['services']['keycloak']['environment']['KEYCLOAK_ADMIN']
    admin_password = server_settings['services']['keycloak']['environment']['KEYCLOAK_ADMIN_PASSWORD']

    # 固定設定項目
    title = 'CADDE認可機能'
    description = ''
    version = '4.0.0'
    tags_metadata = [
        {
            "name": "Data",
            "description": "データ取得用API(提供者コネクタからアクセス；公開API)"
        },
        {
            "name": "Authorization",
            "description": "認可用API(公開API)"
        },
        {
            "name": "ProviderUIAuthorization",
            "description": "データ提供者用認可API(認可機能画面からアクセス；非公開API)"
        },
        {
            "name": "ProviderUI",
            "description": "データ提供者用API(認可機能画面からアクセス；非公開API)"
        }
    ]
    api_prefix = '/cadde/api/v4'
    admin_client_id = 'admin-cli'
    ui_redirect_path = 'load/?'

    # デバッグ用設定項目
    public_api_docs_enabled = True # OpenAPIドキュメント表示/非表示
    private_api_docs_enabled = False # OpenAPIドキュメント表示/非表示
    if not private_api_docs_enabled:
        tags_metadata.pop()
        tags_metadata.pop()
    log_level = logging.INFO
    #log_level = logging.DEBUG

settings = Settings()
