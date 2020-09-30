# CADDEコネクタを利用した NGSIデータの取得方法

## 利用者コネクタAPI

コネクタを利用してNGSIデータを取得するには、利用者コネクタが提供する REST-APIを使用する必要があります。<br>
利用者コネクタが提供する REST-APIの詳細については下記から利用者コネクタメインのAPI仕様書をダウンロードし、参照してください。<br>

- [RESTAPI仕様書格納先](./api/)
<br>
<br>

## データ取得I/F(NGSI)のパラメタとデータカタログの紐づけ
### 1.  x-cadde-resource-url ヘッダ

NGSIデータを取得するためのAPIのリソースURLを指定します。<br>
CADDEコネクタを使用してデータを取得する場合、以下の2種類のURLが指定可能です。

  | NGSIで指定可能URL | 概要 |
  | :------------- | :-------------------------- |
  | {NGSI取得先URL}/entities?type={entityType} | **エンティティの一覧を取得するURL**<br>{entityType}で指定したtypeを持つエンティティの一覧を取得する。<br>例）https://{ドメイン名}/v2/entities?type= Room|
  | {NGSI取得先URL}/entities/{entityId} | **任意のエンティティを取得するURL**<br>{entityId}で指定したエンティティの情報を取得する。<br> 例）https://{ドメイン名}/v2/entities/Bcn_Welt|

<br>
また、NGSIデータを取得するAPIにクエリパラメータを指定する場合は本ヘッダに指定するURLにクエリパラメータをしてください。<br>
<br>
　例）{NGSI取得先URL}/entities?type=CareService&limit=10 
<br>
<br>
<br>
また、本ヘッダに対応するデータカタログの項目は以下の通りです。

  | APIリクエストヘッダ | カタログ項目 | カタログパラメータ |
  | :------------------ | :-------------------------- | :---------- |
  | x-cadde-resource-url | 配信のアクセスURL | resource:access_url |
<br>

### 2. x-cadde-resource-api-type

CADDEコネクタがリソースの提供手段を特定するために用いる識別子です。

  | x-cadde-resource-api-type | 概要 |
  | :------------- | :-------------------------- |
  | api/ngsi | NGSI形式のデータを取得する場合”api/ngsi”を指定する必要があります。|
<br>
<br>
また、本ヘッダに対応するデータカタログの項目は以下の通りです。

  | APIリクエストヘッダ | カタログ項目 | カタログパラメータ |
  | :------------------ | :-------------------------- | :---------- |
  | x-cadde-resource-api-type | リソース提供手段の識別子 | resource:caddec_resource_type |
<br>

### 3. x-cadde-provider

CADDE利用者コネクタがデータ提供者を特定するために用いる識別子です。

  | x-cadde-provider | 概要 |
  | :------------- | :-------------------------- |
  | {提供者ID} | NGSI情報提供先の提供者IDを指定します。|

<br>
<br>
また、本ヘッダに対応するデータカタログの項目は以下の通りです。

  | APIリクエストヘッダ | カタログ項目 | カタログパラメータ |
  | :------------------ | :-------------------------- | :---------- |
  | x-cadde-provider | 提供者ID | extras:caddec_provider_id |
<br>

### 4. x-cadde-contract

CADDEコネクタがデータセットまたはリソースを利用するために契約の確認を要するか否かを表す識別子です。

  | x-cadde-contract | 概要 |
  | :------------- | :-------------------------- |
  | required または notRequired | 2020年9月の時点ではnotRequiredを指定してください。|

<br>
<br>
また、本ヘッダに対応するデータカタログの項目は以下の通りです。

  | APIリクエストヘッダ | カタログ項目 | カタログパラメータ |
  | :------------------ | :-------------------------- | :---------- |
  | x-cadde-contract | 契約確認の要否 | resource:caddec_contract_required |

<br>

### 5. Authorization

利用者トークンを示すヘッダです。

  | Authorization | 概要 |
  | :------------- | :-------------------------- |
  | トークンの値 | 2020年9月の時点では使用しません。|
<br>
<br>

### 6. x-cadde-options

API固有のヘッダを本ヘッダに指定することができます。<br>
例として、NGSIデータを提供するデータ管理サーバに Orionを使用している場合、Orionでは、リクエストヘッダとしてFiware-ServiceおよびFiware-ServicePathを指定することで、マルチテナントおよびマルチサービスの機能を提供していますが、Fiware-Serviceおよび Fiware-ServicePathを本ヘッダに指定することができます。

  | x-cadde-options | 概要 |
  | :------------- | :-------------------------- |
  | {ヘッダ項目}:{ヘッダの値}, {ヘッダ項目2}:{ヘッダの値2}, … | API固有のリクエストヘッダ<br>NGSIデータを取得する際にAPIで固有のリクエストヘッダが必要となる場合に、そのヘッダを指定します。<br>ただし、ヘッダの値に ,(カンマ)を含むものは指定できません。<br>例）Fiware-Service:abc,Fiware-ServicePath:/path1
<br>

## APIの実行例

### 1. エンティティの一覧を取得する場合。
```
$ curl -v -k -X GET "https://{利用者コネクタのドメイン}:{ポート番号}/v2/entities" -s -S --header "x-cadde-resource-url: https://{NGSIデータ管理サーバのドメイン名}/v2/entities?type=Room" --header "x-cadde-resource-api-type: api/ngsi"  --header "x-cadde-contract: notRequired"  --header "x-cadde-options: Fiware-Service:abc, Fiware-ServicePath:/path1" --header "x_cadde_provider: test_id_A" --header "Authorization: dummy"
```

```
[
    {
        "type": "Room",
        "id": "DC_S1-D41",
        "temperature": {
            "value": 35.6,
            "type": "Number",
            "metadata": {}
        }
    },
    {
        "type": "Room",
        "id": "Boe-Idearium",
        "temperature": {
            "value": 22.5,
            "type": "Number",
            "metadata": {}
        }
    }
]
```
<br>

### 2. 任意のエンティティを指定してデータを取得する場合
```
$ curl -v -k -X GET "https://{利用者コネクタのドメイン}:{ポート番号}/v2/entities" -s -S --header "x-cadde-resource-url: https://{NGSIデータ管理サーバのドメイン名}/v2/entities/DC_S1-D41?type=Room" --header "x-cadde-resource-api-type: api/ngsi"  --header "x-cadde-contract: notRequired"  --header "x-cadde-options: Fiware-Service:abc, Fiware-ServicePath:/path1" --header "x_cadde_provider: test_id_A" --header "Authorization: dummy"
```

```
{
    "type": "Room",
    "id": "DC_S1-D41",
    "temperature": {
        "value": 35.6,
        "type": "Number",
        "metadata": {}
    }
}
```
<br>

