# 分野間データ連携基盤: 動作確認環境利用ガイド
- コネクタ環境構築後に、正常に動作するか等を確認するための動作確認環境を準備しています。
- 本ページでは動作確認環境の利用方法を記載しています。
![Alt text](png/OperatonCheck.png?raw=true "Title")


# 利用者コネクタ構築時の動作確認環境利用ガイド

## 前提
- 利用者コネクタのプロキシに動作確認環境専用のクライアント証明書が設定されていることを前提とします。<br>
  [証明書のダウンロードはこちらから](../misc/OperationCheck/OperationCheckClientCertificate.zip) 

## 動作確認手順
構築済みの利用者コネクタから動作確認環境の提供者コネクタに接続し、動作確認する手順です。
### 1. 認証トークン取得

```
curl -X POST -s https://authn.trial.data-linkage.jp/cadde/api/v4/token -H "Authorization:Basic {クライアントID:シークレットをBase64エンコードした文字列}" -H "Content-Type: application/json" -d '{"user_id": "{CADDEユーザID(利用者)}", "password": "{利用者のパスワード}"}'
```
以下の結果が出力されていれば認証トークンの取得完了です。

```
{"access_token":"{認証トークン}","refresh_token":"{リフレッシュトークン}"}
```

### 2. 詳細検索
- Authorizationヘッダには、1．認証トークン取得で発行したトークンの値を指定ください。
```
curl -X GET "http://{利用者コネクタのFQDN}:{ポート番号}/cadde/api/v4/catalog?fq=caddec_dataset_id_for_detail:69892235-883d-59cf-997c-3013f23dff9f" -s -S -H "Cache-Control: no-cache" -H "x-cadde-search: detail" -H "x-cadde-provider: cadde.operationcheck.aa" -H "Authorization:Bearer {認証トークン}"
```
以下の結果が出力されていれば詳細検索完了です。

```
{"help": "http://172.22.40.101:5500/api/3/action/help_show?name=package_search", "success": true, "result": {"count": 1,～省略～{}}}
```

### 3. ファイル取得
- Authorizationヘッダには、1．認証トークン取得で発行したトークンの値を指定ください。
```
curl -X GET "http://{利用者コネクタのFQDN}:{ポート番号}/cadde/api/v4/file" -s -S -H "Cache-Control: no-cache" -H "x-cadde-resource-url: http://data-management/operationcheck/data/operationcheck_example_http_detail.txt" -H "x-cadde-resource-api-type: file/http" -H "x-cadde-provider: cadde.operationcheck.aa" -H "Authorization:Bearer {認証トークン}" -o {出力ファイル名}
```

以下の結果が出力されていれば動作確認完了です。

```
#####

Successful download
operationcheck_example_http_detail.txt

#####
```

# 提供者コネクタ構築時の動作確認環境利用ガイド

## 前提
- 提供者コネクタのリバースプロキシに動作確認環境専用のCA証明書が設定されていることを前提とします。<br>
  [証明書のダウンロードはこちらから](../misc/OperationCheck/OperationCheckClientCertificate.zip) 
- 提供者コネクタ側の環境にFWが存在する場合、動作確認環境の利用者コネクタからの通信が許可されていることを前提とします。<br>
  動作確認環境の利用者コネクタのIPアドレスは「54.92.64.59/32」となりますので、必要に応じて許可設定をお願いします。

## 動作確認手順
動作確認環境の利用者コネクタから構築済みの提供者コネクタに接続し、動作確認する手順です。
curlコマンドを実行可能なコンソールより動作確認環境の利用者コネクタに対してコマンドを実行ください。

### 1. 認証トークン取得

```
curl -X POST -s https://authn.trial.data-linkage.jp/cadde/api/v4/token -H "Authorization:Basic Y29uc3VtZXItb3BlcmF0aW9uY2hlY2sudHJpYWwuZGF0YS1saW5rYWdlLmpwOm1BRk9CWjM5UDNaM1k4U2laYUN3Uk54dFlESE93U1Jz" -H "Content-Type: application/json" -d '{"user_id": "cadde.operationcheck.aa", "password": "tExSqL_m7S5G34i"}'
```
以下の結果が出力されていれば認証トークンの取得完了です。

```
{"access_token":"{認証トークン}","refresh_token":"{リフレッシュトークン}"}
```

### 2. 詳細検索

- 検索クエリ内の{詳細検索用データセットID} には、ご自身で作成したカタログの値(extras:caddec_dataset_id_for_detail)を設定ください。
- x-cadde-providerヘッダには、ご自身のCADDEユーザID(提供者)を指定ください。
- Authorizationヘッダには、1．認証トークン取得で発行したトークンの値を指定ください。

```
curl -X GET "https://consumer-operationcheck.trial.data-linkage.jp/cadde/api/v4/catalog?fq=caddec_dataset_id_for_detail:{詳細検索用データセットID}" -s -S -H "Cache-Control: no-cache" -H "x-cadde-search: detail" -H "x-cadde-provider: {CADDEユーザID(提供者)}" -H "Authorization:Bearer {認証トークン}"
```

以下の結果が出力されていれば詳細検索完了です。

```
{"help": "http://CKAN_URL/api/3/action/help_show?name=package_search", "success": true, "result": {"count": 1,～省略～{}}}
```

### 3. ファイル取得

- x-cadde-resource-urlヘッダには、詳細カタログ検索結果(resources:download_url)から取得したファイルのダウンロードURLを指定ください。
- x-cadde-resource-api-typeヘッダには、詳細カタログ検索結果(resources:caddec_resource_type)から取得したリソース提供手段の識別子(file/http or file/ftp)を指定ください。
- x-cadde-providerヘッダには、ご自身のCADDEユーザID(提供者)を指定ください。
- Authorizationヘッダには、1．認証トークン取得で発行したトークンの値を指定ください。

```
curl -X GET "https://consumer-operationcheck.trial.data-linkage.jp/cadde/api/v4/file" -s -S -H "Cache-Control: no-cache" -H "x-cadde-resource-url: {リソースURL}" -H "x-cadde-resource-api-type: {リソース提供手段の識別子}" -H "x-cadde-provider: {CADDEユーザID(提供者)}" -H "Authorization:Bearer {認証トークン}" -o {出力ファイル名}
```

- x-cadde-resource-urlヘッダに設定したファイルが取得できれば動作確認は完了です。


# (参考)設定値一覧
動作確認環境で使用している設定値について記載します。

### 利用者/提供者共通
- CADDEユーザID：cadde.operationcheck.aa
- CADDEユーザIDのパスワード：tExSqL_m7S5G34i

### 利用者側コネクタ
#### connector/src/consumer/connector-main/swagger_server/configs/connector.json
- 利用者コネクタのID(consumer_connector_id)：consumer-operationcheck.trial.data-linkage.jp
- 利用者コネクタのシークレット(consumer_connector_secret)：mAFOBZ39P3Z3Y8SiZaCwRNxtYDHOwSRs


### 提供者側コネクタ
#### connector/src/provider/connector-main/swagger_server/configs/connector.json
- 提供者コネクタのID(provider_connector_id) ：ip-172-22-40-101.ap-northeast-1.compute.internal
- 提供者コネクタのシークレット(provider_connector_secret) ：ql6ERT1IH3ody6I8NkjKvnYshfcGdnjm


