#!/usr/bin/env -S just --justfile

set default-list := true

mkdocs:
    mkdocs build & sleep 1 & mkdocs gh-deploy

test-cov:
    pytest --cov=sprats --rootdir=src --cov-report=html; xdg-open htmlcov/index.html