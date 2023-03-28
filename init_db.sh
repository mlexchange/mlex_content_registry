#!/bin/bash

. .env
docker cp data/dump mongodb:/dump
docker exec -i mongodb /usr/bin/mongorestore --username=$MONGO_DB_USERNAME --password=$MONGO_DB_PASSWORD --authenticationDatabase=admin --db=content_registry --drop /dump/lbl-mlexchange
