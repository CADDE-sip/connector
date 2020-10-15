# 本ドキュメントについて
本ドキュメントについて：<br>
　本ドキュメントは、コネクタの実装方法/利用方法についてのガイドラインです。<br>
　したがって、分野間データ連携基盤(仮称：CADDE)やコネクタの基本事項についての説明は割愛しています。<br>
　コネクタについてのご質問、ご不明点、ご指摘事項、利用時の不具合、などがありましたら、以下にご連絡ください。<br>
<br>
[問い合わせ先](#問い合わせ先)

# 分野間データ連携基盤: コネクタ

## システム全体構成図
分野間データ連携基盤全体のシステム構成を下記に示します。
![Alt text](doc/png/system.png?raw=true "Title")


## 前提条件
- コネクタ外の前提条件を示します。

  - 利用者側システム(WebApp)、提供者側の CKAN カタログサイト、データ提供用のデータ管理(FTP サーバ,NGSI サーバ,HTTP サーバ)は、コネクタ設置前に事前に準備されていることを前提とします。
  - 利用者システム(WebApp)-利用者コネクタ間および、利用者コネクタ、提供者コネクタ間の通信路のセキュリティ（TLS 認証、IDS、IPS、ファイアウォール等)においては、OSS ソフトウェア、アプライアンス装置を用いて、コネクタ外で、利用者および提供者が準備するものとします。
  - 提供者 ID は、コネクタ外で事前に採番されていることを前提とします。

- Linux 上での動作を前提とします。

  - Docker、Docker Compose が事前インストールされていることを前提とします。
  - 対応する Docker Version は以下の通り。
    - Docker 19.03
  - 対応する OS は、Linux の上記 Docker がサポートする OS 。

- 提供データサイズ (2020 年 9 月末版)にてサポートするデータサイズは以下とします。
  - コンテキスト情報：１ MB 以下
  - ファイル：100MB 以下


<br><br>

# 利用者コネクタ
## 利用者コネクタ環境準備
[分野間データ連携基盤: TLS相互認証設定例 利用者環境プロキシ設定](misc/README.md "利用者環境プロキシ設定") 参照。

## 利用者コネクタ構築手順

1. 利用者コネクタ取得

```
git clone https://(ユーザID)@github.com/202009-LimitedRelease/connector.git
```

2. 共通ファイルの展開 <br>
setup.sh実行
```
cd connector/src/consumer/
sh setup.sh
```

3. コンフィグファイルの設定
- location.json
　<br>location.jsonファイルには、データ提供者接続先情報が記載されています。
　<br>コネクタ運用後は、最新のlocation.jsonを以下のリンクより確認し、更新してください。<br>
　　[location.json](/src/consumer/connector-main/swagger_server/configs/location.json)
　
　<br>個別にデータ提供者接続先情報を追加する場合は、利用者コネクタ内のlocation.jsonを編集してください。<br>
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置<br>提供者側に接続を行う際に指定する提供者側のアドレス設定を記載<br>

  | 設定パラメータ                        | 概要                                                                                                                                                               |
  | :------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | connector_location                    | 以下の提供者 ID を保持                                                                                                                                             |
  | 提供者 ID                             | 提供者 ID を記載する 以下の 3 パラメータを保持<br>provider_connector_data_exchange_url<br>provider_connector_catalog_search_url<br>contract_management_service_url |
  | provider_connector_data_exchange_url  | 提供者データ提供 IF の URL を設定                                                                                                                                  |
  | provider_connector_catalog_search_url | 提供者カタログ検索 IF の URL を設定                                                                                                                                |
  | contract_management_service_url       | 認証サーバの URL を設定 (2020 年 9 月版では未使用)                                                                                                                 |

- ckan.json
  <br>connector/src/consumer/catalog-search/swagger_server/configs/に配置<br>CKAN の横断検索時の接続先の設定を記載
  
  | 設定パラメータ | 概要                     |
  | :------------- | :----------------------- |
  | ckan_url       | 横断検索時の横断検索サーバのURLを記載 | 
 
- ftp.json
  <br>利用者コネクタから提供者コネクタを介さずデータ管理FTPサーバに直接アクセスする場合の設定
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置<br>ftp 接続時の設定を記載<br>

  | 設定パラメータ | 概要                                    |
  | :------------- | :-------------------------------------- |
  | ftp_auth       | 以下の ftp_id, ftp_pass を保持          |
  | ftp_id         | ftp 接続時の ID を設定(anonymous)      |
  | ftp_pass       | ftp 接続時のパスワードを設定(anonymous) |

- ngsi.json
　<br>利用者コネクタから提供者コネクタを介さずNGSIサーバに直接アクセスする場合の利用者ID、アクセストークンを設定
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置<br>NGSI の情報を取得する際に利用するアクセストークンの設定を記載<br>

  | 設定パラメータ | 概要                                                 |
  | :------------- | :--------------------------------------------------- |
  | ngsi_auth      | 以下の利用者 ID を保持                               |
  | 利用者 ID      | 利用者 ID を記載する 以下の auth を保持              |
  | auth           | NGSI へ API アクセスするためのアクセストークンを設定 |

4. 利用者環境情報の設定

connector/src/consumer/.envファイルを下記の通り修正する。<br>

(1) 利用者プロキシ情報の設定<br>
 HTTPS_PROXY_CADDE=XXX
 <br>XXX部分を利用者サーバのIPアドレス:プロキシ(Squid)構築手順で設定したポート番号に修正<br>

(2) 利用者プロキシの証明書情報の設定<br>
　REQUESTS_CA_BUNDLE=/etc/docker/certs.d/{自己署名SSL証明書ファイル名}
　{証明書ファイル名}は、XXX部分を分野間データ連携基盤: TLS相互認証設定例、プロキシ(Squid)構築手順、SSL Bump設定用自己署名SSL証明書を作成 の手順で出力したファイルを指定


5. 証明書ファイル配置<br>
REQUESTS_CA_BUNDLE で指定したディレクトリに自己署名SSL証明書ファイルを配置

```
cp -p (自己署名SSL証明書ファイル名) /etc/docker/certs.d/(自己署名SSL証明書ファイル名)
```

## 利用者コネクタ起動手順
1. 利用者コネクタ起動

```
cd connector/src/consumer
docker-compose up -d
```

2. 利用者コネクタ起動確認
StateがすべてUpとなっていることを確認
```
docker-compose ps
         Name                      Command            State            Ports
-------------------------------------------------------------------------------------
consumer_catalog_search   python3 -m swagger_server   Up      8080/tcp
consumer_connector_main   python3 -m swagger_server   Up      0.0.0.0:18080->8080/tcp
consumer_data_exchange    python3 -m swagger_server   Up      8080/tcp
```
## 利用者コネクタ停止手順
```
docker-compose down
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

### コネクタを利用した NGSIデータの取得方法
[CADDEコネクタを利用した NGSIデータの取得方法](doc/README_NGSI.md) 参照

<br>
<br>

# 提供者コネクタ

## 提供者コネクタ環境準備
[分野間データ連携基盤: TLS相互認証設定例 提供者環境リバースプロキシ設定](misc/README.md "提供者環境リバースプロキシ設定")  参照。

[提供者環境構築ガイド](doc/ProviderManual.md "提供者環境構築ガイド")

### 提供者コネクタ構築手順
1. 提供者コネクタの取得
```
git clone https://(ユーザID)@github.com/202009-LimitedRelease/connector.git
```

2. setup.sh実行
```
cd connector/src/provider/
sh setup.sh
```

3. コンフィグファイルの設定<br>

(1) CKANサーバを提供者コネクタ経由で詳細検索する場合
- ckan.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>CKAN の詳細検索時の接続先の設定を記載
  
  | 設定パラメータ | 概要                     |
  | :------------- | :----------------------- |
  | ckan_url       | 詳細検索時の接続先を記載 |
  
(2) データ管理サーバ(HTTPサーバ)を提供者コネクタ経由で公開する場合<br>
(2-1) 認証ありHTTPサーバに接続の場合
- http.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>http 接続でファイル取得する際に basic 認証が必要なドメインの設定を記載<br>

  | 設定パラメータ | 概要                                                                                                                                |
  | :------------- | :---------------------------------------------------------------------------------------------------------------------------------- |
  | basic_auth      | 以下のドメイン名を保持                                                                                                              |
  | ドメイン名     | basic 認証が必要なドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載 <br>以下の basic_id, basic_pass を保持 |
  | basic_id       | 対象ドメインへのファイル取得 http 接続時のベーシック認証 ID を設定                                                                  |
  | basic_pass     | 対象ドメインへのファイル取得 http 接続時のベーシック認証パスワードを設定  

(2-2) 認証なしHTTPサーバに接続の場合<br>
 http.jsonファイル不要。
  
(3) データ管理サーバ(FTPサーバ)を提供者コネクタ経由で公開する場合
- ftp.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>ftp 接続時の設定を記載<br>

  | 設定パラメータ | 概要                           |
  | :------------- | :----------------------------- |
  | ftp_auth       | 以下の ftp_id, ftp_pass を保持 |
  | ftp_id         | ftp 接続時の ID を設定         |
  | ftp_pass       | ftp 接続時のパスワードを設定   |
  
(4) データ管理サーバ(NGSIサーバ)を提供者コネクタ経由で公開する場合
- ngsi.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>NGSI の情報を取得する際に利用するアクセストークンの設定を記載<br>

  | 設定パラメータ | 概要                                                 |
  | :------------- | :--------------------------------------------------- |
  | ngsi_auth      | 以下の利用者 ID を保持                               |
  | 利用者 ID      | 利用者 ID を記載する 以下の auth を保持              |
  | auth           | NGSI へ API アクセスするためのアクセストークンを設定 |

### 提供者コネクタ起動手順 
```
cd connector/src/provider/
docker-compose up -d
```

### 提供者コネクタ起動確認
StateがすべてUpとなっていることを確認
```
docker-compose ps
         Name                      Command            State            Ports
-------------------------------------------------------------------------------------
provider_catalog_search   python3 -m swagger_server   Up      0.0.0.0:28080->8080/tcp
provider_connector_main   python3 -m swagger_server   Up      8080/tcp
provider_data_exchange    python3 -m swagger_server   Up      0.0.0.0:38080->8080/tcp
```

### 提供者コネクタ動作確認
提供者コネクタの外部API経由で、データ管理サーバ(HTTP or FTP or NGSI)からデータを取得できることを確認。<br>
{リソースURL}には、提供者コネクタからアクセス可能なデータ管理サーバのデータアクセス先を指定
- 例1: `ftp://192.168.0.1/xxx.pdf`
- 例2: `http://192.168.0.1/auth/xxx.csv`

(1) データ管理サーバ(HTTPサーバ)を提供者コネクタAPI経由で取得する場合
```
curl {提供者コネクタIPアドレス}:38080/cadde/api/v1/file -H "x-cadde-resource-url:{リソースURL}" -H "x-cadde-resource-api-type:file/http" -O
```

(2) データ管理サーバ(FTPサーバ)を提供者コネクタAPI経由で取得する場合
```
curl {提供者コネクタIPアドレス}:38080/cadde/api/v1/file -H "x-cadde-resource-url:{リソースURL}" -H "x-cadde-resource-api-type:file/ftp" -O
```

(3) データ管理サーバ(NGSIサーバ)を提供者コネクタ経由で公開する場合
別紙参照

### 提供者コネクタ停止手順 
```
docker-compose down
```

### 提供者コネクタAPI
提供者コネクタのREST-API詳細仕様は、下記からDownloadし参照してください。<br>
[RESTAPI仕様書格納先](doc/api/) 参照
- 提供者_カタログ検索IF.html
- 提供者_コネクタメイン.html
- 提供者_データ交換IF(CADDE).html

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

