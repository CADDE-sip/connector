# 本ドキュメントについて
本ドキュメントについて：<br>
  本ドキュメントは、コネクタの実装方法/利用方法についてのガイドラインです。<br>
  したがって、分野間データ連携基盤(CADDE)やコネクタの基本事項についての説明は割愛しています。<br>
  コネクタについてのご質問、ご不明点、ご指摘事項、利用時の不具合、などがありましたら、以下にご連絡ください。<br>
  ※CADDEは情報・システム研究機構（国立情報学研究所）が商標登録出願中です。<br>
<br>
[問い合わせ先](#問い合わせ先)

# 分野間データ連携基盤: コネクタ

## システム全体構成図
分野間データ連携基盤全体のシステム構成を下記に示します。
![Alt text](doc/png/system.png?raw=true "Title")


## 前提条件
コネクタの前提条件を示します。

  - コネクタは、カタログ検索、データ交換、認証、認可、来歴、契約の機能を具備します。認可、契約を利用する場合の詳細な設定方法は、別途お問い合わせください。
  - 利用者側システム(WebApp)、提供者側の CKAN カタログサイト、データ提供用のデータ管理(FTP サーバ,NGSI サーバ,HTTP サーバ)は、コネクタ設置前に事前に準備されていることを前提とします。
  - 利用者システム(WebApp)-利用者コネクタ間および、利用者コネクタ、提供者コネクタ間の通信路のセキュリティ（TLS 認証、IDS、IPS、ファイアウォール等)においては、OSS ソフトウェア、アプライアンス装置を用いて、コネクタ外で、利用者および提供者が準備するものとします。
  - CADDEユーザIDは、コネクタ外で事前に採番されていることを前提とします。※CADDEユーザIDは、本READEME上では、利用者ID、提供者IDと記載しています。
  
- Linux 上での動作を前提とします。

  - Docker、Docker Compose が事前インストールされていることを前提とします。
  - 対応する Docker Version は以下の通り。
    - Docker 20.10.1
  - 対応する OS は、Linux の上記 Docker がサポートする OS 。

- 提供データサイズ: サポートするデータサイズは以下とします。
  - コンテキスト情報：１ MB 以下
  - ファイル：100MB 以下


<br><br>

# 利用者コネクタ
## 利用者コネクタ環境準備
[分野間データ連携基盤: TLS相互認証設定例 利用者環境プロキシ設定](doc/TSLManual.md "利用者環境プロキシ設定") 参照。

## 利用者コネクタ構築手順

1. 利用者コネクタ取得

```
git clone https://(ユーザID)@github.com/CADDE-sip/connector
cd connector
```

2. 共通ファイルの展開 <br>
setup.sh実行
```
cd src/consumer/
sh setup.sh
```

3. コンフィグファイルの設定
- location.json
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置<br>提供者側に接続を行う際に指定する提供者側のアドレス設定を記載<br>
  <br>個別にデータ提供者接続先情報を追加する場合は、利用者コネクタ内のlocation.jsonを編集してください。<br>

  | 設定パラメータ                     | 概要                                                                           |
  | :--------------------------------- | :----------------------------------------------------------------------------- |
  | connector_location                 | 以下の提供者 ID を保持                                                         |
  | 提供者 ID                          | 提供者 ID を記載する 以下のパラメータを保持<br>provider_connector_url          |
  | provider_connector_url             | 提供者コネクタのアクセスURL                                                    |

- connector.json
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置
  <br>認証サーバに登録した利用者コネクタのIDとシークレットを記載<br>

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | consumer_connector_id              | 認証サーバに設定した利用者コネクタのID                          |
  | consumer_connector_secret          | 認証サーバが発行した利用者コネクタのシークレット                |
  | location_service_url               | ロケーションサービスのアクセスURL                               |
  | trace_log_enable                   | トレース用ログ出力有無                                          |

- ngsi.json
  <br>利用者コネクタから提供者コネクタを介さずNGSIサーバに直接アクセスする場合の利用者ID、アクセストークンを設定
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置
  <br>NGSI の情報を取得する際に利用するアクセストークンの設定を記載<br>

  | 設定パラメータ                     | 概要                                                                           |
  | :--------------------------------- | :----------------------------------------------------------------------------- |
  | ngsi_auth                          | 以下、ドメイン毎の設定を配列で保持                                             |
  | domain                             | ドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載         |
  | auth                               | NGSI へ API アクセスするためのアクセストークンを設定                           |

- public_ckan.json
  <br>connector/src/consumer/catalog-search/swagger_server/configs/に配置<br>CKAN の横断検索時の接続先の設定を記載

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | public_ckan_url                    | 横断検索時の横断検索サーバのURLを記載                           |

- provenance.json
  <br>connector/src/consumer/provenance-management/swagger_server/configs/に配置
  <br>来歴管理サーバのURLの設定を記載
  <br>※来歴の検索時に使用する
  <br>※来歴管理を行う場合は認証認可が必須のためconnector.jsonの設定も必要となる
  <br>※データ取得時は提供者側の来歴管理サーバのアクセスURL宛に履歴登録を行うため、本設定は使用しない

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | provenance_management_api_url      | 来歴管理サーバのアクセスURL                                     | 


## 利用者コネクタ起動手順
1. 利用者コネクタ起動

```
cd connector/src/consumer
docker compose -p consumer up -d
```

2. 利用者コネクタ起動確認
StateがすべてUpとなっていることを確認
```
docker compose ps
NAME                             COMMAND                  SERVICE                          STATUS              PORTS
consumer_authentication          "python3 -m swagger_…"   consumer-authentication          running             8080/tcp
consumer_catalog_search          "python3 -m swagger_…"   consumer-catalog-search          running             8080/tcp
consumer_connector_main          "python3 -m swagger_…"   consumer-connector-main          running             8080/tcp
consumer_data_exchange           "python3 -m swagger_…"   consumer-data-exchange           running             8080/tcp
consumer_provenance_management   "python3 -m swagger_…"   consumer-provenance-management   running             8080/tcp
forward-proxy                    "/usr/sbin/squid '-N…"   squid                            running             3128/tcp
reverse-proxy                    "/docker-entrypoint.…"   reverse-proxy                    running             0.0.0.0:80->80/tcp, :::8080->80/tcp
```
## 利用者コネクタ停止手順
```
docker compose -p consumer down
```

## 利用者コネクタ利用ガイド
利用者コネクタの利用方法については下記参照。<br>
[利用者コネクタ利用ガイド](doc/ConsumerManual.md "利用者コネクタ利用ガイド")

### 利用者コネクタAPI
利用者コネクタのREST-API詳細仕様は、下記からDownloadし参照してください。<br>
[RESTAPI仕様書格納先](doc/api/) 参照
- 利用者_カタログ検索IF.html
- 利用者_コネクタメイン.html
- 利用者_データ交換IF(CADDE).html
- 利用者_認証認可IF.html
- 利用者_来歴管理IF.html

### コネクタを利用した NGSIデータの取得方法
[CADDEコネクタを利用した NGSIデータの取得方法](doc/README_NGSI.md) 参照

### リバースプロキシを使用しない場合
docker-compose.ymlのリバースプロキシコンテナを利用しない場合は、reverse-proxyコンテナをコメントアウトし、
consumer-connector-mainにポートフォワードの指定をしてください。

### フォワードプロキシを使用しない場合
docker-compose.ymlのフォワードプロキシコンテナを利用しない場合は、squidコンテナをコメントアウトしてください。

### 利用者コネクタへのアクセス制限について
利用者コネクタへアクセス制限を行う場合は、利用者コネクタにSSL/TSL認証でアクセス制限をかけてください。
[分野間データ連携基盤: TLS相互認証設定例 提供者環境リバースプロキシ設定](doc/TSLManual.md "利用者環境および提供者環境リバースプロキシ設定")  参照。

<br>
<br>

# 提供者コネクタ

## 提供者コネクタ環境準備
[分野間データ連携基盤: TLS相互認証設定例 提供者環境リバースプロキシ設定](doc/TSLManual.md "利用者環境および提供者環境リバースプロキシ設定")  参照。

[提供者環境構築ガイド](doc/ProviderManual.md "提供者環境構築ガイド")

### 提供者コネクタ構築手順
1. 提供者コネクタの取得
```
git clone https://(ユーザID)@github.com/CADDE-sip/connector
cd connector
```

2. setup.sh実行
```
cd src/provider/
sh setup.sh
```

3. コンフィグファイルの設定<br>

(1) CKANサーバを提供者コネクタ経由で詳細検索および公開する場合
- provider_ckan.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>CKANの接続先の設定を記載

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | release_ckan_url                   | カタログサイト(公開)のアクセスURL                               |
  | detail_ckan_url                    | カタログサイト(詳細)のアクセスURL                               |
  | authorization                      | カタログサイト(詳細)アクセス時に認可確認を行うか否かを設定      |
  | packages_search_for_data_exchange  | データ取得時に交換実績記録用リソースID検索を行うか否かを設定    |



(2) データ管理サーバ(HTTPサーバ)を提供者コネクタ経由で公開する場合<br>
(2-1) 認証ありHTTPサーバに接続の場合
- http.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>http 接続でファイル取得する際に basic 認証が必要なドメインの設定を記載<br>

  | 設定パラメータ                     | 概要                                                                                                                                                   |
  | :--------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
  | basic_auth                         | 以下、ドメイン毎の設定を配列で保持                                                                                                                     |
  | domain                             | basic 認証が必要なドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載                                                               |
  | basic_id                           | 対象ドメインへのファイル取得 http 接続時のベーシック認証 ID を設定                                                                                     |
  | basic_pass                         | 対象ドメインへのファイル取得 http 接続時のベーシック認証パスワードを設定                                                                               |
  | authorization                      | リソースの認可確認設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当するリソースの認可確認設定が存在しない場合、認可確認有無はTrueで動作する |
  | url                                | 認可確認有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、認可確認設定を適用                 |
  | enable                             | 認可確認有無 (認可確認を行う場合True, 認可確認を行わない場合Falseを設定)                                                                               |
  | contract_management_service        | 取引市場利用設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する取引市場利用設定が存在しない場合、取引市場利用有無はTrueで動作する         |
  | url                                | 取引市場利用有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、取引市場利用設定を適用         |
  | enable                             | 取引市場利用有無 (取引市場を利用する場合True,取引市場を利用しない場合Falseを設定)                                                                      |
  | register_provenance                | 来歴登録設定情報 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する来歴登録設定情報が存在しない場合、来歴登録設定情報はTrueで動作する         |
  | url                                | 来歴登録設定情報の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、来歴登録設定情報を適用         |
  | enable                             | 来歴登録設定情報 (来歴登録を利用する場合True,来歴登録設定を利用しない場合Falseを設定)                                                                  |

(2-2) 認証なしHTTPサーバに接続の場合<br>
 http.jsonファイルのbasic_auth編集不要。
  
(3) データ管理サーバ(FTPサーバ)を提供者コネクタ経由で公開する場合
(3-1) anonymous/anonymous以外をID/パスワードとするFTPサーバに接続の場合
- ftp.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>ftp 接続時の設定を記載<br>

  | 設定パラメータ                     | 概要                                                                                                                                                   |
  | :--------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
  | ftp_auth                           | 以下、ドメイン毎の設定を配列で保持                                                                                                                     |
  | domain                             | basic 認証が必要なドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載                                                               |
  | ftp_id                             | ftp 接続時の ID を設定                                                                                                                                 |
  | ftp_pass                           | ftp 接続時のパスワードを設定                                                                                                                           |
  | authorization                      | リソースの認可確認設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当するリソースの認可確認設定が存在しない場合、認可確認有無はTrueで動作する |
  | url                                | 認可確認有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、認可確認設定を適用                 |
  | enable                             | 認可確認有無 (認可確認を行う場合True, 認可確認を行わない場合Falseを設定)                                                                               |
  | contract_management_service        | 取引市場利用設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する取引市場利用設定が存在しない場合、取引市場利用有無はTrueで動作する         |
  | url                                | 取引市場利用有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、取引市場利用設定を適用         |
  | enable                             | 取引市場利用有無 (取引市場を利用する場合True,取引市場を利用しない場合Falseを設定)                                                                      |
  | register_provenance                | 来歴登録設定情報 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する来歴登録設定情報が存在しない場合、来歴登録設定情報はTrueで動作する         |
  | url                                | 来歴登録設定情報の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、来歴登録設定情報を適用         |
  | enable                             | 来歴登録設定情報 (来歴登録を利用する場合True,来歴登録設定を利用しない場合Falseを設定)                                                                      |

(3-2) anonymous/anonymousをID/パスワードとするFTPサーバに接続の場合
 ftp.jsonファイルのftp_auth編集不要。

(4) データ管理サーバ(NGSIサーバ)を提供者コネクタ経由で公開する場合
- ngsi.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>NGSI の情報を取得する際に利用するアクセストークンの設定を記載<br>

  | 設定パラメータ                     | 概要                                                                                                                                                                                              |
  | :--------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
  | ngsi_auth                          | 以下、ドメイン毎の設定を配列で保持                                                                                                                                                                |
  | domain                             | ドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載                                                                                                                            |
  | auth                               | NGSI へ API アクセスするためのアクセストークンを設定                                                                                                                                              |
  | authorization                      | リソースの認可確認設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当するリソースの認可確認設定が存在しない場合、認可確認有無はTrueで動作する                                            |
  | url                                | 認可確認有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、認可確認設定を適用                                                            |
  | tenant                             | 認可確認有無の対象となるNGSIテナント（カタログ項目：NGSIテナント）を記載する データ取得時に指定されたNGSIテナントと本設定のNGSIテナントが一致した場合、認可確認設定を適用                         |
  | servicepath                        | 認可確認有無の対象となるNGSIサービスパス（カタログ項目：NGSIサービスパス）を記載する データ取得時に指定されたNGSIサービスパスと本設定のNGSIサービスパスが一致した場合、認可確認設定を適用         |
  | enable                             | 認可確認有無 (認可確認を行う場合True, 認可確認を行わない場合Falseを設定)                                                                                                                          |
  | contract_management_service        | 取引市場利用設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する取引市場利用設定が存在しない場合、取引市場利用有無はTrueで動作する                                                    |
  | url                                | 取引市場利用有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、取引市場利用設定を適用                                                    |
  | tenant                             | 取引市場利用有無の対象となるNGSIテナント（カタログ項目：NGSIテナント）を記載する データ取得時に指定されたNGSIテナントと本設定のNGSIテナントが一致した場合、取引市場利用設定を適用                 |
  | servicepath                        | 取引市場利用有無の対象となるNGSIサービスパス（カタログ項目：NGSIサービスパス）を記載する データ取得時に指定されたNGSIサービスパスと本設定のNGSIサービスパスが一致した場合、取引市場利用設定を適用 |
  | enable                             | 取引市場利用有無 (取引市場を利用する場合True,取引市場を利用しない場合Falseを設定)                                                                                                                         |
  | register_provenance                | 来歴登録設定情報 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する来歴登録設定情報が存在しない場合、来歴登録設定情報はTrueで動作する                                                    |
  | url                                | 来歴登録設定情報の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、来歴登録設定情報を適用                                                    |
  | tenant                             | 来歴登録設定情報の対象となるNGSIテナント（カタログ項目：NGSIテナント）を記載する データ取得時に指定されたNGSIテナントと本設定のNGSIテナントが一致した場合、来歴登録設定を適用                     |
  | servicepath                        | 来歴登録設定情報の対象となるNGSIサービスパス（カタログ項目：NGSIサービスパス）を記載する データ取得時に指定されたNGSIサービスパスと本設定のNGSIサービスパスが一致した場合、来歴登録設定を適用     |
  | enable                             | 来歴登録設定情報 (来歴登録を利用する場合True,来歴登録設定を利用しない場合Falseを設定)                                                                                                             |

(5) 認証および認可をおこなう場合
- authorization.json
  <br>connector/src/provider/authorization/swagger_server/configs/に配置<br>認証および認可時の接続先を記載

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | authorization_server_url           | 認可サーバのアクセスURL                                         |

- connector.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>認可サーバに登録した提供者コネクタのIDとシークレットを記載<br>

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | provider_id                        | 来歴管理登録するときに提供者を特定するためのID                  |
  | provider_connector_id              | 認可サーバに設定した提供者コネクタのID                          |
  | provider_connector_secret          | 認可サーバが発行した提供者コネクタのシークレット                |
  | trace_log_enable                   | トレース用ログ出力有無                                          |

(6) 来歴管理をおこなう場合
- provenance.json
  <br>connector/src/provider/provenance-management/swagger_server/configs/に配置
  <br>来歴管理サーバのURLの設定を記載
  <br>※来歴管理を行う場合は認証認可が必須のため(5)の設定も必要となる
  <br>※データ取得時は提供者側の来歴管理サーバのアクセスURLを利用者側に返却する

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | provenance_management_api_url      | 来歴管理サーバのアクセスURL                                     | 

### 提供者コネクタ起動手順 
```
cd connector/src/provider/
docker compose -p provider up -d
```

### 提供者コネクタ起動確認
StateがすべてUpとなっていることを確認
```
docker compose -p provider ps
NAME                             COMMAND                  SERVICE                          STATUS              PORTS
provider_authorization           "python3 -m swagger_…"   provider-authorization           running             8080/tcp
provider_catalog_search          "python3 -m swagger_…"   provider-catalog-search          running             8080/tcp
provider_connector_main          "python3 -m swagger_…"   provider-connector-main          running             8080/tcp
provider_data_exchange           "python3 -m swagger_…"   provider-data-exchange           running             8080/tcp
provider_provenance_management   "python3 -m swagger_…"   provider-provenance-management   running             8080/tcp
reverse-proxy                    "/docker-entrypoint.…"   reverse-proxy                    running             0.0.0.0:443->443/tcp, :::443->443/tcp
```

### 提供者コネクタ動作確認
提供者コネクタの外部API経由で、データ管理サーバ(HTTP or FTP or NGSI)からデータを取得できることを確認。<br>
{リソースURL}には、詳細検索用CKAN登録済みで提供者コネクタからアクセス可能なデータ管理サーバのデータアクセス先を指定
- 例1: `ftp://192.168.0.1/xxx.pdf`
- 例2: `http://192.168.0.1/auth/xxx.csv`

(1) データ管理サーバ(HTTPサーバ)を提供者コネクタAPI経由で取得する場合
```
curl {提供者コネクタIPアドレス}/cadde/api/v4/file -H "x-cadde-resource-url:{リソースURL}" -H "x-cadde-resource-api-type:file/http" -O
```

(2) データ管理サーバ(FTPサーバ)を提供者コネクタAPI経由で取得する場合
```
curl {提供者コネクタIPアドレス}/cadde/api/v4/file -H "x-cadde-resource-url:{リソースURL}" -H "x-cadde-resource-api-type:file/ftp" -O
```

(3) データ管理サーバ(NGSIサーバ)を提供者コネクタ経由で公開する場合
別紙参照

### 提供者コネクタ停止手順 
```
docker compose -p provider down
```

### 提供者コネクタAPI
提供者コネクタのREST-API詳細仕様は、下記からDownloadし参照してください。<br>
[RESTAPI仕様書格納先](doc/api/) 参照
- 提供者_カタログ検索IF.html
- 提供者_コネクタメイン.html
- 提供者_データ交換IF(CADDE).html
- 提供者_認証認可IF.html
- 提供者_来歴管理IF.html

## LICENSE
[MIT](./LICENSE.md)

## 問い合わせ先
お問い合わせ時には、下記必要項目を記載の上、問い合わせ窓口宛にご連絡ください。<br>
問い合わせ窓口：sip2cadde_support＠nii.ac.jp <br><br>
*********<br>
①分類：選択[資材関連(GitHubからのダウンロード等)/構築関連(コネクタ構築中)/各種仕様確認/その他] <br>
②連絡先 <br>
③問い合わせ内容 <br>
④対応希望日 <br>
⑤事象発生日 <br>
⑥利用環境(OS/CPU/メモリ/コネクタバージョン/コネクタ種別(利用者or提供者))  <br>
⑦動作不良のAPIやエラーコード等 <br>
⑧添付資料：画面キャプチャやログ等 <br>
⑨関連する過去の問い合わせ番号 <br>
**********<br><br>
⑤～⑨について、構築中の不具合や動作不良に関する問い合わせの場合、可能な範囲でご記載ください。<br>


