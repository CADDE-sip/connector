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
  - 利用者システム(WebApp)―利用者コネクタ間および、利用者コネクタ―提供者コネクタ間の通信路のセキュリティ（TLS 認証、IDS、IPS、ファイアウォール等)においては、OSS ソフトウェア、アプライアンス装置を用いて、コネクタ外で、利用者および提供者が準備するものとします。
  - CADDEユーザID、コネクタのID・シークレットは、コネクタ外で事前に採番されていることを前提とします。※CADDEユーザIDは、本READEME上では、CADDEユーザID(利用者)、CADDEユーザID(提供者)と記載しています。
  
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
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置<br>

  提供者側に接続を行う際に指定する提供者側のアドレス設定を記載してください。<br>
  個別にデータ提供者接続先情報を追加する場合は、利用者コネクタ内のlocation.jsonを編集してください。<br>

  | 設定パラメータ                     | 概要                                                                              |
  | :--------------------------------- | :-------------------------------------------------------------------------------- |
  | connector_location                 | 以下の提供者 ID を保持                                                            |
  | CADDEユーザID(提供者)              | CADDEユーザID(提供者) を記載する 以下のパラメータを保持<br>provider_connector_url |
  | provider_connector_url             | 提供者コネクタのアクセスURL                                                       |

- connector.json
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置<br>

  認証サーバに登録した利用者コネクタのIDとシークレットを記載してください。<br>

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | consumer_connector_id              | 認証サーバに設定した利用者コネクタのID                          |
  | consumer_connector_secret          | 認証サーバが発行した利用者コネクタのシークレット                |
  | location_service_url               | ロケーションサービスのアクセスURL                               |
  | trace_log_enable                   | コネクタの詳細ログ出力有無<br>出力無の設定でも基本的な動作ログは出力されます |

- ngsi.json
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置<br>

  利用者コネクタから提供者コネクタを介さずNGSIサーバに直接アクセスする場合のCADDEユーザID(利用者)、アクセストークンを設定します。<br>
  NGSI の情報を取得する際に利用するアクセストークンの設定を記載してください。<br>

  | 設定パラメータ                     | 概要                                                                           |
  | :--------------------------------- | :----------------------------------------------------------------------------- |
  | ngsi_auth                          | 以下、ドメイン毎の設定を配列で保持                                             |
  | domain                             | ドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載         |
  | auth                               | NGSI へ API アクセスするためのアクセストークンを設定                           |

- public_ckan.json
  <br>connector/src/consumer/catalog-search/swagger_server/configs/に配置<br>

  利用者コネクタから横断検索を行う際に使用します。<br>
  横断検索サイトの接続先の設定を記載してください。<br>

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | public_ckan_url                    | 横断検索時の横断検索サーバのURLを記載                           |

4. フォワードプロキシの設定
<br>提供者コネクタがアクセス制限を行っている場合は、下記を参考に利用者コネクタのフォワードプロキシにSSL/TLS設定を行います。
<br>[分野間データ連携基盤: TLS相互認証設定例 フォワードプロキシ(Squid)構築手順](doc/TLSManual.md "利用者環境プロキシ") 参照。<br>
※フォワードプロシキを使用しない場合、本設定は不要です。<br>

5. リバースプロキシの設定
<br>利用者コネクタへアクセス制限を行う場合は、下記を参考に利用者コネクタのリバースプロキシにSSL/TLS設定を行います。
<br>[分野間データ連携基盤: TLS相互認証設定例 リバースプロキシ(nginx)構築手順](doc/TLSManual.md "利用者環境プロキシ") 参照。<br>
※利用者コネクタへアクセス制限を行わず、リバースプロシキを使用しない場合、本設定は不要です。<br>

## 利用者コネクタ起動手順

1. 利用者コネクタ起動

```
cd connector/src/consumer
sh start.sh
```

起動した利用者コネクタの構成は以下となります。<br>
![Alt text](doc/png/consumer.png?raw=true "利用者コネクタ構成図")

2. 利用者コネクタ起動確認
<br>
コネクタ起動時にStateがすべてUpとなっていることを確認してください。<br>

```
NAME                             COMMAND                  SERVICE                          STATUS              PORTS
consumer_authentication          "python3 -m swagger_…"   consumer-authentication          running             8080/tcp
consumer_catalog_search          "python3 -m swagger_…"   consumer-catalog-search          running             8080/tcp
consumer_connector_main          "python3 -m swagger_…"   consumer-connector-main          running             8080/tcp
consumer_data_exchange           "python3 -m swagger_…"   consumer-data-exchange           running             8080/tcp
consumer_provenance_management   "python3 -m swagger_…"   consumer-provenance-management   running             8080/tcp
forward-proxy                    "/usr/sbin/squid '-N…"   squid                            running             3128/tcp
reverse-proxy                    "/docker-entrypoint.…"   reverse-proxy                    running             0.0.0.0:80->80/tcp, :::8080->80/tcp
```

### プロキシを使用しない場合
<br>プロキシコンテナを利用しない場合は、コネクタ起動時にパラメータを指定します。<br>

#### リバースプロキシ、フォワードプロキシを使用しない場合
<br>リバースプロキシおよびフォワードプロキシを使用しない場合、以下のコマンドで利用者コネクタを起動してください。<br>
```
sh start.sh noproxy
```

<br>起動した際に、リバースプロキシおよびフォワードプロキシが起動していないことを確認してください。<br>
リバースプロキシを起動しない場合、コネクタメインが80番ポートで起動します。<br>
```
NAME                             COMMAND                  SERVICE                          STATUS              PORTS
consumer_authentication          "python3 -m swagger_…"   consumer-authentication          running             8080/tcp
consumer_catalog_search          "python3 -m swagger_…"   consumer-catalog-search          running             8080/tcp
consumer_connector_main          "python3 -m swagger_…"   consumer-connector-main          running             0.0.0.0:80->8080/tcp, :::80->8080/tcp
consumer_data_exchange           "python3 -m swagger_…"   consumer-data-exchange           running             8080/tcp
consumer_provenance_management   "python3 -m swagger_…"   consumer-provenance-management   running             8080/tcp
```

#### リバースプロキシを使用しない場合
<br>リバースプロキシのみ使用しない場合、以下のコマンドで利用者コネクタを起動してください。<br>
```
sh start.sh noreverseproxy
```
<br>起動した際に、リバースプロキシが起動していないことを確認してください。<br>
リバースプロキシを起動しない場合、コネクタメインが80番ポートで起動します。<br>
```
NAME                             COMMAND                  SERVICE                          STATUS              PORTS
consumer_authentication          "python3 -m swagger_…"   consumer-authentication          running             8080/tcp
consumer_catalog_search          "python3 -m swagger_…"   consumer-catalog-search          running             8080/tcp
consumer_connector_main          "python3 -m swagger_…"   consumer-connector-main          running             0.0.0.0:80->8080/tcp, :::80->8080/tcp
consumer_data_exchange           "python3 -m swagger_…"   consumer-data-exchange           running             8080/tcp
consumer_provenance_management   "python3 -m swagger_…"   consumer-provenance-management   running             8080/tcp
forward-proxy                    "/usr/sbin/squid '-N…"   squid                            running             3128/tcp
```

#### フォワードプロキシを使用しない場合
<br>フォワードプロキシのみ使用しない場合、以下のコマンドで利用者コネクタを起動してください。
```
sh start.sh noforwardproxy
```

<br>起動した際に、フォワードプロキシが起動していないことを確認してください。<br>
```
NAME                             COMMAND                  SERVICE                          STATUS              PORTS
consumer_authentication          "python3 -m swagger_…"   consumer-authentication          running             8080/tcp
consumer_catalog_search          "python3 -m swagger_…"   consumer-catalog-search          running             8080/tcp
consumer_connector_main          "python3 -m swagger_…"   consumer-connector-main          running             8080/tcp
consumer_data_exchange           "python3 -m swagger_…"   consumer-data-exchange           running             8080/tcp
consumer_provenance_management   "python3 -m swagger_…"   consumer-provenance-management   running             8080/tcp
reverse-proxy                    "/docker-entrypoint.…"   reverse-proxy                    running             0.0.0.0:80->80/tcp, :::8080->80/tcp
```

## 利用者コネクタ停止手順
```
sh stop.sh
```

## 利用者コネクタ利用ガイド
<br>利用者コネクタの利用方法については下記参照。<br>
[利用者コネクタ利用ガイド](doc/ConsumerManual.md "利用者コネクタ利用ガイド")

### 利用者コネクタAPI
<br>利用者コネクタのREST-API詳細仕様は、下記からダウンロードし参照してください。<br>
[RESTAPI仕様書格納先](doc/api/) 参照
- 利用者_カタログ検索IF.html
- 利用者_コネクタメイン.html
- 利用者_データ交換IF(CADDE).html
- 利用者_認証認可IF.html
- 利用者_来歴管理IF.html

### コネクタを利用した NGSIデータの取得方法
<br>[CADDEコネクタを利用した NGSIデータの取得方法](doc/README_NGSI.md) 参照 <br>


<br>
<br>

# 提供者コネクタ

## 提供者コネクタ環境準備
[提供者環境構築ガイド](doc/ProviderManual.md "提供者環境構築ガイド")

## 提供者コネクタ構築手順
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
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>
  CKANの接続先の設定を記載します。<br>

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | release_ckan_url                   | カタログサイト(公開)のアクセスURL                               |
  | detail_ckan_url                    | カタログサイト(詳細)のアクセスURL                               |
  | authorization                      | カタログサイト(詳細)アクセス時に認可確認を行うか否かを設定      |
  | packages_search_for_data_exchange  | データ取得時に交換実績記録用リソースID検索を行うか否かを設定<br>※来歴を使用せず、かつ、カタログ無しの状態でデータの提供を行いたい場合は、リソースID検索を行わない設定（false）にする |


(2) データ管理サーバ(HTTPサーバ)を提供者コネクタ経由で公開する場合<br>
(2-1) 認証ありHTTPサーバに接続の場合
- http.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>
  http 接続でファイル取得する際に basic 認証が必要なドメインの設定を記載します。<br>

  | 設定パラメータ                     | 概要                                                                                                                                                   |
  | :--------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
  | basic_auth                         | 以下、ドメイン毎の設定を配列で保持                                                                                                                     |
  | domain                             | basic 認証が必要なドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載                                                               |
  | basic_id                           | 対象ドメインへのファイル取得 http 接続時のベーシック認証 ID を設定                                                                                     |
  | basic_pass                         | 対象ドメインへのファイル取得 http 接続時のベーシック認証パスワードを設定                                                                               |
  | authorization                      | リソースの認可確認設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当するリソースの認可確認設定が存在しない場合、認可確認有無はTrueで動作する |
  | authorization/url                  | 認可確認有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、認可確認設定を適用                 |
  | authorization/enable               | 認可確認有無 (認可確認を行う場合True, 認可確認を行わない場合Falseを設定)                                                                               |
  | contract_management_service        | 取引市場利用設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する取引市場利用設定が存在しない場合、取引市場利用有無はTrueで動作する         |
  | contract_management_service/url    | 取引市場利用有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、取引市場利用設定を適用         |
  | contract_management_service/enable | 取引市場利用有無 (取引市場を利用する場合True,取引市場を利用しない場合Falseを設定)                                                                      |
  | register_provenance                | 来歴登録設定情報 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する来歴登録設定情報が存在しない場合、来歴登録設定情報はTrueで動作する         |
  | register_provenance/url            | 来歴登録設定情報の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、来歴登録設定情報を適用         |
  | register_provenance/enable         | 来歴登録設定情報 (来歴登録を利用する場合True,来歴登録設定を利用しない場合Falseを設定)                                                                  |

  ※urlの最大文字数は255バイト

(2-2) 認証なしHTTPサーバに接続の場合<br>
 http.jsonファイルのbasic_authは編集不要です。
  
(3) データ管理サーバ(FTPサーバ)を提供者コネクタ経由で公開する場合<br>
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
  | authorization/url                  | 認可確認有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、認可確認設定を適用                 |
  | authorization/enable               | 認可確認有無 (認可確認を行う場合True, 認可確認を行わない場合Falseを設定)                                                                               |
  | contract_management_service        | 取引市場利用設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する取引市場利用設定が存在しない場合、取引市場利用有無はTrueで動作する         |
  | contract_management_service/url    | 取引市場利用有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、取引市場利用設定を適用         |
  | contract_management_service/enable | 取引市場利用有無 (取引市場を利用する場合True,取引市場を利用しない場合Falseを設定)                                                                      |
  | register_provenance                | 来歴登録設定情報 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する来歴登録設定情報が存在しない場合、来歴登録設定情報はTrueで動作する         |
  | register_provenance/url            | 来歴登録設定情報の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、来歴登録設定情報を適用         |
  | register_provenance/enable         | 来歴登録設定情報 (来歴登録を利用する場合True,来歴登録設定を利用しない場合Falseを設定)                                                                      |

  ※urlの最大文字数は255バイト

(3-2) anonymous/anonymousをID/パスワードとするFTPサーバに接続の場合
 <br>ftp.jsonファイルのftp_authは編集不要です。

(4) データ管理サーバ(NGSIサーバ)を提供者コネクタ経由で公開する場合
- ngsi.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>NGSI の情報を取得する際に利用するアクセストークンの設定を記載します。<br>

  | 設定パラメータ                          | 概要                                                                                                                                                                                              |
  | :-------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
  | ngsi_auth                               | 以下、ドメイン毎の設定を配列で保持                                                                                                                                                                |
  | domain                                  | ドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載                                                                                                                            |
  | auth                                    | NGSI へ API アクセスするためのアクセストークンを設定                                                                                                                                              |
  | authorization                           | リソースの認可確認設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当するリソースの認可確認設定が存在しない場合、認可確認有無はTrueで動作する                                            |
  | authorization/url                       | 認可確認有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、認可確認設定を適用                                                            |
  | authorization/tenant                    | 認可確認有無の対象となるNGSIテナント（カタログ項目：NGSIテナント）を記載する データ取得時に指定されたNGSIテナントと本設定のNGSIテナントが一致した場合、認可確認設定を適用                         |
  | authorization/servicepath               | 認可確認有無の対象となるNGSIサービスパス（カタログ項目：NGSIサービスパス）を記載する データ取得時に指定されたNGSIサービスパスと本設定のNGSIサービスパスが一致した場合、認可確認設定を適用         |
  | authorization/enable                    | 認可確認有無 (認可確認を行う場合True, 認可確認を行わない場合Falseを設定)                                                                                                                          |
  | contract_management_service             | 取引市場利用設定 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する取引市場利用設定が存在しない場合、取引市場利用有無はTrueで動作する                                                    |
  | contract_management_service/url         | 取引市場利用有無の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、取引市場利用設定を適用                                                    |
  | contract_management_service/tenant      | 取引市場利用有無の対象となるNGSIテナント（カタログ項目：NGSIテナント）を記載する データ取得時に指定されたNGSIテナントと本設定のNGSIテナントが一致した場合、取引市場利用設定を適用                 |
  | contract_management_service/servicepath | 取引市場利用有無の対象となるNGSIサービスパス（カタログ項目：NGSIサービスパス）を記載する データ取得時に指定されたNGSIサービスパスと本設定のNGSIサービスパスが一致した場合、取引市場利用設定を適用 |
  | contract_management_service/enable      | 取引市場利用有無 (取引市場を利用する場合True,取引市場を利用しない場合Falseを設定)                                                                                                                         |
  | register_provenance                     | 来歴登録設定情報 以下、URLごとの設定を配列で保持<br>※データ取得時に該当する来歴登録設定情報が存在しない場合、来歴登録設定情報はTrueで動作する                                                    |
  | register_provenance/url                 | 来歴登録設定情報の対象となるリソースのURLを記載する データ取得時に指定されたリソースURLに設定上のURLが含まれていた場合、来歴登録設定情報を適用                                                    |
  | register_provenance/tenant              | 来歴登録設定情報の対象となるNGSIテナント（カタログ項目：NGSIテナント）を記載する データ取得時に指定されたNGSIテナントと本設定のNGSIテナントが一致した場合、来歴登録設定を適用                     |
  | register_provenance/servicepath         | 来歴登録設定情報の対象となるNGSIサービスパス（カタログ項目：NGSIサービスパス）を記載する データ取得時に指定されたNGSIサービスパスと本設定のNGSIサービスパスが一致した場合、来歴登録設定を適用     |
  | register_provenance/enable              | 来歴登録設定情報 (来歴登録を利用する場合True,来歴登録設定を利用しない場合Falseを設定)                                                                                                             |

  ※urlの最大文字数は255バイト

(5) 認証および認可をおこなう場合
- authorization.json
  <br>connector/src/provider/authorization/swagger_server/configs/に配置<br>
  認証および認可時の接続先を記載してください。<br>

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | authorization_server_url           | 認可サーバのアクセスURL                                         |

- connector.json
  connector/src/provider/connector-main/swagger_server/configs/に配置<br>
  認可サーバに登録した提供者コネクタのIDとシークレットを記載してください。<br>

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | provider_id                        | CADDEユーザID(提供者)                                           |
  | provider_connector_id              | 認可サーバに設定した提供者コネクタのID                          |
  | provider_connector_secret          | 認可サーバが発行した提供者コネクタのシークレット                |
  | trace_log_enable                   | コネクタの詳細ログ出力有無<br>出力無の設定でも基本的な動作ログは出力されます |

(6) 来歴管理をおこなう場合
- provenance.json
  <br>connector/src/provider/provenance-management/swagger_server/configs/に配置
  <br>来歴管理サーバのURLの設定を記載
  <br>※データ取得時に、カタログに来歴のID(交換実績記録用リソースID)が登録されていた場合、来歴管理サーバに対する受信履歴登録時に使用します。
  <br>※来歴管理を行う場合は認証が必須となります。
  <br>※データ取得時は提供者側の来歴管理サーバのアクセスURLを利用者側に返却し、利用者側は受け取った来歴管理サーバのアクセスURLに対し受信履歴登録を行います。

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | provenance_management_api_url      | 来歴管理サーバのアクセスURL                                     |

(6-1) 来歴を行う場合のCKAN設定
<br>来歴を記録する場合、カタログにある来歴のID(交換実績記録用リソースID)を取得する必要があるため、provider_ckan.jsonのpackages_search_for_data_exchangeをtrueに設定します。
- provider_ckan.json
```
{
    "release_ckan_url" : "https://example.com",
    "detail_ckan_url" : "https://example.com",
    "authorization" : true,
    "packages_search_for_data_exchange" : true
}
```

(6-2) 来歴を行う場合のデータ管理サーバ設定
<br>データ取得の対象となるリソースURLが来歴を記録するようにregister_provenanceのenableをtrueにします。<br>
- http.json、ftp.json
```
    "register_provenance": [
        {
            "url": "{リソースURLに含まれるURL文字列}",
            "enable" : true
        }
    ]
```
- ngsi.json
```
    "register_provenance": [
        {
            "url": "{リソースURLに含まれるURL文字列}",
            "tenant": "{NGSIテナント}",
            "servicepath": "{NGSIサービスパス}",
            "enable" : true
        }
    ]
```

4. リバースプロキシの設定
<br>[分野間データ連携基盤: TLS相互認証設定例 提供者環境リバースプロキシ設定](doc/TLSManual.md "提供者環境プロキシ")  参照。<br>
※リバースプロシキを使用しない場合、本設定は不要です。<br>

## 提供者コネクタ起動手順

1. 提供者コネクタ起動
```
cd connector/src/provider/
sh start.sh
```

起動した提供者コネクタの構成は以下となります。<br>
![Alt text](doc/png/producer.png?raw=true "提供者コネクタ構成図")


2. 提供者コネクタ起動確認
提供者コネクタ起動時にStateがすべてUpとなっていることを確認
```
NAME                             COMMAND                  SERVICE                          STATUS              PORTS
provider_authorization           "python3 -m swagger_…"   provider-authorization           running             8080/tcp
provider_catalog_search          "python3 -m swagger_…"   provider-catalog-search          running             8080/tcp
provider_connector_main          "python3 -m swagger_…"   provider-connector-main          running             8080/tcp
provider_data_exchange           "python3 -m swagger_…"   provider-data-exchange           running             8080/tcp
provider_provenance_management   "python3 -m swagger_…"   provider-provenance-management   running             8080/tcp
reverse-proxy                    "/docker-entrypoint.…"   reverse-proxy                    running             0.0.0.0:443->443/tcp, :::443->443/tcp
```
<br>

### プロキシを使用しない場合
<br>リバースプロキシのみ使用しない場合、以下のコマンドで提供者コネクタを起動してください。<br>
```
sh start.sh noproxy
```
<br>起動した際に、リバースプロキシが起動していないことを確認してください。<br>
リバースプロキシを起動しない場合、カタログ検索IFが28080番ポート、データ交換IFが38080番ポートで起動します。<br>
```
NAME                             COMMAND                  SERVICE                          STATUS              PORTS
provider_authorization           "python3 -m swagger_…"   provider-authorization           running             8080/tcp
provider_catalog_search          "python3 -m swagger_…"   provider-catalog-search          running             0.0.0.0:28080->8080/tcp, :::28080->8080/tcp
provider_connector_main          "python3 -m swagger_…"   provider-connector-main          running             8080/tcp
provider_data_exchange           "python3 -m swagger_…"   provider-data-exchange           running             0.0.0.0:38080->8080/tcp, :::38080->8080/tcp
provider_provenance_management   "python3 -m swagger_…"   provider-provenance-management   running             8080/tcp
```


### 提供者コネクタ停止手順 
```
sh stop.sh
```

## 提供者コネクタ利用ガイド

### 提供者内で認証なし・認可なしでの提供者コネクタ動作確認

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

(1) データ管理サーバ(HTTPサーバ)を提供者コネクタAPI経由で取得する場合
```
curl {提供者コネクタIPアドレス}/cadde/api/v4/file -H "x-cadde-resource-url:{リソースURL}" -H "x-cadde-resource-api-type:file/http" -O
```

(2) データ管理サーバ(FTPサーバ)を提供者コネクタAPI経由で取得する場合
```
curl {提供者コネクタIPアドレス}/cadde/api/v4/file -H "x-cadde-resource-url:{リソースURL}" -H "x-cadde-resource-api-type:file/ftp" -O
```

(3) データ管理サーバ(NGSIサーバ)を提供者コネクタ経由で公開する場合
<br>NGSI情報取得については、[別紙参照](doc/README_NGSI.md) 

<br>

### 認可について
<br>認可機能を使用する場合は、認可サーバを構築して認可設定を行い、提供者コネクタ内のコンフィグを適切に設定します。
<br>※認可機能を使用する場合、認証は必須となります。

1. 認可サーバ構築
<br>認可サーバの構築については、[認可サーバのドキュメント](misc/authorization/README.md) 参照<br>

2. 認可設定
<br>構築した認可サーバ画面、または、[CLI](doc/ProviderManual.md)にて認可設定を行う。<br>
※カタログ検索(詳細検索)に対して認可を行う場合は、{リソースURL}に指定するURLをprovider_ckan.jsonのdetail_ckan_urlに指定しているCKANのURLを設定してください。<br>
- CLIでの認可設定コマンド
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

3. 提供者コネクタ内のコンフィグ設定

(1) カタログ検索時の認可設定
<br>カタログ検索(詳細検索)に対して認可を行う場合は、provider_ckan.jsonのauthorizationをtrueにします。
```
{
    "release_ckan_url" : "https://example.com",
    "detail_ckan_url" : "https://example.com",
    "authorization" : true,
    "packages_search_for_data_exchange" : true
}
```

(2) データ取得時の認可設定
<br>提供手段に応じて、データ管理サーバのコンフィグにあるauthorizationのurlに{リソースURL}に含まれるURLを指定し、authorizationのenableをtrueに設定します。
```
http.jsonおよびftp.json
    "authorization": [
        {
            "url": "{リソースURLに含まれるURL文字列}",
            "enable" : true
        }
    ],

ngsi.json
    "authorization": [
        {
            "url": "{リソースURLに含まれるURL文字列}",
            "tenant": "{NGSIテナント}",
            "servicepath": "{NGSIサービスパス}",
            "enable" : true
        }
    ],
```


<br>提供者コネクタの利用方法については下記参照。<br>
[提供者環境構築ガイド](doc/ProviderManual.md "提供者環境構築ガイド")

### 提供者コネクタAPI
提供者コネクタのREST-API詳細仕様は、下記からダウンロードし参照してください。<br>
[RESTAPI仕様書格納先](doc/api/) 参照
- 提供者_カタログ検索IF.html
- 提供者_コネクタメイン.html
- 提供者_データ交換IF(CADDE).html
- 提供者_認証認可IF.html
- 提供者_来歴管理IF.html

<br>
<br>

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

