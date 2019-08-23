#!/usr/bin/env bash

PROJECT=$1
USER=$2
PASSWORD=$3

if [ -z "${PROJECT}" ]; then
  echo "Project not defined"
  exit 0
fi

if [ -z "${USER}" ]; then
    read -r -p "Username: " USER
    read -r -s -p "Password: " PASSWORD
fi

TOKEN=$(curl -X POST -s -d "username=${USER}&password=${PASSWORD}" "https://tools.lab.fiware.org/ktp/${PROJECT}")

echo ""
echo -e "\nToken: $TOKEN"
echo ""