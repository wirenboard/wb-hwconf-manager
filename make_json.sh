#!/bin/bash

cat wb-hardware.schema.json modules/*.schema.json | \
    jq --slurp '.[0].definitions = .[0].definitions + (.[1:] | add) | .[0]'  > wb-hardware.schema.json.NEW

