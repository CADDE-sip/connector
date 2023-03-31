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
認可が必要なNGSIデータの場合は、クエリパラメータを含めたリソースのURL（カタログ項目：配信のダウンロードURL）に一致するデータのみ指定可能です。<br>
認可が不要なNGSIデータの場合は、リソースURL（カタログ項目：配信のダウンロードURL）の範囲のデータの取得条件であれば、以下の2種類のURL、クエリパラメータが指定可能です。

  | NGSIで指定可能URL | 概要 |
  | :------------- | :-------------------------- |
  | {NGSI取得先URL}/entities?type={entityType} | **エンティティの一覧を取得するURL**<br>{entityType}で指定したtypeを持つエンティティの一覧を取得する。<br>例）https://{ドメイン名}/v2/entities?type= Room|
  | {NGSI取得先URL}/entities/{entityId}?type={entityType} | **任意のエンティティを取得するURL**<br>{entityId}で指定したエンティティの情報を取得する。{entityType}には{entityID}が属するentityTypeを指定する。<br> 例）https://{ドメイン名}/v2/entities/Bcn_Welt?type=Room|

<br>
NGSIデータを取得するAPIにクエリパラメータを指定する場合は本ヘッダに指定するURLにクエリパラメータをしてください。<br>
<br>
　例）{NGSI取得先URL}/entities?type=CareService&limit=10 
<br>
<br>

### 2. x-cadde-resource-api-type

CADDEコネクタがリソースの提供手段を特定するために用いる識別子です。

  | x-cadde-resource-api-type | 概要 |
  | :------------- | :-------------------------- |
  | api/ngsi | NGSI形式のデータを取得する場合”api/ngsi”を指定する必要があります。|
<br>

### 3. x-cadde-provider

CADDE利用者コネクタがデータ提供者を特定するために用いる識別子です。

  | x-cadde-provider | 概要 |
  | :------------- | :-------------------------- |
  | {CADDEユーザID(提供者)} | NGSI情報提供先のCADDEユーザID(提供者)を指定します。|

<br>

### 4. Authorization

利用者トークンを示すヘッダです。

  | Authorization | 概要 |
  | :------------- | :-------------------------- |
  | トークンの値 | 利用者トークンを設定します。|
<br>
<br>

### 5. x-cadde-options

API固有のヘッダを本ヘッダに指定することができます。<br>
例として、NGSIデータを提供するデータ管理サーバに Orionを使用している場合、Orionでは、リクエストヘッダとしてFiware-ServiceおよびFiware-ServicePathを指定することで、マルチテナントおよびマルチサービスの機能を提供していますが、Fiware-Serviceおよび Fiware-ServicePathを本ヘッダに指定することができます。

  | x-cadde-options | 概要 |
  | :------------- | :-------------------------- |
  | {ヘッダ項目}:{ヘッダの値}, {ヘッダ項目2}:{ヘッダの値2}, … | API固有のリクエストヘッダ<br>NGSIデータを取得する際にAPIで固有のリクエストヘッダが必要となる場合に、そのヘッダを指定します。<br>ただし、ヘッダの値に ,(カンマ)を含むものは指定できません。<br>例）Fiware-Service:abc,Fiware-ServicePath:/path1
<br>

## カタログ項目とAPIの関係
### 1. x-cadde-resource-urlヘッダ
x-cadde-resource-urlヘッダの値はデータカタログ項目の「配信のダウンロードURL」です。

  | APIリクエストヘッダ | カタログ項目 | カタログパラメータ |
  | :------------------ | :-------------------------- | :---------- |
  | x-cadde-resource-url | 配信のダウンロードURL | resources:url |
<br>
<br>

### 2. x-cadde-resource-api-typeヘッダ
x-cadde-resource-api-typeヘッダの値はデータカタログ項目の「リソース提供手段の識別子」が対応します。

  | APIリクエストヘッダ | カタログ項目 | カタログパラメータ |
  | :------------------ | :-------------------------- | :---------- |
  | x-cadde-resource-api-type | リソース提供手段の識別子 | resources:caddec_resource_type |
<br>
<br>

### 3. x-cadde-providerヘッダ
x-cadde-providerヘッダの値はデータカタログ項目の「CADDEユーザID(提供者)」が対応します。

  | APIリクエストヘッダ | カタログ項目 | カタログパラメータ |
  | :------------------ | :-------------------------- | :---------- |
  | x-cadde-provider | CADDEユーザID(提供者) | extras:caddec_provider_id |
<br>
<br>

### 4. x-cadde-optionsヘッダ
x-cadde-optionsヘッダを利用することで、Fiware-ServiceおよびFiware-ServicePathを指定することができます。
<br>
Fiware-ServiceおよびFiware-ServicePathの値はデータカタログ項目の「NGSIテナント」、「NGSIサービスパス」の値が対応します。

  | APIリクエストヘッダ | カタログ項目 | カタログパラメータ |
  | :------------------ | :-------------------------- | :---------- |
  | x-cadde-options | NGSIテナント<br>NGSIサービスパス | resources:ngsi_tenant<br>resources:ngsi_service_path |
<br>
<br>


## API実行例
### curlコマンド実行イメージ

```
$ curl -v -X GET "http://{利用者コネクタのFQDN}:{ポート番号}/cadde/api/v4/entities"
　-H "x-cadde-resource-url: {配信のダウンロードURL}" 
　-H "x-cadde-resource-api-type: {リソース提供手段の識別子}" 
　-H "x-cadde-provider: {CADDEユーザID(提供者)}"
　-H "Authorization: Bearer {利用者トークン}"
　-H "x-cadde-options: Fiware-Service: {NGSIテナント}, Fiware-ServicePath: {NGSIサービスパス}"
```
<br>

### データカタログ項目の値を利用したAPI実行例
#### データカタログ項目の例

  | カタログ項目 | カタログパラメータ | 項目の値
  | :------------------ | :-------------------------- | :---------- |
  | 配信のダウンロードURL | resources:url | https://closed.XX.go.jo/v2/entities?type=PublicFacility |
  | NGSIデータ種別 | resources:ngsi_entity_type | PublicFacility |
  | リソース提供手段の識別子 | resources:caddec_resource_type | api/ngsi |
  | CADDEユーザID(提供者) | extras:caddec_provider_id | provider1@dataex.jp |
  | NGSIテナント | resources:ngsi_tenant | shinnihon |
  | NGSIテナントNGSIサービスパス | resources:ngsi_service_path | /shisetsu |


#### 上記のデータカタログ項目を利用したcurlコマンド実行例
```
$ curl -v -X GET "http://CADDE.Y.co.jp:888/cadde/api/v4/entities"
　-H "x-cadde-resource-url: https://closed.XX.go.jo/v2/entities?type=PublicFacility" 
　-H "x-cadde-resource-api-type: api/ngsi" 
　-H "x-cadde-provider: provider1@dataex.jp" 
　-H "Authorization: Bearer XXXX"
　-H "x-cadde-options: Fiware-Service: shinnihon, Fiware-ServicePath: /shisetsu"
```

<br>

### 任意のエンティティを指定してデータを取得する場合
#### 上記のデータ一覧から、「entity1」というエンティティデータのみを取得する例。認可が不要なデータの場合。
```
$ curl -v -X GET "http://CADDE.Y.co.jp:888/cadde/api/v4/entities"
　-H "x-cadde-resource-url: https://closed.XX.go.jo/v2/entities/entity1?type=PublicFacility" 
　-H "x-cadde-resource-api-type: api/ngsi" 
　-H "x-cadde-provider: provider1@dataex.jp" 
　-H "Authorization: Bearer XXXX"
　-H "x-cadde-options: Fiware-Service: shinnihon, Fiware-ServicePath: /shisetsu"
```
<br>



## NGSIデータモデル
NGSIデータの取得APIでは、x-cadde-resource-urlに指定するURLにクエリパラメータを指定することで、データの取得条件を指定することができます。<br>
認可が不要なデータの場合、データカタログ項目の「NGSIデータモデル」を参照することで、データの取得条件を利用者自身が決定することができます。

### 取得データの絞り込みを可能とするデータモデルと取得条件を指定した例

#### データカタログ項目の例

  | カタログ項目 | カタログパラメータ | 項目の値
  | :------------------ | :-------------------------- | :---------- |
  | 配信のダウンロードURL | resources:url | https://closed.XX.go.jo/v2/entities?type=PublicFacility |
  | NGSIデータ種別 | resources:ngsi_entity_type | PublicFacility |
  | リソース提供手段の識別子 | resources:caddec_resource_type | api/ngsi |
  | CADDEユーザID(提供者) | extras:caddec_provider_id | provider1@dataex.jp |
  | NGSIテナント | resources:ngsi_tenant | shinnihon |
  | NGSIテナントNGSIサービスパス | resources:ngsi_service_path | /shisetsu |
  | NGSIデータモデル | resources:ngsi_data_model |  { <br> 　attrs:{<br> 　　name: { <br> 　　　description: イベント名称,<br> 　　　types: Text,<br> 　　},<br> 　　fee: { <br> 　　　description: 入場料金,<br> 　　　types: Number,<br> 　　　metadata: {<br> 　　　　unit: {<br> 　　　　　description:単位<br> 　　　　}<br> 　　　}<br> 　　},<br> 　：<br> 　}<br> } |

<br> 

#### 例）全体のイベント情報から、入場料金が 800円より安いデータだけを抽出する
① 上記のデータカタログ項目の「NGSIデータモデル」を参照することで、公開されているデータは「fee」という項目が入場料金を示す項目であることがわかる。<br>
② 「fee」は数値（Number）型であることがわかる。
<br>

#### 全体のデータから「入場料金」が800円より安いデータだけを抽出する curlコマンド例
```
$ curl -v -X GET "http://CADDE.Y.co.jp:888/cadde/api/v4/entities"
　　-H "x-cadde-resource-url: https://closed.XX.go.jo/v2/entities?type=Event_2021&q=fee<800" 
　　-H “x-cadde-resource-api-type:api/ngsi”
　　-H "x-cadde-provider: provider1@dataex.jp" 
　　-H "Authorization: Bearer XXXX“
　　-H “x-cadde-options: Fiware-Service: shinnihon, Fiware-ServicePath: /event” 
```
