#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker build -f docker/Dockerfile -t instock:local .
