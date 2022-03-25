
# 提供者環境構築ガイド
提供者サーバ環境として事前に準備する必要がある項目について下記に記載します。

### 1. 提供者用データ管理サーバ(FTPサーバ or HTTPサーバ or NGSIサーバ)
事前にFTPサーバ or HTTPサーバ or NGSIサーバが起動していること。
各サーバにデータが登録されていることが前提。

### 2. 詳細検索用カタログサイト(CKAN)
 詳細検索用カタログサイトには、提供者コネクタ経由で取得可能なすべてのカタログ詳細情報を登録します。
 各カタログ設定項目についての詳細については、(参考1) SIPデータカタログ項目仕様参照のこと。

### 3. 横断検索用カタログサイト(CKAN)
 横断検索用カタログサイトには、横断検索サーバに公開可能なカタログ情報を登録します。
 各提供者の横断検索用カタログサイトのカタログ情報は、横断検索サーバに横断検索用カタログサイトアクセスURLを設定することにより、定期的に収集されます。<br>
 
(1) CADDE内限定データのカタログ項目<br>
　提供者コネクタ経由で詳細カタログ検索、データ取得可能とするために、横断検索用カタログサイトのカタログに下記項目設定が必須です。
- 提供者ID (extras:caddec_provider_id) 事前に払い出された提供者IDを設定。
- 詳細検索用データセットID (extras:caddec_dataset_id_for_detail) 横断検索用カタログと対になる詳細検索用カタログのデータセットIDを設定。
- リソース提供手段の識別子 (resources:caddec_resource_type): HTTPサーバの場合:file/http, FTPサーバの場合:file/ftp, NGSIサーバの場合:api/ngsi を設定。
- コネクタ利用の要否 (resources:caddec_contract_required): requiredを設定

(2) オープンデータのカタログ項目<br>
　提供者コネクタ経由で詳細カタログ検索、データ取得しないオープンデータの場合、横断カタログサイトのカタログに下記項目設定は不要です。
- 提供者ID (extras:caddec_provider_id) : カタログ項目を設定しない。
- 詳細検索用データセットID (extras:caddec_dataset_id_for_detail) : カタログ項目を設定しない。
- リソース提供手段の識別子 (resources:caddec_resource_type): カタログ項目を設定しない。
- コネクタ利用の要否 (resources:caddec_contract_required): notRequired または requiredを設定

### 4. リソース認可設定
　提供者環境内のリソースに対して、アクセス許可を与える場合は、認可サーバに対して認可設定を設定する必要があります。
　(1)アクセストークン取得APIを使用し、トークン取得後、（2-1)認可設定APIにより、指定したリソースに対する認可設定、(2-2)認可削除APIにより、指定したリソースに対する認可削除を行えます。
 
　※CADDEユーザIDを申請時に、アクセストークン取得時に必要な提供者クライアントID、シークレットについては提供いたします。

#### (1) アクセストークン取得
```
curl -v -X POST -H "Content-Type: application/json" -d "client_id={提供者のクライアントID}" -d "client_secret={提供者のシークレット}" https://key-author.test.data-linkage.jp/cadde/api/v1/apitoken
```

#### (2-1) 認可設定
```
curl -v -X POST -H "Content-Type: application/json" -H "Authorization: {アクセストークン}" -d'{"provider_id":"<提供者ID>", "consumer_id":"<利用者ID>","resource_url":"<リソースURL>"}' https://key-author.test.data-linkage.jp/cadde/api/v1/authorization
```

#### (2-2) 認可削除
```
curl -v -X DELETE -H "Content-Type: application/json" -H "Authorization: {アクセストークン}" -d'{"provider_id":"<提供者ID>", "consumer_id":"<利用者ID>","resource_url":"<リソースURL>" }' https://key-author.test.data-linkage.jp/cadde/api/v1/authorization
```

# (参考1) SIPデータカタログ項目仕様
横断検索用カタログサイト、詳細検索用カタログサイトに登録するカタログ仕様の詳細については、下記を参照してください。
- [SIPデータカタログ項目仕様V1.2(2021年10月19日版).xlsx](catalog/SIPデータカタログ項目仕様V1.2(2021年10月19日版).xlsx)

