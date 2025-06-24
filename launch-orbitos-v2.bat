@echo off
start firefox http://localhost:3000
cd frontend
cmd /k "npm run win-run:all"
