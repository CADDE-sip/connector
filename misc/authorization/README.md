# CADDE認可機能

## 設定について

### docker-compose.yaml

Dockerコンテナ群を起動するための設定ファイルです。<br>
以下の値を編集してください。

|設定パラメータ           |概要                                                               |
|:-----------------------|:-----------------------------------------------------------------|
|services.nginx.ports                             | ポート番号（左側のホスト側のポートのみ）    |
|services.keycloak.environment.KEYCLOAK_ADMIN     | Keycloakのアドミンユーザ名                |
|services.keycloak.environment.KEYCLOAK_PASSWORD  |Keycloakのアドミンパスワード               |
|services.keycloak.environment.KC_DB_USERNAME     |DBのユーザ名（POSTGRES_USERと同様）        |
|services.keycloak.environment.KC_DB_PASSWORD     | DBのパスワード（POSTGRES_PASSWORDと同様） |
|services.postgres.environment.POSTGRES_USER      | DBのユーザ名（KC_DB_USERNAMEと同様）      |
|services.postgres.environment.POSTGRES_PASSWORD  | DBのパスワード（KC_DB_PASSWORDと同様）    |

### settings.json

アプリケーションサーバで使用する設定ファイルです。<br>
以下の値を編集してください。

|設定パラメータ           |概要                                                                                       |
|:-----------------------|:------------------------------------------------------------------------------------------|
|provider_connector_id   | 提供者コネクタのクライアントID（以下で./provider_setup.shで対話的に入力する値と合わせてください）|
|client_id               | 認可機能のクライアントID                                                                    |
|client_secret           | 認可機能のクライアントシークレット                                                           |
|authz_keycloak_url      | 認可機能KeycloakのベースURL                                                                |
|authn_url               | 認証機能APIのベースURL                                                                     |
|authn_keycloak_url      | 認証機能KeycloakのベースURL（以下で./provider_setup.shで対話的に入力する値と合わせてください）  |
|authn_realm_name        | 認証機能のレルム名（authenticationを指定する）                                               |
|subject_issuer          | 認証機能の発行者（認証機能）を表す文字列（authenticationを指定する）                           |

### settings_provider_setup.json

provider_setup.pyが使用する設定ファイルです。<br>
このファイルを直接編集する必要はありません。<br>
./provider_setup.shを実行した際に対話的に入力した値が書き込まれます。

## Dockerイメージの作成について

Dockerfileの定義にもとづいて作成するDockerイメージを作成します。

### Keycloakコンテナイメージの作成

prebuilt_keycloak:19.0.2というDcokerイメージを作成します。<br>
そのために、以下のシェルスクリプトを実行します。
```
./image_build_keycloak.sh
```
### FastAPIコンテナイメージの作成

fastapi:latestというDcokerイメージを作成します。<br>
そのために、以下のシェルスクリプトを実行します。
```
./image_build_fastapi.sh
```
## 起動・停止について

シェルスクリプトを実行することによってDockerコンテナの起動・停止をします。

### コンテナ群起動
```
./start.sh
```

### コンテナ群起動確認

起動時にStateがすべてUpとなっていることを確認

```
NAME                COMMAND                  SERVICE             STATUS              PORTS
authz_fastapi       "python -m uvicorn m…"   fastapi             running             8000/tcp
authz_keycloak      "/opt/keycloak/bin/k…"   keycloak            running             8443/tcp
authz_nginx         "/docker-entrypoint.…"   nginx               running             0.0.0.0:XXXXX->80/tcp, :::XXXXX->80/tcp
authz_postgres      "docker-entrypoint.s…"   postgres            running             5432/tcp
```

### コンテナ群停止
```
./stop.sh
```
## セットアップについて

コンテナを起動中に./provider_setup.shを実行して、対話的に以下を入力します。<br>
これらの入力はsettings_provider_setup.jsonに書き込まれます。

|設定パラメータ                     |概要                                                    |
|:-------------------------------|:-------------------------------------------------------|
|CADDEユーザID(レルム名)　         |CADDEユーザIDがレルム名として設定されます　　　　　　　　　  |
|提供者コネクタのクライアントID　   |settings.jsonのprovider_connector_idと値を合わせてください |
|CADDE認証機能KeycloakのベースURL　|settings.jsonのauthn_keycloak_urlと値を合わせてください    |

## 認可機能の使用方法について

### アクセス方法

WebブラウザのアドレスバーにURLを入力することでアクセスする。<br>
URLに関しては認可機能を起動しているマシンのIPアドレス／ドメイン名とする。<br>
ポート番号に関しては、docker-compose.yamlのservices.nginx.portsで設定したものを指定すること。<br>

### 認可機能操作方法

Web画面のトップ画面に表示されている「ログイン」ボタンを押下すると認証機能のログイン画面に遷移する（AUTHENTICATIONと表示されているログイン画面）。<br>
そこで、CADDE提供者IDとパスワードを入力し、ログインに成功すると、ログイン状態となり認可機能の画面に戻る。<br>
ログイン状態では、画面左に表示されている認可機能の各メニューを利用することができるようになる。

![Alt text](doc/png/login.png?raw=true "ログイン")


### 「認可機能の設定」画面

本画面にて、認可機能自体の設定を変更することができる。<br>
ここでは以下の項目を確認、変更することができるが、通常の利用では操作することはない。<br>
- アクセストークン生存期間：　認可機能が発行するアクセストークンの生存期間を確認、変更する
- クライアントID：　提供者コネクタのクライアントIDを確認する
- 提供者クライアントシークレット：　提供者コネクタのクライアントシークレットを確認、変更する
- UserInfo URL：　認証機能と連携する際に使用するUserInfo URLを確認、変更する

![Alt text](doc/png/settings.png?raw=true "認可機能の設定")

### 「認可一覧」画面

本画面にて、登録された認可の一覧を確認することができる。<br>
認可は「配信のURL」で表示されており、押下することで「認可詳細」画面に遷移し、選択した「配信のURL」に認可を確認することができる。

![Alt text](doc/png/list.png?raw=true "認可一覧")

### 「認可詳細」画面

本画面にて、「配信のURL」に付与されている認可を確認、削除することができる。<br>
認可の表のユーザ、組織、AALの列は、それぞれ、「ユーザに対する認可」、「組織に対する認可」、「当人認証に対する認可」の条件を示している。取引IDの列は、契約有りの認可設定の際に付番された取引IDを示している。つまり、取引IDのある認可は契約管理によって登録された認可である。<br>
認可を削除したい場合、削除対象の認可の行を押下することで選択状態になるため、その状態で「認可削除」ボタンを押下することで、認可を削除することができる。<br>
もし「配信のURL」に付与されている全ての認可を削除した場合、「認可一覧」画面から当該「配信URL」は削除される。

![Alt text](doc/png/detail.png?raw=true "認可詳細")

### 「認可登録」画面

本画面にて、認可の登録をすることができる。<br>
認可を登録するには、「配信のURL」といくつかの認可の条件を入力する必要がある。<br>
配信のURLは必須項目のため、必ず入力する。<br>
認可の条件は、「ユーザに対する認可」、「組織に対する認可」、「当人認証に対する認可」の3つがあるが、少なくともひとつに関しては入力する必要がある。<br>
- ユーザに対する認可：　どのユーザに対して認可をするか、ということを指定する
- 組織に対する認可：　どの組織に所属しているユーザに対して認可するか、ということを指定する。組織もCADDEユーザIDによって指定することに注意すること。
- 当人認証に対する認可：　どの当人認証レベルの認証をしたユーザに対して認可するか、ということを指定する。当人認証レベルは、ユーザ認証時の認証の要素数などによって異なる。

「配信のURL」と認可の条件を記入したのち、「認可設定」ボタンを押下すると認可を登録することができる。<br>
正常に登録された認可は「認可一覧」画面にて確認することができる。

![Alt text](doc/png/registration.png?raw=true "認可登録")


### CLIを用いての認可設定
<br>CLIにて認可設定を行う場合は、以下のコマンドを使用する。<br>
```
curl -v -X POST https://{提供者コネクタのFQDN}:{ポート番号}/cadde/api/v4/authorization -H "Content-Type: application/json" -H "Authorization:Bearer {認証トークン}" \
 -d '{
  "permission": {
    "target": "{リソースURL}",
    "assigner": "{CADDEユーザID(提供者)}",
    "assignee": {
      "user": "{CADDEユーザID(利用者) [オプション]}",
      "org": "{組織のCADDEユーザID [オプション]}",
      "aal": 2,
      "extras": "{その他の属性 [オプション]}"
    }
  },
  "contract": {
    "trade_id": "",
    "contract_url": "",
    "contract_type": ""
  }
}' 
```

