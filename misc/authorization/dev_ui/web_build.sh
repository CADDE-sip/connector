#!/bin/bash

# 現状のプロセスを停止
# docker rm -f `docker ps -a -q`

build_type=$1
CONTAINER=authz_ui
docker rm -f $CONTAINER

# リリースビルド => vueファイルをリリースビルドして、nginxの公開ディレクトリに配置
if [ "$build_type" == "build" ]
then
    echo '================================ '
    echo 'portal quasar build '
    echo '================================ '
    sudo docker compose -f docker-compose-dev.yml -p authz_dev_ui up -d
    sudo docker exec -it $CONTAINER /bin/sh -c 'cd app; quasar build'
    cp -pR app/dist/spa/* ../nginx/public/
    sudo docker compose -f docker-compose-dev.yml -p authz_dev_ui stop

# デバッグ用ビルド => vueファイルをデバッグビルド、docker-compose-dev.ymlのポートで公開 9000
elif [ "$build_type" == "debug" ]
then
    echo '================================ '
    echo 'portal quasar debug'
    echo '================================ '
    sudo docker compose -f docker-compose-dev.yml -p authz_dev_ui up -d
    sudo docker exec -it $CONTAINER /bin/sh -c 'cd app; quasar dev'

else
  echo "[Release Build Command]"
  echo "sh client_build.sh build"
  echo "[Debug Build Command]"
  echo "sh client_build.sh debug"
fi

