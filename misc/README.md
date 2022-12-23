# 分野間データ連携基盤: TLS相互認証設定例
- 利用者コネクタ-提供者コネクタ間の通信においてはTLSによる相互認証を行うことが前提となり、  
利用者及び提供者にて準備するものとなる。
- 本ページではサンプルとして利用者コネクタ-提供者コネクタ間におけるTLS相互認証を実現するための設定例を記載する。
- TLS相互認証は下図のプロキシ及びリバースプロキシにて実現する。
![Alt text](../doc/png/conf_example.png?raw=true "Title")

## 前提条件

- 本ページでサンプルとして公開するOSS及び動作確認済みのバージョンは以下の通り
    - プロキシ：Squid 4.10
    - リバースプロキシ：Nginx 1.19.2

- TLS相互認証に必要な証明書、秘密鍵(pem形式)はユーザーにて事前に準備済みであることを前提とする。
  - 各環境で必要なファイルは以下の通り
    - 利用者側：クライアント証明書、秘密鍵(暗号化なし)
    - 提供者側：サーバー証明書(※)、秘密鍵、クライアント認証設定用CA証明書
      - (※)サーバー証明書のCN(Common Name)についてはIPアドレスでの指定が不可となるため、サブドメインまでを含んだドメインを指定ください。 
- Linux 上での動作を前提とする。
  - Docker、Docker Compose が事前インストールされていることを前提とする。
  - 対応する Docker Version は以下の通りとする。
    - Docker 20.10.1
  - 対応する OS は、Linux の上記 Docker がサポートする OS とする。

- 本ページではTLS相互認証に必要な設定値のみの記載となる。
  - TLS認証以外の動作に関わる設定については必要に応じてユーザー側で考慮すること。

# 利用者環境プロキシ設定

## プロキシ(Squid)構築手順

1. プロキシ(Squid)取得

```
git clone https://github.com/CADDE-sip/connector
```

2. コンフィグファイルの設定、ファイル配置

SSL Bump設定用自己署名SSL証明書を作成
```
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout squidCA.pem -out squidCA.pem
```
※証明書の有効期限は365日で仮置きしているため、必要に応じて期限を設定すること。

SSL Bump設定用自己署名SSL証明書、クライアント証明書、秘密鍵を下記ディレクトリに配置
```
connector/misc/squid/volumes/ssl/
```


- squid.conf
  <br>connector/misc/squid/volumesに配置<br>

  | 設定パラメータ | 概要 |
  | :------------- | :-------------------------- |
  | http_port | ssl_bumpを設定。 |
  | tls_outgoing_options | サーバー接続時に使用するクライアント証明書、秘密鍵を設定 |

 - 設定箇所(デフォルト：73行目)
```
tls_outgoing_options cert=/etc/squid/ssl/{クライアント証明書} key=/etc/squid/ssl/{クライアント秘密鍵}
```
クライアント証明書、秘密鍵はユーザーで準備したファイル名に置き換える。

 - (参考)証明書エラー回避用設定箇所(デフォルト：70行目)
```
# sslproxy_cert_error allow all
```
接続先がオレオレ証明書等で証明書エラーを回避する必要がある場合は、上記行のコメントアウトを解除する。

3. 初回プロキシ(Squid)起動

```
cd connector/misc/squid
docker-compose -f docker-compose_initial.yml up -d --build
```

4. 初回プロキシ(Squid)起動確認

```
docker-compose ps
    Name                Command           State           Ports
------------------------------------------------------------------------
forward-proxy   /usr/sbin/squid -NYCd 1   Up      0.0.0.0:3128->3128/tcp
```

5. 初回プロキシ(Squid)TLS設定

```
docker exec -it forward-proxy /usr/lib/squid/security_file_certgen -c -s /var/lib/squid/ssl_db -M 20MB
docker cp forward-proxy:/var/lib/squid/ssl_db ./volumes/
docker-compose -f docker-compose_initial.yml stop
```
## プロキシ(Squid)起動手順
1. プロキシ(Squid)起動

```
docker-compose -f docker-compose.yml up -d
```

2. プロキシ(Squid)起動確認

```
docker-compose ps
    Name                Command           State           Ports
------------------------------------------------------------------------
forward-proxy   /usr/sbin/squid -NYCd 1   Up      0.0.0.0:3128->3128/tcp
```

## プロキシ(Squid)停止手順

```
docker-compose down
```

# 提供者環境リバースプロキシ設定

## リバースプロキシ(nginx)構築手順

1. リバースプロキシ(nginx)取得

```
git clone https://github.com/CADDE-sip/connector
```

2. コンフィグファイルの設定、ファイル配置

サーバー証明書、秘密鍵、クライアント認証用CA証明書を下記ディレクトリに配置
```
connector/misc/nginx/volumes/ssl/
```


- default.conf
  <br>connector/misc/nginx/volumes/に配置<br>

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
    location /cadde/api/v1/file {
        proxy_pass http://{提供者コネクタのFQDNまたはIPアドレス}:38080/cadde/api/v1/file;
    }

    location /api/3/action/package_search {
        proxy_pass http://{提供者コネクタのFQDNまたはIPアドレス}:28080/api/3/action/package_search;
    }
```
サーバー証明書,サーバー秘密鍵,CA証明書はユーザーで用意したファイル名に置き換える。

## リバースプロキシ(nginx)起動手順
1. リバースプロキシ(nginx)起動

```
cd connector/misc/nginx
docker-compose -f docker-compose.yml up -d
```

2. リバースプロキシ(nginx)起動確認

```
docker-compose ps
    Name                   Command               State                    Ports
-------------------------------------------------------------------------------------------------
reverse-proxy   /docker-entrypoint.sh ngin ...   Up      0.0.0.0:443->443/tcp, 0.0.0.0:80->80/tcp
```

## リバースプロキシ(nginx)停止手順
```
docker-compose down
```
