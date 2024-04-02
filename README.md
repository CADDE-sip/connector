# 本ドキュメントについて
本ドキュメントについて：<br>
  本ドキュメントは、コネクタの実装方法/利用方法についてのガイドラインです。<br>
  したがって、分野間データ連携基盤(CADDE)やコネクタの基本事項についての説明は割愛しています。<br>
  コネクタについてのご質問、ご不明点、ご指摘事項、利用時の不具合、などがありましたら、以下にご連絡ください。<br>
  ※CADDE（ジャッデ）は大学共同利用機関法人 情報・システム研究機構 国立情報学研究所の登録商標です。<br>
<br>

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

## 導入ガイドライン
CADDEコネクタの導入範囲、構成については、下記ガイドを参照してください。
- [CADDE4.0_導入ガイド【第1編】システム導入パターン編(2023年3月版)_1.docx](doc/guide/CADDE4.0_導入ガイド【第1編】システム導入パターン編(2023年3月版)_1.docx)
- [CADDE4.0_導入ガイド【第2編】データ提供者環境導入編(2023年3月版)_1.docx](doc/guide/CADDE4.0_導入ガイド【第2編】データ提供者環境導入編(2023年3月版)_1.docx)
- [CADDE4.0_導入ガイド【第3編】データ利用者環境導入編(2023年3月版)_2.docx](doc/guide/CADDE4.0_導入ガイド【第3編】データ利用者環境導入編(2023年3月版)_2.docx)

<br>
<br>

# 利用者コネクタ

## 利用者コネクタ構築手順

1. 利用者コネクタ取得

```
git clone https://github.com/CADDE-sip/connector
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
<br>[分野間データ連携基盤: TLS相互認証設定例 フォワードプロキシ(Squid)構築手順](doc/TLSManual.md "利用者環境プロキシ") 参照。<br>
※フォワードプロシキを使用しない場合、本設定は不要です。<br>

5. リバースプロキシの設定
<br>利用者コネクタへアクセス制限を行う場合は、下記を参考に利用者コネクタのリバースプロキシにSSL/TLS設定を行います。<br>
[分野間データ連携基盤: TLS相互認証設定例 リバースプロキシ(nginx)構築手順](doc/TLSManual.md "利用者環境プロキシ") 参照。<br>
※利用者コネクタへアクセス制限を行わず、リバースプロシキを使用しない場合、本設定は不要です。<br>

<br>
<br>

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
コネクタ起動時にStateがすべてrunningとなっていることを確認してください。<br>

```
NAME                             COMMAND                  SERVICE                          STATUS              PORTS
consumer_authentication          "python3 -m swagger_…"   consumer-authentication          running             8080/tcp
consumer_catalog_search          "python3 -m swagger_…"   consumer-catalog-search          running             8080/tcp
consumer_connector_main          "python3 -m swagger_…"   consumer-connector-main          running             8080/tcp
consumer_data_exchange           "python3 -m swagger_…"   consumer-data-exchange           running             8080/tcp
consumer_provenance_management   "python3 -m swagger_…"   consumer-provenance-management   running             8080/tcp
consumer_forward-proxy           "/usr/sbin/squid '-N…"   consumer-forward-proxy           running             3128/tcp
consumer_reverse-proxy           "/docker-entrypoint.…"   consumer-reverse-proxy           running             0.0.0.0:80->80/tcp, :::8080->80/tcp
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
consumer_forward-proxy           "/usr/sbin/squid '-N…"   consumer-forward-proxy           running             3128/tcp
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
consumer_reverse-proxy           "/docker-entrypoint.…"   consumer-reverse-proxy           running             0.0.0.0:80->80/tcp, :::8080->80/tcp
```

### 利用者コネクタ停止手順
```
sh stop.sh
```

### V3.0からV4.0へのアップデート方法
<br>利用者コネクタのアップデートは以下の手順で行ってください。<br>

1. 利用者コネクタ停止
```
# V3.0の利用者コネクタ停止手順
cd src/consumer/
docker-compose -p consumer down
```

2. コンフィグ類の退避
<br>各コンフィグを任意のディレクトリへ退避してください。
<br>.envの設定はV4.0から固定となります。利用者側で変更する場合は編集してください。
```
cd src/consumer/
cp .env {任意のディレクトリ}
cp catalog-search/swagger_server/configs/ckan.json {任意のディレクトリ}
cp connector-main/swagger_server/configs/connector.json {任意のディレクトリ}
cp connector-main/swagger_server/configs/ftp.json {任意のディレクトリ}
cp connector-main/swagger_server/configs/http.json {任意のディレクトリ}
cp connector-main/swagger_server/configs/location.json {任意のディレクトリ}
cp connector-main/swagger_server/configs/ngsi.json {任意のディレクトリ}
cp provenance-management/swagger_server/configs/provenance.json {任意のディレクトリ}
```
3. 利用者コネクタアップデート
```
git checkout .
git pull
```

4. コンフィグ類のマージ
<br>V3.0とV4.0で更新のあるコンフィグは以下となります。
<br>[利用者コネクタ構築手順のコンフィグ設定](#利用者コネクタ構築手順) を参考に設定してください。

| V3.0のコンフィグファイル名                                   | V4.0のコンフィグファイル名                                   | コンフィグファイル内容の変更点               |
| :----------------------------------------------------------- | :----------------------------------------------------------- |:-------------------------------------------- |
| .env                                                         | .env                                                         | 設定値を固定(編集不要)                       |
| catalog-search/swagger_server/configs/ckan.json              | catalog-search/swagger_server/configs/public_ckan.json       | コンフィグファイル名およびフィールド名の変更 |
| connector-main/swagger_server/configs/connector.json         | connector-main/swagger_server/configs/connector.json         | history_management_tokenの削除<br>location_service_urlおよびtrace_log_enableの追加            |
| connector-main/swagger_server/configs/idp.json               | －                                                           | コンフィグファイル削除                       |
| connector-main/swagger_server/configs/location.json          | connector-main/swagger_server/configs/location.json          | provider_connector_urlの追加<br>provider_connector_data_exchange_urlの削除<br>provider_connector_catalog_search_urlの削除<br>contract_management_service_urlの削除<br>contract_management_service_keyの削除 |
| connector-main/swagger_server/configs/ngsi.json              | connector-main/swagger_server/configs/ngsi.json              | authorizationの削除                          |
| provenance-management/swagger_server/configs/provenance.json | provenance-management/swagger_server/configs/provenance.json | デフォルト値の削除                           |

<br>以下2つのコンフィグファイルは更新のないため、退避したコンフィグを上書きしてください。
| 更新のないコンフィグファイル名                               |
| :----------------------------------------------------------- |
| connector-main/swagger_server/configs/ftp.json               |
| connector-main/swagger_server/configs/http.json              |

<br>

5. 利用者コネクタ起動
<br>[利用者コネクタ起動手順](#利用者コネクタ起動手順) 参照

<br>
<br>

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
[CADDEコネクタを利用した NGSIデータの取得方法](doc/README_NGSI.md) 参照 <br>

<br>
<br>

# 提供者コネクタ

## 提供者コネクタ環境準備
[提供者環境構築ガイド](doc/ProviderManual.md "提供者環境構築ガイド")

## 提供者コネクタ構築手順
1. 提供者コネクタの取得
```
git clone https://github.com/CADDE-sip/connector
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
- 認可機能構築
<br>認可機能の構築については、[別紙参照](misc/authorization/README.md)<br>

- authorization.json
  <br>connector/src/provider/authorization/swagger_server/configs/に配置<br>
  認証および認可時の接続先を記載してください。<br>

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | authorization_server_url           | 認可機能のアクセスURL                                         |

- connector.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>
  認可機能に登録した提供者コネクタのIDとシークレットを記載してください。<br>

  | 設定パラメータ                     | 概要                                                            |
  | :--------------------------------- | :-------------------------------------------------------------- |
  | provider_id                        | CADDEユーザID(提供者)                                           |
  | provider_connector_id              | 認可機能に設定した提供者コネクタのID                          |
  | provider_connector_secret          | 認可機能が発行した提供者コネクタのシークレット                |
  | trace_log_enable                   | コネクタの詳細ログ出力有無<br>出力無の設定でも基本的な動作ログは出力されます |

- カタログ検索時の認可設定
<br>カタログ検索(詳細検索)に対して認可を行う場合は、provider_ckan.jsonのauthorizationをtrueにします。
```
{
    "release_ckan_url" : "https://example.com",
    "detail_ckan_url" : "https://example.com",
    "authorization" : true,
    "packages_search_for_data_exchange" : true
}
```

- データ取得時の認可設定
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
[分野間データ連携基盤: TLS相互認証設定例 提供者環境リバースプロキシ設定](doc/TLSManual.md "提供者環境プロキシ")  参照。<br>
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
提供者コネクタ起動時にStateがすべてrunningとなっていることを確認
```
NAME                             COMMAND                  SERVICE                          STATUS              PORTS
provider_authorization           "python3 -m swagger_…"   provider-authorization           running             8080/tcp
provider_catalog_search          "python3 -m swagger_…"   provider-catalog-search          running             8080/tcp
provider_connector_main          "python3 -m swagger_…"   provider-connector-main          running             8080/tcp
provider_data_exchange           "python3 -m swagger_…"   provider-data-exchange           running             8080/tcp
provider_provenance_management   "python3 -m swagger_…"   provider-provenance-management   running             8080/tcp
provider_reverse-proxy           "/docker-entrypoint.…"   provider-reverse-proxy           running             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp, :::80->80/tcp, :::443->443/tcp
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

### V3.0からV4.0へのアップデート方法
<br>提供者コネクタのアップデートは以下の手順で行ってください。<br>

1. 提供者コネクタ停止
```
# V3.0の提供者コネクタ停止手順
cd src/provider/
docker-compose -p provider down
```

2. コンフィグ類の退避
<br>各コンフィグを任意のディレクトリへ退避してください。
```
cd src/provider/
cp authentication-authorization/swagger_server/configs/authorization.json	{任意のディレクトリ}
cp connector-main/swagger_server/configs/ckan.json {任意のディレクトリ}
cp connector-main/swagger_server/configs/connector.json {任意のディレクトリ}
cp connector-main/swagger_server/configs/ftp.json {任意のディレクトリ}
cp connector-main/swagger_server/configs/http.json {任意のディレクトリ}
cp connector-main/swagger_server/configs/ngsi.json {任意のディレクトリ}
cp provenance-management/swagger_server/configs/provenance.json {任意のディレクトリ}
```
3. 提供者コネクタアップデート
```
git checkout .
git pull
```

4. コンフィグ類のマージ
<br>V3.0とV4.0で更新のあるコンフィグは以下となります。
<br>[提供者コネクタ構築手順のコンフィグ設定](#提供者コネクタ構築手順) を参考に設定してください。

| V3.0のコンフィグファイル名                                             | V4.0のコンフィグファイル名                               | コンフィグファイル内容の変更点                                                                |
| :--------------------------------------------------------------------- | :------------------------------------------------------- |:--------------------------------------------------------------------------------------------- |
| authentication-authorization/swagger_server/configs/authorization.json | authorization/swagger_server/configs/authorization.json  | コンテナ名の変更<br>既存設定全削除<br>authorization_server_urlの追加                          |
| connector-main/swagger_server/configs/ckan.json                        | connector-main/swagger_server/configs/provider_ckan.json | コンフィグファイル名の変更<br>authorizationの追加<br>packages_search_for_data_exchangeの追加  |
| connector-main/swagger_server/configs/connector.json                   | connector-main/swagger_server/configs/connector.json     | contract_management_service_urlの削除<br>contract_management_service_keyの削除<br>history_management_tokenの削除<br>trace_log_enableの追加            |
| connector-main/swagger_server/configs/ftp.json                         | connector-main/swagger_server/configs/ftp.json           | authorizationの追加<br>contract_management_serviceの追加<br>register_provenanceの追加         |
| connector-main/swagger_server/configs/http.json                        | connector-main/swagger_server/configs/http.json          | authorizationの追加<br>contract_management_serviceの追加<br>register_provenanceの追加         |
| connector-main/swagger_server/configs/ngsi.json                        | connector-main/swagger_server/configs/ngsi.json          | ngsi_authからauthorizationフィールド削除<br>authorizationの追加<br>contract_management_serviceの追加<br>register_provenanceの追加            |

5. 提供者コネクタ起動
<br>[提供者コネクタ起動手順](#提供者コネクタ起動手順) 参照

<br>
<br>

## 提供者コネクタ利用ガイド
<br>提供者コネクタの利用方法については下記参照。<br>
[提供者環境構築ガイド](doc/ProviderManual.md "提供者環境構築ガイド")

### 提供者コネクタAPI
<br>提供者コネクタのREST-API詳細仕様は、下記からダウンロードし参照してください。<br>
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

