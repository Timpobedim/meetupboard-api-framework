#!/usr/bin/env bash
# Генерация Python-клиента по нормализованной спецификации openapi/meetupboard.json.
# openapi-generator (наследник Swagger Codegen) запускается в Docker — Java не нужна.
set -euo pipefail
cd "$(dirname "$0")/.."

docker run --rm -v "$PWD:/local" openapitools/openapi-generator-cli:v7.25.0 generate \
  -i /local/openapi/meetupboard.json \
  -g python \
  -o /local/clients/meetupboard_client \
  --package-name meetupboard_client \
  --additional-properties=projectName=meetupboard-client,packageVersion=1.0.0,library=urllib3 \
  --global-property=apiTests=false,modelTests=false,apiDocs=false,modelDocs=false
