# 🔐 simple-dnssec-watchdog

[![Docker Pulls](https://img.shields.io/docker/pulls/mm28ajos/simple-dnssec-watchdog.svg)](https://hub.docker.com/r/mm28ajos/simple-dnssec-watchdog)
[![Docker Build](https://github.com/mm28ajos/simple-dnssec-watchdog/actions/workflows/build-images.yml/badge.svg)](https://github.com/mm28ajos/simple-dnssec-watchdog/actions/workflows/build-images.yml)
[![Docker Image Size](https://img.shields.io/docker/image-size/mm28ajos/simple-dnssec-watchdog/latest)](https://hub.docker.com/r/mm28ajos/simple-dnssec-watchdog)
[![GitHub Release](https://img.shields.io/github/v/release/mm28ajos/simple-dnssec-watchdog?sort=semver)](https://github.com/mm28ajos/simple-dnssec-watchdog/releases)

A lightweight containerized Flask API that checks whether a given domain is protected by **valid DNSSEC** records using `dig` and a trusted upstream resolver.

This service can be used **standalone** or as an **HTTP(S) healthcheck endpoint for Uptime Kuma**.

## 🔐 How DNSSEC Validation Works

- Uses `dig +dnssec` to query a trusted resolver (like Quad9 or Cloudflare)
- Confirms:
  - `RRSIG` records are present in the answer
  - `ad` (Authenticated Data) flag is set in the response header

This indicates both DNSSEC signing and validation are successful.

---

## 🚀 Features

- ✅ Accepts custom upstream DNS servers
- ✅ Supports Punycode (IDN) domains
- ✅ Configurable timeout
- ✅ `/check` and `/healthz` endpoints
- ✅ IPv6-ready
- ✅ Production-ready with Gunicorn
- ✅ Dockerized with a minimal Alpine image
- ✅ Multi-arch images for `amd64`, `arm64`, and `arm/v7`

---

## 🧪 Example API Usage

```bash
GET /check?domain=cloudflare.com&dns=1.1.1.1&timeout=5
```

### ✅ Parameters

| Parameter | Required | Description                         | Default     | Example           |
|-----------|----------|-------------------------------------|-------------|-------------------|
| `domain`  | ✅       | Domain to validate (IDN supported)  | —           | `cloudflare.com` |
| `dns`     | ❌       | Upstream DNS resolver IP            | `9.9.9.9`   | `1.1.1.1`         |
| `timeout` | ❌       | Query timeout in seconds            | `10`        | `5`               |


### ✅ Successful DNSSEC Response
```json
{
  "status": "valid",
  "domain": "cloudflare.com",
  "ascii_domain": "cloudflare.com",
  "dns": "1.1.1.1",
  "timeout": 5
}
```

### ❌ Failed DNSSEC Response

If a domain is not properly signed with DNSSEC or the upstream resolver does not validate it, you'll receive a `400` response:

```json
{
  "status": "invalid",
  "message": "DNSSEC records are missing or not validated",
  "domain": "example.org",
  "ascii_domain": "example.org",
  "dns": "1.1.1.1",
  "timeout": 10,
  "output": "; <<>> DiG 9.18.1 <<>> +dnssec example.org @1.1.1.1\n;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1\n..."
}
```
> 🛑 **Note:** This means the DNS response was not authenticated via DNSSEC. Either the domain lacks DNSSEC records, or the resolver did not validate them.

## 📡 Kuma Integration (Uptime Kuma)

This container is ideal for monitoring **DNSSEC coverage** using [Uptime Kuma](https://github.com/louislam/uptime-kuma).

You can create a Kuma monitor with the following settings:

- **Type:** HTTP(s)
- **URL:** `http://<container-ip>:8080/check?domain=example.com&dns=9.9.9.9`
- **Expected HTTP Status:** `200`
- **Optional Keyword Match:** `"valid"`

Kuma will mark the monitor **up** only if DNSSEC is successfully validated.

## 🐳 Quickstart with Docker Compose

```yaml
services:
  dnssec-checker:
    image: mm28ajos/simple-dnssec-watchdog:latest
    container_name: dnssec-checker
    restart: unless-stopped
    networks:
      - net_kuma
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3

networks:
  net_kuma:
    external: true
```

Ensure the Docker network exists and kuma monitor is also in that network.


## 📦 DockerHub

You can pull the prebuilt image directly:

```bash
docker pull mm28ajos/simple-dnssec-watchdog
```

### 📦 Available Tags

- **`latest`**: Latest release from the `main` branch or a semver tag (e.g. `1.0.0`)
- **`{version}`**: Tagged releases (e.g. `1.0.0`, `1.1.0`)

**Architecture support:**

- `linux/amd64`
- `linux/arm64`
- `linux/arm/v7`

➡️ [View on Docker Hub](https://hub.docker.com/r/mm28ajos/simple-dnssec-watchdog)

### ⚙️ CI/CD: Build & Publish Logic

This project uses a **GitHub Actions** workflow to automatically:

- ✅ Build the Docker image using [Buildx](https://github.com/docker/buildx) for multiple platforms
- ✅ Tag the image appropriately:
  - If a Git tag matches the pattern `v1.2.3`, it will tag:
    - `mm28ajos/simple-dnssec-watchdog:1.2.3`
    - `mm28ajos/simple-dnssec-watchdog:latest`
- ✅ Push the images to Docker Hub
- ✅ Sync the `README.md` to the Docker Hub repository page

The workflow is triggered:

- On push to the `main` branch
- On new Git tags (e.g. `v1.0.0`)
- On the 1st of every month via cron (`0 4 1 * *`)


---

## 🤝 Contributing

Issues and pull requests are welcome — feel free to improve error handling, support more query types, or extend DNSSEC validation logic!
