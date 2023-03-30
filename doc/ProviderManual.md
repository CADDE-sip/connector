
# 提供者環境構築ガイド
提供者サーバ環境として事前に準備する必要がある項目について下記に記載します。

## 1. 提供者用データ管理サーバ(FTPサーバ or HTTPサーバ or NGSIサーバ)
事前にFTPサーバ or HTTPサーバ or NGSIサーバが起動していること。
各サーバにデータが登録されていることが前提。

## 2. 詳細検索用カタログサイト(CKAN)
 詳細検索用カタログサイトには、提供者コネクタ経由で取得可能なすべてのカタログ詳細情報を登録します。
 各カタログ設定項目についての詳細については、(参考1) SIPデータカタログ項目仕様参照のこと。

## 3. 横断検索用カタログサイト(CKAN)
 横断検索用カタログサイトには、横断検索サーバに公開可能なカタログ情報を登録します。
 各提供者の横断検索用カタログサイトのカタログ情報は、横断検索サーバに横断検索用カタログサイトアクセスURLを設定することにより、定期的に収集されます。<br>

### (1) CADDE内限定データのカタログ項目<br>
　提供者コネクタ経由で詳細カタログ検索、データ取得可能とするために、横断検索用カタログサイトのカタログに下記項目設定が必須です。
- CADDEユーザID(提供者) (extras:caddec_provider_id) 事前に払い出されたCADDEユーザID(提供者)を設定。
- 詳細検索用データセットID (extras:caddec_dataset_id_for_detail) 横断検索用カタログと対になる詳細検索用カタログのデータセットIDを設定。
- リソース提供手段の識別子 (resources:caddec_resource_type): HTTPサーバの場合:file/http, FTPサーバの場合:file/ftp, NGSIサーバの場合:api/ngsi を設定。
- コネクタ利用の要否 (resources:caddec_contract_required): requiredを設定

### (2) オープンデータのカタログ項目<br>
　提供者コネクタ経由で詳細カタログ検索、データ取得しないオープンデータの場合、横断カタログサイトのカタログに下記項目設定は不要です。
- CADDEユーザID(提供者) (extras:caddec_provider_id) : カタログ項目を設定しない。
- 詳細検索用データセットID (extras:caddec_dataset_id_for_detail) : カタログ項目を設定しない。
- リソース提供手段の識別子 (resources:caddec_resource_type): カタログ項目を設定しない。
- コネクタ利用の要否 (resources:caddec_contract_required): notRequired または requiredを設定

## 4. 提供者内で認証なし・認可なしでの提供者コネクタ動作確認

<br>提供者コネクタの外部API経由で、データ管理サーバ(HTTP or FTP or NGSI)からデータを取得できることを確認する方法を以下に示します。<br>
{リソースURL}には、詳細検索用CKAN登録済みで提供者コネクタからアクセス可能なデータ管理サーバのデータアクセス先を指定します<br>
提供者コネクタのデータ管理サーバコンフィグ(http.json、ftp.json、ngsi.json)の認可設定、取引市場使用有無設定、来歴登録設定に該当のリソースURLを記載し、enableをfalseに指定してください。<br>
- 例1: `ftp://192.168.0.1/xxx.pdf`
```
ftp.json
    "authorization": [
        {
            "url": "ftp://192.168.0.1/",
            "enable" : false
        }
    ],
    "contract_management_service": [
        {
            "url": "ftp://192.168.0.1/",
            "enable" : false
        }
    ],
    "register_provenance": [
        {
            "url": "ftp://192.168.0.1/",
            "enable" : false
        }
    ]
```
- 例2: `http://192.168.0.1/auth/xxx.csv`
```
http.json
    "authorization": [
        {
            "url": "http://192.168.0.1/auth/",
            "enable" : false
        }
    ],
    "contract_management_service": [
        {
            "url": "http://192.168.0.1/auth/",
            "enable" : false
        }
    ],
    "register_provenance": [
        {
            "url": "http://192.168.0.1/auth/",
            "enable" : false
        }
    ]
```

### (1) データ管理サーバ(HTTPサーバ)を提供者コネクタAPI経由で取得する場合
```
curl {提供者コネクタIPアドレス}/cadde/api/v4/file -H "x-cadde-resource-url:{リソースURL}" -H "x-cadde-resource-api-type:file/http" -O
```

### (2) データ管理サーバ(FTPサーバ)を提供者コネクタAPI経由で取得する場合
```
curl {提供者コネクタIPアドレス}/cadde/api/v4/file -H "x-cadde-resource-url:{リソースURL}" -H "x-cadde-resource-api-type:file/ftp" -O
```

### (3) データ管理サーバ(NGSIサーバ)を提供者コネクタ経由で公開する場合
<br>NGSI情報取得については、[別紙参照](doc/README_NGSI.md) 

<br>


## 5. リソース認可設定
　提供者環境内のリソースに対して、アクセス許可を与える場合は、認可機能に対して認可設定を設定する必要があります。
　(1)アクセストークン取得APIを使用し、トークン取得後、（2-1)認可設定APIにより、指定したリソースに対する認可設定、(2-2)認可削除APIにより、指定したリソースに対する認可削除を行えます。
 
　※CADDEユーザIDを申請時に、アクセストークン取得時に必要な提供者クライアントID、シークレットを提供いたします。

### (1) アクセストークン取得
```
curl -v -X POST https://key-authen.test.data-linkage.jp/cadde/api/v4/token -H "Cache-Control: no-cache" -H "Content-Type: application/json" -H "Authorization:Basic {クライアントID:シークレットをBase64エンコードした文字列}" -d '{ "consumer_id": "{CADDEユーザID(提供者)}", "password": "{提供者のパスワード}" }'
```

### (2-1) 認可設定
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
    "trade_id": "string",
    "contract_url": "string",
    "contract_type": "string"
  }
}' 
```

### (2-2) 認可削除
```
curl -v -X DELETE https://{提供者コネクタのFQDN}:{ポート番号}/cadde/api/v4/authorization -H "Content-Type: application/json" -H "Authorization:Bearer {認証トークン}" \
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
    "trade_id": "string"
  }
}' 
```

### (2-3) 認可一覧取得
```
curl -v -X GET https://{提供者コネクタのFQDN}:{ポート番号}/cadde/api/v4/authorization_list -H "Content-Type: application/json" -H "Authorization:Bearer {認証トークン}" -d '{ "assigner": "{CADDEユーザID(提供者)}" }' 
```

### (2-4) 認可取得
```
curl -v -X GET https://{提供者コネクタのFQDN}:{ポート番号}/cadde/api/v4/authorization -H "Content-Type: application/json" -H "Authorization:Bearer {認証トークン}" -d '{ "assigner": "{CADDEユーザID(提供者)}",  "target": "{リソースURL}" }' 
```

# (参考1) 認可設定のパラメータ

### 1. Authorization ヘッダ

認証トークンを示すヘッダです。

  | Authorization | 概要                                |
  | :------------ | :---------------------------------- |
  | トークンの値  | 認証機能が発行するトークンを設定します。（Bearer指定） |


### 2. ボディ

認可設定時に指定するパラメータです。

  | パラメータ     | 概要                                            |
  | :------------- | :---------------------------------------------- |
  | permission     | 認可情報                                        |
  | target         | 認可の対象とするリソースURL                     |
  | assigner       | 認可される対象となるCADDEユーザID(提供者)       |
  | assignee       | 認可の判定対象（いずれか1つ以上を指定する）     |
  | user           | 認可の対象となるCADDEユーザID(利用者)           |
  | org            | 認可の対象となるCADDEユーザが所属する組織のID   |
  | aal            | 認可の対象となるCADDEユーザのAAL                |
  | extras         | 認可の対象となるCADDEユーザの属性情報           |
  | contract       | 認可に紐づく契約情報                            |
  | trade_id       | 対象の認可に紐づく取引ID                        |
  | contract_url   | 対象の認可に紐づく契約管理サービスのアクセスURL |
  | contract_type  | 対象の認可に紐づく契約形態                      |


# (参考2) SIPデータカタログ項目仕様
横断検索用カタログサイト、詳細検索用カタログサイトに登録するカタログ仕様の詳細については、下記を参照してください。
- [CADDE4.0 データカタログ項目仕様(2023年3月版)_1.xlsx](catalog/CADDE4.0_データカタログ項目仕様(2023年3月版)_1.xlsx)
- [CADDE4.0 データカタログ項目仕様ガイドライン(2023年3月版)_1.pptx](catalog/CADDE4.0_データカタログ項目仕様ガイドライン(2023年3月版)_1.pptx)
- [CADDE4.0 データカタログ項目仕様ガイドライン付録_横断検索解説(2023年3月版)_1.xlsx](catalog/CADDE4.0_データカタログ項目仕様ガイドライン付録_横断検索解説(2023年3月版)_1.xlsx)

