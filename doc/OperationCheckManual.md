# 分野間データ連携基盤: 動作確認環境利用ガイド
- コネクタ環境構築後に、正常に動作するか等を確認するための動作確認環境を準備しています。
- 本ページでは動作確認環境の利用方法を記載しています。
![Alt text](png/OperatonCheck.png?raw=true "Title")


# 利用者コネクタ構築時の動作確認環境利用ガイド

構築済みの利用者コネクタを動作確認環境の提供者コネクタと接続する手順です。

## 前提
- 利用者コネクタのプロキシに動作確認環境専用のクライアント証明書が設定されていることを前提とします。<br>
  [証明書のダウンロードはこちらから](../misc/OperationCheck/OperationCheckClientCertificate.zip) 

## 動作確認手順
1. アクセストークン取得

```
curl -v -X POST -H "Cache-Control: no-cache" -H "Content-Type: application/json" -d '{ "consumer_id": "cadde:verify_user01.aa", "password": "uVa1BvnKas_5odW" }' https://key-authen.test.data-linkage.jp/cadde/api/v1/consumer/token
```

2. 詳細検索


```
curl -X GET -v "http://{利用者コネクタのFQDN}:{ポート番号}/api/3/action/package_search?fq=caddec_dataset_id_for_detail:5add6540-cc2a-5080-8720-619c95e81e9e" -s -S -H "Cache-Control: no-cache" -H "x-cadde-search: detail" -H "x-cadde-provider:cadde:verify_user01.aa" -H "x-idp-url:https://key-authen.test.data-linkage.jp/auth/realms/cadde-authentication" -H "Authorization:{トークン}"
```

3. ファイル取得

```
curl -X GET -v "http://{利用者コネクタのFQDN}:{ポート番号}/cadde/api/v1/file" -H "x-cadde-resource-url:http://data-management/data/example_http.txt" -H "x-cadde-resource-api-type:file/http" -H "x-cadde-provider:cadde:verify_user01.aa" -H "x-idp-url:https://key-authen.test.data-linkage.jp/auth/realms/cadde-authentication" -H "Authorization:{トークン}" -o {出力ファイル名}
```

以下の結果が出力されていれば動作確認完了です。

```
Successful download

example_http.txt
```

# 提供者コネクタ構築時の動作確認環境利用ガイド

動作確認環境の利用者コネクタと構築済みの提供者コネクタを接続する手順です。

## 前提
- 提供者コネクタのリバースプロキシに動作確認環境専用のCA証明書が設定されていることを前提とします。<br>
  [証明書のダウンロードはこちらから](../misc/OperationCheck/OperationCheckClientCertificate.zip) 
- 提供者コネクタにFWが存在する場合はIPアドレス「35.75.141.64」を許可設定されていることを前提とします。

## 動作確認手順
1. アクセストークン取得

```
curl -v -X POST -H "Cache-Control: no-cache" -H "Content-Type: application/json" -d '{ "consumer_id": "cadde:verify_user01.aa", "password": "uVa1BvnKas_5odW" }' https://key-authen.test.data-linkage.jp/cadde/api/v1/consumer/token
```

2. 詳細検索

```
curl -X GET -v "https://verify-consumer.test.data-linkage.jp/api/3/action/package_search?fq=caddec_dataset_id_for_detail:{詳細検索用データセットID}" -s -S -H "Cache-Control: no-cache" -H "x-cadde-search: detail" -H "x-cadde-provider:{提供者ID}" -H "x-idp-url:https://key-authen.test.data-linkage.jp/auth/realms/cadde-authentication" -H "Authorization:{トークン}"
```


3. ファイル取得

```
curl -X GET -v "https://verify-consumer.test.data-linkage.jp/cadde/api/v1/file" -H "x-cadde-resource-url:{リソースURL}" -H "x-cadde-resource-api-type:{リソース提供手段の識別子}" -H "x-cadde-provider:{提供者ID}" -H "x-idp-url:https://key-authen.test.data-linkage.jp/auth/realms/cadde-authentication" -H "Authorization:{トークン}" -o {出力ファイル名}
```

