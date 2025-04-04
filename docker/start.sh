#!/bin/sh

if [ "$1" = "jupyter" ]; then
  jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=""
else
  uvicorn app.main:app --host=0.0.0.0 --port=8000 --reload
fi
