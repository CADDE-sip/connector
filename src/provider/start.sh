#!/bin/bash
start_type=$1

if [ "$start_type" == "noproxy" ]
then
    # リバースプロキシを起動しない
    docker compose -f docker-compose_noproxy.yml up -d
    docker compose ps

else
    # 全コンテナを起動
    docker compose -f docker-compose.yml up -d
    docker compose ps

fi
