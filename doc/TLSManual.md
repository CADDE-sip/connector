# 分野間データ連携基盤: TLS相互認証設定例
- 利用者コネクタ-提供者コネクタ間の通信においてはTLSによる相互認証を行うことが前提となり、  
利用者及び提供者にて準備するものとなる。
- 本ページでは利用者システム(WebApp)―利用者コネクタ間および、利用者コネクタ―提供者コネクタ間におけるTLS相互認証を実現するための設定例を記載する。
- 利用者システム(WebApp)―利用者コネクタ間におけるアクセス制限は下図の利用者側のリバースプロキシにて実現する。
![Alt text](../doc/png/tls_example1.png?raw=true "Title")
- 利用者コネクタ―提供者コネクタ間におけるTLS相互認証は下図の利用者側のフォワードプロキシ及び提供者側のリバースプロキシにて実現する。
![Alt text](../doc/png/tls_example2.png?raw=true "Title")

## 前提条件

- 本ページでサンプルとして公開するOSS及び動作確認済みのバージョンは以下の通り
    - プロキシ：Squid 4.10
    - リバースプロキシ：Nginx 1.23.1

- プロキシおよびリバースプロシキはコネクタに含まれる
    - プロキシ：利用者コネクタ(connector/src/consumer/squid)
    - リバースプロキシ：提供者コネクタ(connector/src/provider/nginx)

- TLS相互認証に必要な証明書、秘密鍵(pem形式)はユーザーにて事前に準備済みであることを前提とする。
  - 各環境で必要なファイルは以下の通り
    - 利用者側：クライアント証明書、秘密鍵(暗号化なし)
    - 提供者側：サーバー証明書、秘密鍵、クライアント認証設定用CA証明書

- Linux 上での動作を前提とする。
  - Docker、Docker Compose が事前インストールされていることを前提とする。
  - 対応する Docker Version は以下の通りとする。
    - Docker 20.10.1
  - 対応する OS は、Linux の上記 Docker がサポートする OS とする。

- 本ページではTLS相互認証に必要な設定値のみの記載となる。
  - TLS認証以外の動作に関わる設定については必要に応じてユーザー側で考慮すること。

# 利用者環境プロキシ

## フォワードプロキシ(Squid)構築手順

1. コンフィグファイルの設定、ファイル配置

SSL Bump設定用自己署名SSL証明書を作成
```
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout squidCA.pem -out squidCA.pem
```
※証明書の有効期限は365日で仮置きしているため、必要に応じて期限を設定すること。

SSL Bump設定用自己署名SSL証明書、クライアント証明書、秘密鍵を下記ディレクトリに配置
```
connector/src/consumer/squid/volumes/ssl/
```


- squid.conf
  <br>connector/src/consumer/squid/volumesに配置<br>

  | 設定パラメータ | 概要 |
  | :------------- | :-------------------------- |
  | http_port | ssl_bumpを設定。 |
  | tls_outgoing_options | サーバー接続時に使用するクライアント証明書、秘密鍵を設定 |

 - 設定例
```
http_port 3128 ssl-bump generate-host-certificates=on dynamic_cert_mem_cache_size=4MB cert=/etc/squid/ssl/squidCA.pem
tls_outgoing_options cert=/etc/squid/ssl/{クライアント証明書} key=/etc/squid/ssl/{クライアント秘密鍵}
```
クライアント証明書、秘密鍵はユーザーで準備したファイル名に置き換える。

3. 初回プロキシ(Squid)起動

```
cd connector/src/consumer/squid
docker compose -f docker-compose_initial.yml up -d --build
```

4. 初回プロキシ(Squid)起動確認

```
docker compose ps
    Name                Command           State           Ports
------------------------------------------------------------------------
forward-proxy   /usr/sbin/squid -NYCd 1   Up      0.0.0.0:3128->3128/tcp
```

5. 初回プロキシ(Squid)TLS設定

```
docker exec -it forward-proxy /usr/lib/squid/security_file_certgen -c -s /var/lib/squid/ssl_db -M 20MB
docker cp forward-proxy:/var/lib/squid/ssl_db ./volumes/
docker compose -f docker-compose_initial.yml down
```

## リバースプロキシ(nginx)構築手順

### 利用者コネクタに対するアクセス制限を行う場合
利用者コネクタに対するアクセス制限を行う場合は、SSL/TLS認証を行う。<br>

1. サーバー証明書、秘密鍵、クライアント認証用CA証明書準備
<br>サーバー証明書、秘密鍵、クライアント認証用CA証明書を下記ディレクトリに配置する。<br>
```
connector/src/consumer/nginx/volumes/ssl/
```

2.  コンフィグファイルの設定
- default.conf
  connector/src/consumer/nginx/volumes/に配置<br>
  ssl用サーバ設定を有効にし、配置したサーバー証明書、秘密鍵、クライアント認証用CA証明書を設定してください。

  | 設定パラメータ | 概要 |
  | :------------- | :-------------------------- |
  | ssl_certificate | サーバー証明書を設定 |
  | ssl_certificate_key | 秘密鍵ファイルを設定 |
  | ssl_verify_client | クライアント認証使用時に設定(設定値:on) |
  | ssl_client_certificate | クライアント認証に使用するCA証明書を設定 |
  | location /cadde/api/v1/file | proxy_passに提供者コネクタのカタログ検索IFを指定 |
  | location /api/3/action/package_search | proxy_passに提供者コネクタのデータ交換IFを指定 |

 - 設定例
```
server{
    listen 443 ssl;
    server_name  localhost;

    ssl_certificate /etc/nginx/ssl/{サーバー証明書};
    ssl_certificate_key /etc/nginx/ssl/{サーバー秘密鍵};
    ssl_verify_client on;
    ssl_client_certificate /etc/nginx/ssl/{CA証明書};

    # データ取得(CADDE)
    location /cadde/api/v4/file {
        proxy_pass http://consumer_connector_main:8080/cadde/api/v4/file;
        add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; object-src 'self'; script-src 'none'; style-src 'none'";
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy no-referrer always;
        add_header Strict-Transport-Security "max-age=31536000";
        add_header Cache-Control no-store;
        add_header Pragma no-cache;
    }

    # データ取得(NGSI)
    location /cadde/api/v4/file {
        proxy_pass http://consumer_connector_main:8080/cadde/api/v4/entities;
        add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; object-src 'self'; script-src 'none'; style-src 'none'";
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy no-referrer always;
        add_header Strict-Transport-Security "max-age=31536000";
        add_header Cache-Control no-store;
        add_header Pragma no-cache;
    }

    # カタログ検索
    location /cadde/api/v4/catalog {
        proxy_pass http://consumer_connector_main:8080/cadde/api/v4/catalog;
        add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; object-src 'self'; script-src 'none'; style-src 'none'";
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy no-referrer always;
        add_header Strict-Transport-Security "max-age=31536000";
        add_header Cache-Control no-store;
        add_header Pragma no-cache;
    }
```
  ※サーバー証明書,サーバー秘密鍵,CA証明書はユーザーで用意したファイル名に置き換える。


# 提供者環境プロキシ

## リバースプロキシ(nginx)構築手順

### 提供者コネクタに対するアクセス制限を行う場合
提供者コネクタに対するアクセス制限を行う場合は、SSL/TLS認証を行う。<br>

1. サーバー証明書、秘密鍵、クライアント認証用CA証明書準備
<br>サーバー証明書、秘密鍵、クライアント認証用CA証明書を下記ディレクトリに配置する。<br>
```
connector/src/provider/nginx/volumes/ssl/
```

2.  コンフィグファイルの設定
- default.conf
  connector/src/provider/nginx/volumes/に配置<br>
  ssl用サーバ設定配置したサーバー証明書、秘密鍵、クライアント認証用CA証明書を設定してください。<br>

  | 設定パラメータ | 概要 |
  | :------------- | :-------------------------- |
  | ssl_certificate | サーバー証明書を設定 |
  | ssl_certificate_key | 秘密鍵ファイルを設定 |
  | ssl_verify_client | クライアント認証使用時に設定(設定値:on) |
  | ssl_client_certificate | クライアント認証に使用するCA証明書を設定 |
  | location /cadde/api/v1/file | proxy_passに提供者コネクタのカタログ検索IFを指定 |
  | location /api/3/action/package_search | proxy_passに提供者コネクタのデータ交換IFを指定 |

 - 設定例
```
    ssl_certificate /etc/nginx/ssl/{サーバー証明書};
    ssl_certificate_key /etc/nginx/ssl/{サーバー秘密鍵};
    ssl_verify_client on;
    ssl_client_certificate /etc/nginx/ssl/{CA証明書};

    # 認可機能
    location /cadde/api/v4/authorization {
        proxy_pass http://authz_nginx/cadde/api/v4/authorization;
        add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; object-src 'self'; script-src 'none'; style-src 'none'";
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy no-referrer always;
        add_header Strict-Transport-Security "max-age=31536000";
        add_header Cache-Control no-store;
        add_header Pragma no-cache;
    }

    # データ交換
    location /cadde/api/v4/file {
        proxy_pass http://provider_data_exchange:8080/cadde/api/v4/file;
        add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; object-src 'self'; script-src 'none'; style-src 'none'";
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy no-referrer always;
        add_header Strict-Transport-Security "max-age=31536000";
        add_header Cache-Control no-store;
        add_header Pragma no-cache;
    }

    # カタログ検索
    location /cadde/api/v4/catalog {
        proxy_pass http://provider_catalog_search:8080/cadde/api/v4/catalog;
        add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'self'; object-src 'self'; script-src 'none'; style-src 'none'";
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Referrer-Policy no-referrer always;
        add_header Strict-Transport-Security "max-age=31536000";
        add_header Cache-Control no-store;
        add_header Pragma no-cache;
    }
```
  ※サーバー証明書,サーバー秘密鍵,CA証明書はユーザーで用意したファイル名に置き換える。
