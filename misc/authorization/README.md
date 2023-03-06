# CADDE認可機能


## 設定について

### docker-compose.yaml

Dockerコンテナ群を起動するための設定ファイルです。
以下の値を編集してください。

services.nginx.ports: ポート番号（左側のホスト側のポートのみ）
services.keycloak.environment.KEYCLOAK_ADMIN: Keycloakのアドミンユーザ名
services.keycloak.environment.KEYCLOAK_PASSWORD: Keycloakのアドミンパスワード
services.keycloak.environment.KC_DB_USERNAME: DBのユーザ名（POSTGRES_USERと同様）
services.keycloak.environment.KC_DB_PASSWORD: DBのパスワード（POSTGRES_PASSWORDと同様）
services.postgres.environment.POSTGRES_USER: DBのユーザ名（KC_DB_USERNAMEと同様）
services.postgres.environment.POSTGRES_PASSWORD: DBのパスワード（KC_DB_PASSWORDと同様）

### settings.json

アプリケーションサーバで使用する設定ファイルです。
以下の値を編集してください。

provider_connector_id: 提供者コネクタのクライアントID（以下で./provider_setup.shで対話的に入力する値と合わせてください）
client_id: 認可機能のクライアントID
client_secret: 認可機能のクライアントシークレット
authz_keycloak_url: 認可機能KeycloakのベースURL
authn_url: 認証機能APIのベースURL
authn_keycloak_url: 認証機能KeycloakのベースURL（以下で./provider_setup.shで対話的に入力する値と合わせてください）
authn_realm_name: 認証機能のレルム名（authenticationを指定する）
subject_issuer: 認証機能の発行者（認証機能）を表す文字列（authenticationを指定する）

### settings_provider_setup.json

provider_setup.pyが使用する設定ファイルです。
このファイルを直接編集する必要はありません。
./provider_setup.shを実行した際に対話的に入力した値が書き込まれます。


## Dockerイメージの作成について

Dockerfileの定義にもとづいて作成するDockerイメージを作成します。

### Keycloakコンテナイメージの作成

prebuilt_keycloak:19.0.2というDcokerイメージを作成します。
そのために、以下のシェルスクリプトを実行します。

./image_build_keycloak.sh

### FastAPIコンテナイメージの作成

fastapi:latestというDcokerイメージを作成します。
そのために、以下のシェルスクリプトを実行します。

./image_build_fastapi.sh


## 起動・停止について

シェルスクリプトを実行することによってDockerコンテナの起動・停止をします。

### コンテナ群起動

./start.sh

### コンテナ群停止

./stop.sh


## セットアップについて

コンテナを起動中に./provider_setup.shを実行して、対話的に以下を入力します。

CADDEユーザID(レルム名)　
提供者コネクタのクライアントID　settings.jsonのprovider_connector_idと値を合わせてください
CADDE認証機能KeycloakのベースURL　settings.jsonのauthn_keycloak_urlと値を合わせてください

これらの入力はsettings_provider_setup.jsonに書き込まれます。
