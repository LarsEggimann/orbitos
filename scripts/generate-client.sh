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
# npx biome format --write ./app/client
