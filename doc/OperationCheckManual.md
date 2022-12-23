# 分野間データ連携基盤: 動作確認環境利用ガイド
- コネクタ環境構築後に、正常に動作するか等を確認するための動作確認環境を準備しています。
- 本ページでは動作確認環境の利用方法を記載しています。
![Alt text](png/OperatonCheck.png?raw=true "Title")


# 利用者コネクタ構築時の動作確認環境利用ガイド

## 前提
- 利用者コネクタのプロキシに動作確認環境専用のクライアント証明書が設定されていることを前提とします。<br>
  [証明書のダウンロードはこちらから](../misc/OperationCheck/OperationCheckClientCertificate.zip) 

## 利用者コネクタ設定手順
動作確認環境の提供者コネクタに接続する際には利用者コネクタの設定を変更する必要があります。<br>
Github上に設定済みのファイルを準備していますので以下の手順で置き換えください。

```
cd connector
cp -p misc/OperationCheck/connector/src/consumer/authentication-authorization/swagger_server/configs/authentication.json src/consumer/authentication-authorization/swagger_server/configs/authentication.json
cp -p misc/OperationCheck/connector/src/consumer/connector-main/swagger_server/configs/connector.json src/consumer/connector-main/swagger_server/configs/connector.json
cp -p misc/OperationCheck/connector/src/consumer/connector-main/swagger_server/configs/idp.json src/consumer/connector-main/swagger_server/configs/idp.json
cp -p misc/OperationCheck/connector/src/consumer/connector-main/swagger_server/configs/location.json src/consumer/connector-main/swagger_server/configs/location.json
```

置き換え後、利用者コネクタを再起動します。
```
cd src/consumer
docker-compose -p consumer down
docker-compose -p consumer up -d
```

## 動作確認手順
構築済みの利用者コネクタから動作確認環境の提供者コネクタに接続し、動作確認する手順です。
### 1. アクセストークン取得

```
curl -X POST -H "Cache-Control: no-cache" -H "Content-Type: application/json" -d '{ "consumer_id": "cadde:verify_user01.aa", "password": "uVa1BvnKas_5odW" }' https://key-authen.test.data-linkage.jp/cadde/api/v1/consumer/token
```
以下の結果が出力されていればアクセストークンの取得完了です。

```
{"msg":"success","access_token":"{トークン}"}
```

### 2. 詳細検索
- Authorizationヘッダには、1．アクセストークン取得で発行したトークンの値を指定ください。
```
curl -X GET -v "http://{利用者コネクタのFQDN}:{ポート番号}/api/3/action/package_search?fq=caddec_dataset_id_for_detail:5add6540-cc2a-5080-8720-619c95e81e9e" -s -S -H "Cache-Control: no-cache" -H "x-cadde-search: detail" -H "x-cadde-provider:cadde:verify_user01.aa" -H "x-idp-url:https://key-authen.test.data-linkage.jp/auth/realms/cadde-authentication" -H "Authorization:{トークン}"
```
以下の結果が出力されていれば詳細検索完了です。

```
{"help": "http://verify-provider.test.data-linkage.jp:5000/api/3/action/help_show?name=package_search", "success": true, "result": {"count": 1,～略～{}}}
```

### 3. ファイル取得
- Authorizationヘッダには、1．アクセストークン取得で発行したトークンの値を指定ください。
```
curl -X GET -v "http://{利用者コネクタのFQDN}:{ポート番号}/cadde/api/v1/file" -H "x-cadde-resource-url:http://data-management/data/example_http.txt" -H "x-cadde-resource-api-type:file/http" -H "x-cadde-provider:cadde:verify_user01.aa" -H "x-idp-url:https://key-authen.test.data-linkage.jp/auth/realms/cadde-authentication" -H "Authorization:{トークン}" -o {出力ファイル名}
```

以下の結果が出力されていれば動作確認完了です。

```
Successful download

example_http.txt
```

# 提供者コネクタ構築時の動作確認環境利用ガイド

## 前提
- 提供者コネクタのリバースプロキシに動作確認環境専用のCA証明書が設定されていることを前提とします。<br>
  [証明書のダウンロードはこちらから](../misc/OperationCheck/OperationCheckClientCertificate.zip) 
- 提供者コネクタ側の環境にFWが存在する場合、動作確認環境の利用者コネクタからの通信が許可されていることを前提とします。<br>
  動作確認環境の利用者コネクタのIPアドレスは「35.75.141.64」となりますので、必要に応じて許可設定をお願いします。

## 提供者コネクタ設定手順

動作確認環境の利用者コネクタに接続する際には提供者コネクタの設定を変更する必要があります。<br>
Github上に設定済みのファイルを準備していますので以下の手順で置き換えください。

```
cd connector
cp -p misc/OperationCheck/connector/src/provider/authentication-authorization/swagger_server/configs/authentication.json src/provider/authentication-authorization/swagger_server/configs/authentication.json
cp -p misc/OperationCheck/connector/src/provider/connector-main/swagger_server/configs/connector.json src/provider/connector-main/swagger_server/configs/connector.json
```

置き換え後、提供者コネクタを再起動します。
```
cd src/provider/
docker-compose -p provider down
docker-compose -p provider up -d
```

## 動作確認手順
動作確認環境の利用者コネクタから構築済みの提供者コネクタに接続し、動作確認する手順です。
curlコマンドを実行可能なコンソールより動作確認環境の利用者コネクタに対してコマンドを実行ください。

### 1. アクセストークン取得

```
curl -X POST -H "Cache-Control: no-cache" -H "Content-Type: application/json" -d '{ "consumer_id": "cadde:verify_user01.aa", "password": "uVa1BvnKas_5odW" }' https://key-authen.test.data-linkage.jp/cadde/api/v1/consumer/token
```
以下の結果が出力されていればアクセストークンの取得完了です。

```
{"msg":"success","access_token":"{トークン}"}
```

### 2. 詳細検索

- 検索クエリ内の{詳細検索用データセットID} には、ご自身で作成したカタログの値(extras:caddec_dataset_id_for_detail)を設定ください。
- x-cadde-providerヘッダには、ご自身のCADDEユーザIDを指定ください。
- Authorizationヘッダには、1．アクセストークン取得で発行したトークンの値を指定ください。

```
curl -X GET -v "https://verify-consumer.test.data-linkage.jp/api/3/action/package_search?fq=caddec_dataset_id_for_detail:{詳細検索用データセットID}" -s -S -H "Cache-Control: no-cache" -H "x-cadde-search: detail" -H "x-cadde-provider:{提供者ID}" -H "x-idp-url:https://key-authen.test.data-linkage.jp/auth/realms/cadde-authentication" -H "Authorization:{トークン}"
```

以下の結果が出力されていれば詳細検索完了です。

```
{"help": "http://CKAN_URL/api/3/action/help_show?name=package_search", "success": true, "result": {"count": 1,～略～{}}}
```

### 3. ファイル取得

- x-cadde-resource-urlヘッダには、詳細カタログ検索結果(resources:download_url)から取得したファイルのダウンロードURLを指定ください。
- x-cadde-resource-api-typeヘッダには、詳細カタログ検索結果(resources:caddec_resource_type)から取得したリソース提供手段の識別子(file/http or file/ftp)を指定ください。
- x-cadde-providerヘッダには、ご自身のCADDEユーザIDを指定ください。
- Authorizationヘッダには、1．アクセストークン取得で発行したトークンの値を指定ください。

```
curl -X GET -v "https://verify-consumer.test.data-linkage.jp/cadde/api/v1/file" -H "x-cadde-resource-url:{リソースURL}" -H "x-cadde-resource-api-type:{リソース提供手段の識別子}" -H "x-cadde-provider:{提供者ID}" -H "x-idp-url:https://key-authen.test.data-linkage.jp/auth/realms/cadde-authentication" -H "Authorization:{トークン}" -o {出力ファイル名}
```

- x-cadde-resource-urlヘッダに設定したファイルが取得できれば動作確認は完了です。


# (参考)設定値一覧
動作確認環境で使用している設定値について記載します。

### 利用者/提供者共通
- CADDEユーザID：cadde:verify_user01.aa
- CADDEユーザIDのパスワード：uVa1BvnKas_5odW

### 利用者側コネクタ
#### connector/src/consumer/connector-main/swagger_server/configs/connector.json
- 利用者コネクタのID(consumer_connector_id)：https://verify-consumer.test.data-linkage.jp/
- 利用者コネクタのシークレット(consumer_connector_secret)：25f1c50c-15e6-45d7-a918-cd273d43e276
#### connector/src/consumer/authentication-authorization/swagger_server/configs/authentication.json
- 認証サーバのURL(authentication_server_url) ：https://key-authen.test.data-linkage.jp/auth/realms/cadde-authentication


### 提供者側コネクタ
#### connector/src/provider/authentication-authorization/swagger_server/configs/authentication.json
- 認可サーバのURL(authentication_server_url) ：https://key-author.test.data-linkage.jp/auth/realms/cadde-verify-authorization
#### connector/src/provider/connector-main/swagger_server/configs/connector.json
- 提供者コネクタのID(provider_connector_id) ：https://verify-provider.test.data-linkage.jp/
- 提供者コネクタのシークレット(provider_connector_secret) ：dcfe2dbf-8cd1-4dd3-8512-8c7f044348aa


