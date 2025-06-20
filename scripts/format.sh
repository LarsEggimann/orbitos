#!/bin/sh -e
set -x


# format backend code 
cd backend

ruff check src tests --fix
ruff format src tests


# format frontend code
cd ../frontend
npm run format

cd ..