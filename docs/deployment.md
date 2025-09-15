# Deployment Guide

This guide describes how to build, run, and configure the NEDC Bench API in Docker Compose and Kubernetes.

## Prerequisites

- Docker and Docker Compose
- Optional: Kubernetes cluster + `kubectl`

## Environment Variables

- `LOG_LEVEL` (default: `INFO`)
- `NEDC_NFC` (default: `/app/nedc_eeg_eval/v6.0.0`)
- `REDIS_URL` (default: `redis://redis:6379` in Compose; cluster DNS in K8s)

## Build and Run (Compose)

```bash
docker-compose build
docker-compose up -d
docker-compose ps
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/metrics
```

## Kubernetes Deployment

```bash
kubectl apply -f k8s/
kubectl get deploy,svc
kubectl rollout status deploy/nedc-bench-api
kubectl port-forward svc/nedc-bench-api 8000:80
curl http://localhost:8000/api/v1/health
```

## Image Build and Tagging

```bash
# API image
docker build -f Dockerfile.api -t nedc-bench/api:latest .
docker run --rm -p 8000:8000 nedc-bench/api:latest
```

## Configuration Matrix

- Compose: `REDIS_URL=redis://redis:6379`; Prometheus scrapes `api:8000`.
- K8s: use cluster DNS (e.g., `redis.default.svc.cluster.local:6379`) if Redis runs in‑cluster.

