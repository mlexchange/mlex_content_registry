#!/bin/bash

docker cp data/dump mongodb:/dump
docker exec -i mongodb /usr/bin/mongorestore --username $1 --password $2 --authenticationDatabase admin --db content_registry /dump/lbl-mlexchange
