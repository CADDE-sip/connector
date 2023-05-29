echo -n "CADDEユーザID: "
read realm

echo -n "提供者コネクタのクライアントID: "
read client

echo -n "CADDE認証機能認証サーバのURL: "
read identity_provider

json=$(cat << EOS
{
  "realm": "${realm}",
  "client": "${client}",
  "identity_provider": "${identity_provider}"
}
EOS
)

echo $json > ./settings_provider_setup.json

sudo docker compose exec fastapi python3 provider_setup.py
