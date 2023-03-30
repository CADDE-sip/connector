
# 利用者コネクタ利用ガイド
コネクタを使用し、カタログを検索し、データ取得する方法を下記2つのケースについて説明します。
- (1) 利用者コネクタ、提供者コネクタを経由し、データ管理サーバ(HTTP or FTP or NGSI)からデータを取得するケース
- (2) 利用者コネクタから提供者コネクタを経由せず、データ管理サーバ(HTTP or FTP or NGSI)から直接オープンデータを取得するケース
- (3) 利用者コネクタを経由し、来歴管理に対して来歴情報(来歴確認 or API履歴ID検索)を取得するケース

## (1) 利用者コネクタ、提供者コネクタを経由し、データ管理サーバ(HTTP or FTP or NGSI)からデータを取得するケース
### (1-1) 横断検索 
横断検索サーバに対してカタログ検索を実行します。<br>
APIの実行例を下記に示します。<br>
- x-cadde-searchヘッダには、'meta'を指定。<br>
- 検索クエリ内の{検索キー}には、検索文字列を指定。<br>
```
$ curl -v -X GET "http://{利用者コネクタのFQDN}:{ポート番号}/cadde/api/v4/catalog?q={検索キー}" -s -S -H "Cache-Control: no-cache" -H "x-cadde-search: meta"
```

### (1-2) 詳細検索
提供者が持つ詳細検索用カタログサイト(CKAN)対してカタログ検索を実行します。<br>
APIの実行例を下記に示します。<br>
- x-cadde-searchヘッダには、'detail'を指定。
- x-cadde-providerヘッダには、横断カタログ検索結果(extras:caddec_provider_id)から取得したCADDEユーザID(提供者)を指定。
- Authorizationヘッダには、認証・認可を行う場合は認証機能が発行したトークンの値を指定。認証・認可を行わない場合はヘッダ未設定。
- 検索クエリ内の{詳細検索用データセットID} には、横断カタログ検索結果(extras:caddec_dataset_id_for_detail)の値を設定
```
$ curl -v -X GET 'http://{利用者コネクタのFQDN}:{ポート番号}/cadde/api/v4/catalog?fq=caddec_dataset_id_for_detail:{詳細検索用データセットID}' -s -S -H "Cache-Control: no-cache" -H "x-cadde-search: detail" -H "x-cadde-provider: {CADDEユーザID(提供者)}" -H "Authorization:Bearer {認証トークン}"
```

### (1-3) ファイル取得
横断 or 詳細カタログ検索結果のカタログ情報を元に、ファイル取得APIを利用し、HTTPサーバ or FTPサーバ or NGSIサーバからデータを取得します。<br>
リソース提供手段の識別子がfile/http, file/ftp の場合は、(1-3-1)ファイル取得(CADDE) APIを実行。<br>
リソース提供手段の識別子がapi/ngsi の場合は、(1-3-2)ファイル取得(NGSI) APIを実行。

### (1-3-1) ファイル取得(CADDE) 
カタログ検索結果の情報を元に提供者データ管理(HTTPサーバ or FTPサーバ)からファイルを取得します。<br>
APIの実行例を下記に示します。<br>
- x-cadde-providerヘッダには、詳細カタログ検索結果(extras:caddec_provider_id)から取得したCADDEユーザID(提供者)を指定。
- x-cadde-resource-urlヘッダには、詳細カタログ検索結果(resources:download_url)から取得したファイルのダウンロードURLを指定。
- x-cadde-resource-api-typeヘッダには、詳細カタログ検索結果(resources:caddec_resource_type)から取得したリソース提供手段の識別子(file/http or file/ftp)を指定。
- Authorizationヘッダには、認証・認可を行う場合は認証機能が発行したトークンの値を指定。認証・認可を行わない場合はヘッダ未設定。

```
$ curl -v -X GET "http://{利用者コネクタのFQDN}:{ポート番号}/cadde/api/v4/file" -s -S -H "Cache-Control: no-cache" -H "x-cadde-resource-url: {リソースURL}" -H "x-cadde-resource-api-type: {リソース提供手段の識別子}" -H "x-cadde-provider: {CADDEユーザID(提供者)}" -H "Authorization:Bearer {認証トークン}" -o {出力ファイル名}
```

### (1-3-2) ファイル取得(NGSI)
NGSI情報取得については、[別紙参照](./README_NGSI.md) 


## (2) 利用者コネクタから提供者コネクタを経由せず、データ管理サーバ(HTTP or FTP or NGSI)から直接オープンデータを取得するケース
提供者コネクタが設置されていないデータ管理サーバからデータを取得する場合のAPI実行方法を下記に示します。

### (2-1) 横断検索　※(1-1) と同様
横断検索サーバに対してカタログ検索を実行します。<br>
APIの実行例を下記に示します。<br>
- x-cadde-searchヘッダには、'meta'を指定。<br>
- 検索クエリ内の{検索キー}には、検索文字列を指定。<br>
```
$ curl -v -X GET "http://{利用者コネクタのFQDN}:{ポート番号}/cadde/api/v4/catalog?q={検索キー}" -s -S -H "Cache-Control: no-cache" -H "x-cadde-search: meta"
```

### (2-2) ファイル取得
横断検索結果のカタログ結果を元に、ファイル取得APIを利用し、HTTPサーバ or FTPサーバ or NGSIサーバからデータを取得します。<br>
リソース提供手段の識別子がfile/http, file/ftp の場合は、(2-2-1)ファイル取得(CADDE) APIを実行。<br>
リソース提供手段の識別子がapi/ngsi の場合は、(2-2-2)ファイル取得(NGSI) APIを実行。

### (2-2-1) ファイル取得(CADDE)
横断検索カタログ結果を元に提供者データ管理(HTTPサーバ)から直接オープンデータを取得します。<br>
APIの実行例を下記に示します。<br>
- x-cadde-resource-urlヘッダには、横断カタログ検索結果(resources:download_url)から取得したファイルのダウンロードURLを指定。
- x-cadde-resource-api-typeヘッダには、横断カタログ検索結果(resources:caddec_resource_type)から取得したリソース提供手段の識別子(file/http or file/ftp)を指定。
- Authorizationヘッダには、認証・認可を行う場合は認証機能が発行したトークンの値を指定。認証・認可を行わない場合はヘッダ未設定。

```
$ curl -v -X GET "http://{利用者コネクタのFQDN}:{ポート番号}/cadde/api/v4/file" -s -S -H "Cache-Control: no-cache" -H "x-cadde-resource-url: {リソースURL}" -H "x-cadde-resource-api-type: {リソース提供手段の識別子}" -H "Authorization:Bearer {認証トークン}" -o {出力ファイル名}
```

### (2-2-2) ファイル取得(NGSI)
NGSI情報取得については、[別紙参照](./README_NGSI.md) 



## (3) 来歴管理に対して来歴情報(来歴確認 or 履歴ID検索)を取得するケース
### (3-1) 来歴確認 
来歴管理サービスに対して来歴確認を実行します。<br>
APIの実行例を下記に示します。<br>
- x-directionヘッダには、履歴取得方向(BACKWARD(=default)、FORWARD、 BOTH)を指定。<br>
- x-depthヘッダには、換実績記録用リソースIDで指定されたイベントからの深さを指定(-1を指定するとすべて取得)。<br>
- x-caddec-resource-id-for-provenanceヘッダには、対象の交換実績記録用リソースIDを指定。<br>

```
$ curl -v -X GET "http://{来歴管理サービスのFQDN}:{ポート番号}/v2/lineage/{caddec-resource-id-for-provenance}" -H "Cache-Control: no-cache" -H "Authorization:Bearer {認証トークン}" -H "x-direction:BACKWARD" -H "x-depth:-1" 
```

### (3-2) API履歴ID検索 
来歴管理サービスに対してAPI履歴ID検索を実行します。<br>
APIの実行例を下記に示します。<br>
- ボディにはJSON形式で{"selector":{ 検索条件 }}を指定します。

```
$ curl -v -X POST "http://{来歴管理サービスのFQDN}:{ポート番号}/v2/searchevents" -H "Cache-Control: no-cache" -H "Content-Type: application/json" -H "Authorization:Bearer {認証トークン}" -d '{"selector": { "cdleventid":"<識別情報>" }}'
```

# (参考1) データ取得I/Fのパラメータとデータカタログの紐づけ
### 1.  x-cadde-resource-url ヘッダ

データを取得するためのAPIのリソースURLを指定します。

本リクエストヘッダに対応するデータカタログの項目は以下の通りです。

  | APIリクエストヘッダ  | カタログ項目          | カタログパラメータ     |
  | :------------------- | :-------------------- | :--------------------- |
  | x-cadde-resource-url | 配信のダウンロードURL | resources:download_url |

### 2. x-cadde-resource-api-type ヘッダ

CADDEコネクタがリソースの提供手段を特定するために用いる識別子です。

  | x-cadde-resource-api-type | 概要                                                               |
  | :------------------------ | :----------------------------------------------------------------- |
  | file/http                 | HTTPサーバデータを取得する場合file/httpを指定する必要があります。  |
  | file/ftp                  | FTPサーバデータを取得する場合file/ftpを指定する必要があります。    |
  | api/ngsi                  | NGSIサーバデータを取得する場合api/ngsiを指定する必要があります。   |
<br>
本ヘッダに対応するデータカタログの項目は以下の通りです。

  | APIリクエストヘッダ       | カタログ項目             | カタログパラメータ             |
  | :------------------------ | :----------------------- | :----------------------------- |
  | x-cadde-resource-api-type | リソース提供手段の識別子 | resources:caddec_resource_type |
<br>

### 3. x-cadde-provider ヘッダ

CADDE利用者コネクタがデータ提供者を特定するために用いる識別子です。

  | x-cadde-provider        | 概要                                            |
  | :---------------------- | :---------------------------------------------- |
  | {CADDEユーザID(提供者)} | 情報提供先のCADDEユーザID(提供者)を指定します。 |

<br>
<br>
本ヘッダに対応するデータカタログの項目は以下の通りです。

  | APIリクエストヘッダ | カタログ項目          | カタログパラメータ         |
  | :------------------ | :-------------------- | :------------------------- |
  | x-cadde-provider    | CADDEユーザID(提供者) | extras:caddec_provider_id  |
<br>

### 4. Authorization ヘッダ

認証トークンを示すヘッダです。

  | Authorization | 概要                                                   |
  | :------------ | :----------------------------------------------------- |
  | トークンの値  | 認証機能が発行するトークンを設定します。（Bearer指定） |
<br>

トークンは、下記コマンドによって得られるレスポンスのaccess_tokenを使用する。
```
$ curl -v -X POST https://key-authen.test.data-linkage.jp/cadde/api/v4/token -H "Cache-Control: no-cache" -H "Content-Type: application/json" -H "Authorization:Basic {クライアントID:シークレットをBase64エンコードした文字列}" -d '{ "consumer_id": "{CADDEユーザID(利用者)}", "password": "{利用者のパスワード}" }'
```

# (参考2) SIPデータカタログ項目仕様
横断検索、詳細検索によって取得できるカタログ仕様の詳細については、下記を参照してください。
- [CADDE4.0 データカタログ項目仕様(2023年3月版)_1.xlsx](catalog/CADDE4.0_データカタログ項目仕様(2023年3月版)_1.xlsx)
- [CADDE4.0 データカタログ項目仕様ガイドライン(2023年3月版)_1.pptx](catalog/CADDE4.0_データカタログ項目仕様ガイドライン(2023年3月版)_1.pptx)
- [CADDE4.0 データカタログ項目仕様ガイドライン付録_横断検索解説(2023年3月版)_1.xlsx](catalog/CADDE4.0_データカタログ項目仕様ガイドライン付録_横断検索解説(2023年3月版)_1.xlsx)

