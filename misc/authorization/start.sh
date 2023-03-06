#!/bin/bash
sudo docker compose up --remove-orphans -d
sleep 1
sudo docker compose ps
