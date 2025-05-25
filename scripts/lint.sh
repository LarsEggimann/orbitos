#!/usr/bin/env bash

set -e
set -x

# format backend code 
cd backend

mypy src
ruff check src tests
ruff format src tests --check

# format frontend code
cd ../frontend
# TODO

cd ..
