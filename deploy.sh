#!/bin/bash
set -e

# Build backend image
docker build -f Dockerfile.backend -t regradar-backend .

# Build frontend image
docker build -f Dockerfile.frontend -t regradar-frontend .

# Start services
docker compose up -d
