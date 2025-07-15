#! /usr/bin/env bash

set -e
set -x

source .venv/bin/activate
cd backend
python -c "import src.main; import json; print(json.dumps(src.main.app.openapi()))" > ../openapi.json
cd ..
mv openapi.json frontend/
cd frontend
npm run generate-client
rm openapi.json

# generate raspi server api client
cd ../backend/src/modules/raspi
python -c "import raspi_server.main; import json; print(json.dumps(raspi_server.main.app.openapi()))" > ./openapi.json
openapi-python-client generate --path ./openapi.json --output-path ./client --overwrite
rm openapi.json
