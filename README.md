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
[分野間データ連携基盤: TLS相互認証設定例 利用者環境プロキシ設定](misc/README.md "利用者環境プロキシ設定") 参照。

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

  | 設定パラメータ                        | 概要                                                                                                                                                               |
  | :------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | connector_location                    | 以下の提供者 ID を保持                                                                                                                                             |
  | 提供者 ID                             | 提供者 ID を記載する 以下の 3 パラメータを保持<br>provider_connector_data_exchange_url<br>provider_connector_catalog_search_url<br>contract_management_service_url |
  | provider_connector_data_exchange_url  | 提供者データ提供 IF の URL                                                                                                                                         |
  | provider_connector_catalog_search_url | 提供者カタログ検索 IF の URL                                                                                                                                       |
  | provider_connector_id                 | 来歴管理登録するときに提供者を特定するためのID                                                                                                                     |
  | contract_management_service_url       | 契約管理サーバの URL                                                                                                                                               |
  | contract_management_service_key       | 契約管理サーバの API キー                                                                                                                                          |

- connector.json
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置
  <br>認証サーバに登録した利用者コネクタのIDとシークレットを記載<br>

  | 設定パラメータ                        | 概要                                                                                                                                                               |
  | :------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | consumer_connector_id                 | 認証サーバに設定した利用者コネクタのID                                                                                                                         |
  | consumer_connector_secret             | 認証サーバが発行した利用者コネクタのシークレット                                                                                                               |
  | history_management_token              | 来歴管理が使用するトークン (2022 年 3 月版では未使用)                                                                                                              |

- ngsi.json
  <br>利用者コネクタから提供者コネクタを介さずNGSIサーバに直接アクセスする場合の利用者ID、アクセストークンを設定
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置
  <br>NGSI の情報を取得する際に利用するアクセストークンの設定を記載<br>

  | 設定パラメータ | 概要                                                 |
  | :------------- | :--------------------------------------------------- |
  | ngsi_auth      | 以下、ドメイン毎の設定を配列で保持                               |
  | domain      　 | ドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載              |
  | auth           | NGSI へ API アクセスするためのアクセストークンを設定 |

- idp.json
  <br>connector/src/consumer/connector-main/swagger_server/configs/に配置
  <br>IdPのURLと認証サーバのアイデンティティプロバイダー名を記載
  <br>利用者側で外部IdPによる認証を行わない場合、CADDEが提供するIdPを利用

  | 設定パラメータ               | 概要                           |
  | :--------------------------- | :----------------------------- |
  | CADDEが提供するIdP           | "cadde"固定                    |
  | CADDEが連携する外部IdPのURL  | アイデンティティプロバイダー名 |

- authentication.json
  <br>connector/src/consumer/authentication-authorization/swagger_server/configs/に配置<br>認証時の接続先を記載

  | 設定パラメータ                     | 概要                                                                     |
  | :--------------------------------- | :----------------------------------------------------------------------- |
  | authentication_server_url          | 認証サーバのURL                                                      |
  | introspect                         | トークン検証設定                                                         |
  | introspect - endpoint              | トークン検証エンドポイント。"protocol/openid-connect/token"固定          |
  | federation                         | トークン連携設定                                                         |
  | federation - endpoint              | トークン連携エンドポイント。"protocol/openid-connect/token"固定          |
  | federation - grant_type            | 許諾タイプ。"urn:ietf:params:oauth:grant-type:token-exchange"固定        |
  | federation - subject_token_type    | トークンタイプ。"urn:ietf:params:oauth:token-type:access_token"固定      |
  | federation - requested_token_type  | 要求トークンタイプ。"urn:ietf:params:oauth:token-type:access_token"固定  |

- ckan.json
  <br>connector/src/consumer/catalog-search/swagger_server/configs/に配置<br>CKAN の横断検索時の接続先の設定を記載
  
  | 設定パラメータ | 概要                     |
  | :------------- | :----------------------- |
  | ckan_url       | 横断検索時の横断検索サーバのURLを記載 | 

- provenance.json
  <br>connector/src/consumer/provenance-management/swagger_server/configs/に配置<br>来歴管理サーバのURLの設定を記載
  <br>来歴管理I/FがおなじDockerネットワークで起動している場合は変更不要
  
  | 設定パラメータ                 | 概要                     |
  | :----------------------------- | :----------------------- |
  | provenance_management_api_url  | 来歴管理サーバのURL      | 

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
docker-compose -p consumer up -d
```

2. 利用者コネクタ起動確認
StateがすべてUpとなっていることを確認
```
docker-compose -p consumer ps
                Name                             Command             State      Ports
---------------------------------------------------------------------------------------
consumer_authentication_authorization   python3 -m swagger_server   Up         8080/tcp
consumer_catalog_search                 python3 -m swagger_server   Up         8080/tcp
consumer_connector_main                 python3 -m swagger_server   Up         0.0.0.0:80->8080/tcp
consumer_data_exchange                  python3 -m swagger_server   Up         8080/tcp
consumer_provenance_management          python3 -m swagger_server   Up         8080/tcp
```
## 利用者コネクタ停止手順
```
docker-compose -p consumer down
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

<br>
<br>

# 提供者コネクタ

## 提供者コネクタ環境準備
[分野間データ連携基盤: TLS相互認証設定例 提供者環境リバースプロキシ設定](misc/README.md "提供者環境リバースプロキシ設定")  参照。

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
- ckan.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>CKANの接続先の設定を記載
  
  | 設定パラメータ    | 概要                      |
  | :---------------- | :------------------------ |
  | release_ckan_url  | 横断検索用CKANのURLを記載 |
  | detail_ckan_url   | 詳細検索用CKANのURLを記載 |
  
(2) データ管理サーバ(HTTPサーバ)を提供者コネクタ経由で公開する場合<br>
(2-1) 認証ありHTTPサーバに接続の場合
- http.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>http 接続でファイル取得する際に basic 認証が必要なドメインの設定を記載<br>

  | 設定パラメータ | 概要                                                                                          |
  | :------------- | :-------------------------------------------------------------------------------------------- |
  | basic_auth     | 以下、ドメイン毎の設定を配列で保持                               |
  | domain         | basic 認証が必要なドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載      |
  | basic_id       | 対象ドメインへのファイル取得 http 接続時のベーシック認証 ID を設定                            |
  | basic_pass     | 対象ドメインへのファイル取得 http 接続時のベーシック認証パスワードを設定                      |
  | basic_pass     | 対象ドメインへのファイル取得 http 接続時のベーシック認証パスワードを設定                      |
  | authorization  | リソースの認可確認有無 (認可確認を行う場合enable, 認可確認を行わない場合disableを設定     |

(2-2) 認証なしHTTPサーバに接続の場合<br>
 http.jsonファイルの編集不要。
  
(3) データ管理サーバ(FTPサーバ)を提供者コネクタ経由で公開する場合
(3-1) anonymous/anonymous以外をID/パスワードとするFTPサーバに接続の場合
- ftp.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>ftp 接続時の設定を記載<br>

  | 設定パラメータ | 概要                           |
  | :------------- | :-------------------------------------------------------------------------------------------- |
  | ftp_auth       | 以下、ドメイン毎の設定を配列で保持                               |
  | domain         | basic 認証が必要なドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載      |
  | ftp_id         | ftp 接続時の ID を設定                                                                        |
  | ftp_pass       | ftp 接続時のパスワードを設定                                                                  |
  | authorization  | リソースの認可確認有無 (認可確認を行う場合enable, 認可確認を行わない場合disableを設定     |

(3-2) anonymous/anonymousをID/パスワードとするFTPサーバに接続の場合
 ftp.jsonファイルの編集不要。

(4) データ管理サーバ(NGSIサーバ)を提供者コネクタ経由で公開する場合
- ngsi.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>NGSI の情報を取得する際に利用するアクセストークンの設定を記載<br>

  | 設定パラメータ | 概要                                                 |
  | :------------- | :--------------------------------------------------- |
  | ngsi_auth      | 以下、ドメイン毎の設定を配列で保持                               |
  | domain      　 | ドメイン名を記載する ポート指定を行う場合は":ポート番号"を合わせて記載              |
  | auth           | NGSI へ API アクセスするためのアクセストークンを設定 |
  | authorization  | リソースの認可確認有無 (認可確認を行う場合enable, 認可確認を行わない場合disableを設定     |

(5) 認証および認可をおこなう場合
- authentication.json
  <br>connector/src/provider/authentication-authorization/swagger_server/configs/に配置<br>認証および認可時の接続先を記載

  | 設定パラメータ                     | 概要                                                                     |
  | :--------------------------------- | :----------------------------------------------------------------------- |
  | authentication_server_url          | 認可サーバのURL                                                      |
  | introspect                         | トークン検証設定                                                         |
  | introspect - endpoint              | トークン検証エンドポイント。"protocol/openid-connect/token"固定          |
  | federation                         | トークン連携設定                                                         |
  | federation - endpoint              | トークン連携エンドポイント。"protocol/openid-connect/token"固定          |
  | federation - grant_type            | 許諾タイプ。"urn:ietf:params:oauth:grant-type:token-exchange"固定        |
  | federation - subject_token_type    | トークンタイプ。"urn:ietf:params:oauth:token-type:access_token"固定      |
  | federation - requested_token_type  | 要求トークンタイプ。"urn:ietf:params:oauth:token-type:access_token"固定  |
  | federation - subject_issuer        | 認証と連携するアイデンティティプロバイダー名                             |
  | pat_req                            | APIトークン取得設定                                                      |
  | pat_req - endpoint                 | APIトークン連携エンドポイント。"protocol/openid-connect/token"固定       |
  | pat_req - grant_type               | 許諾タイプ。"client_credentials"固定                                     |
  | contract                           | 認可確認設定                                                             |
  | contract - endpoint                | 認可確認エンドポイント。"protocol/openid-connect/token"固定              |
  | contract - grant_type              | 許諾タイプ。"urn:ietf:params:oauth:grant-type:uma-ticket"固定            |

- connector.json
  <br>connector/src/provider/connector-main/swagger_server/configs/に配置<br>認可サーバに登録した提供者コネクタのIDとシークレットを記載<br>

  | 設定パラメータ                        | 概要                                                                  |
  | :------------------------------------ | :-------------------------------------------------------------------- |
  | provider_id                           | 来歴管理登録するときに提供者を特定するためのID                        |
  | provider_connector_id                 | 認可サーバに設定した提供者コネクタのID                            |
  | provider_connector_secret             | 認可サーバが発行した提供者コネクタのシークレット                  |
  | contract_management_service_url       | 契約管理サーバの URL                                                  |
  | contract_management_service_key       | 契約管理サーバの API キー                                             |
  | history_management_token              | 来歴管理が使用するトークン (2022 年 3 月版では未使用)                 |

(6) 来歴管理をおこなう場合
- provenance.json
  <br>connector/src/provider/provenance-management/swagger_server/configs/に配置
  <br>来歴管理サーバのURLの設定を記載
  <br>来歴管理I/FがおなじDockerネットワークで起動している場合は変更不要  
  <br>※来歴管理を行う場合は認証認可が必須のため(5)の設定も必要となる
  
  | 設定パラメータ                 | 概要                     |
  | :----------------------------- | :----------------------- |
  | provenance_management_api_url  | 来歴管理サーバのURL      | 


### 提供者コネクタ起動手順 
```
cd connector/src/provider/
docker-compose -p provider up -d
```

### 提供者コネクタ起動確認
StateがすべてUpとなっていることを確認
```
docker-compose -p provider ps
         Name                                Command              State            Ports
--------------------------------------------------------------------------------------------------
provider_authentication_authorization  python3 -m swagger_server   Up      8080/tcp
provider_catalog_search                python3 -m swagger_server   Up      0.0.0.0:28080->8080/tcp
provider_connector_main                python3 -m swagger_server   Up      8080/tcp
provider_data_exchange                 python3 -m swagger_server   Up      0.0.0.0:38080->8080/tcp
provider_provenance_management         python3 -m swagger_server   Up      8080/tcp
```

### 提供者コネクタ動作確認
提供者コネクタの外部API経由で、データ管理サーバ(HTTP or FTP or NGSI)からデータを取得できることを確認。<br>
{リソースURL}には、詳細検索用CKAN登録済みで提供者コネクタからアクセス可能なデータ管理サーバのデータアクセス先を指定
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
docker-compose -p provider down
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


