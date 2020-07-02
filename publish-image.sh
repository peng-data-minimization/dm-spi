#!/usr/bin/env bash

set -e

echo -e "\e[32m\nLoggin in to DockerHub...\e[0m"
docker login

echo -e "\e[32m\nBuilding and tagging docker images...\e[0m"
docker build -t kafka-data-minimization-spi .

docker tag kafka-data-minimization-spi tubpeng/kafka-data-minimization-spi

echo -e "\e[32m\nPushing images at DockerHub...\e[0m"
docker push tubpeng/kafka-data-minimization-spi