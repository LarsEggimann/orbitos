#!/usr/bin/env bash
set -euo pipefail

# make sure the script is run from the project root directory
cd "$(dirname "$(dirname "$(realpath "$0")")")"

# Make sure Python knows 'backend' is the source directory
export PYTHONPATH="backend"

echo "=================================================="
echo "        Generating Frontend Client"
echo "=================================================="

python3 -c "import json, src.main; print(json.dumps(src.main.app.openapi(), indent=2))" > frontend/openapi.json

(cd frontend && npm run generate-client -- --silent && rm openapi.json)

echo "Frontend client generated successfully!"

# crate variable for backend/src/modules to avoid repeating it
MODULES_DIR="backend/src/modules"      

echo "=================================================="
echo "        Generating Pandora Server API Client"
echo "=================================================="
python3 -c "import json, src.modules.pandora.pandora_server.main; print(json.dumps(src.modules.pandora.pandora_server.main.app.openapi(), indent=2))" > $MODULES_DIR/pandora/openapi.json

openapi-python-client generate \
    --path $MODULES_DIR/pandora/openapi.json \
    --output-path $MODULES_DIR/pandora/pandora_server/client \
    --overwrite
rm $MODULES_DIR/pandora/openapi.json

echo "Pandora Server API client generated successfully!"

echo "=================================================="
echo "        Generating Raspi Server API Client"
echo "=================================================="
python3 -c "import json, src.modules.raspi.raspi_server.main; print(json.dumps(src.modules.raspi.raspi_server.main.app.openapi(), indent=2))" > $MODULES_DIR/raspi/openapi.json

openapi-python-client generate \
    --path $MODULES_DIR/raspi/openapi.json \
    --output-path $MODULES_DIR/raspi/client \
    --overwrite
rm $MODULES_DIR/raspi/openapi.json

echo "Raspi Server API client generated successfully!"

echo "=================================================="
echo "       All clients generated successfully!"
echo "=================================================="