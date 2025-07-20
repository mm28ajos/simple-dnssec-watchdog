#!/usr/bin/env python3

import sys
import re
import signal
import logging
import subprocess
import ipaddress
import idna
from flask import Flask, request, jsonify, Response
from threading import Event
from typing import Optional, Tuple

app = Flask(__name__)
DEFAULT_DNS = "9.9.9.9"
DEFAULT_TIMEOUT = 10
shutdown_event = Event()

# ─── Graceful Shutdown ────────────────────────────────────────────────────────
def handle_shutdown(signum: int, frame) -> None:
    logging.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_event.set()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# ─── Helper Functions ─────────────────────────────────────────────────────────

def is_valid_ip(address: str) -> bool:
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False

def convert_and_validate_domain(domain: str) -> Optional[str]:
    try:
        ascii_domain = idna.encode(domain).decode("ascii")
        if 1 <= len(ascii_domain) <= 253 and '.' in ascii_domain:
            return ascii_domain
        return None
    except idna.IDNAError:
        return None

def check_dnssec(domain_ascii: str, upstream_dns: str, timeout: int = DEFAULT_TIMEOUT) -> Tuple[str, str]:
    try:
        proc = subprocess.run(
            ["dig", "+dnssec", domain_ascii, f"@{upstream_dns}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            text=True
        )
        output = proc.stdout
        has_ad_flag = re.search(r';;\s*flags:.*\bad\b', output, re.IGNORECASE)
        has_rrsig = re.search(r'^\S+\s+\d+\s+IN\s+RRSIG', output, re.MULTILINE)
        if has_ad_flag and has_rrsig:
            return "valid", output
        else:
            return "invalid", output
    except subprocess.TimeoutExpired:
        return "timeout", "Timeout: DNSSEC check exceeded timeout limit"
    except Exception as e:
        logging.exception("DNSSEC check failed")
        return "error", str(e)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/check")
def check() -> Tuple[Response, int]:
    domain_input = request.args.get("domain")
    upstream_dns = request.args.get("dns", DEFAULT_DNS)
    timeout_param = request.args.get("timeout", str(DEFAULT_TIMEOUT))

    if not domain_input:
        return jsonify({"error": "Missing 'domain' query parameter"}), 400

    try:
        timeout = int(timeout_param)
        if timeout <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({"error": f"Invalid timeout value: {timeout_param}"}), 400

    domain_ascii = convert_and_validate_domain(domain_input)
    if not domain_ascii:
        return jsonify({"error": f"Invalid domain name: {domain_input}"}), 400

    if not is_valid_ip(upstream_dns):
        return jsonify({"error": f"Invalid DNS server IP: {upstream_dns}"}), 400

    status, output = check_dnssec(domain_ascii, upstream_dns, timeout)

    if status == "valid":
        return jsonify({
            "status": "valid",
            "domain": domain_input,
            "ascii_domain": domain_ascii,
            "dns": upstream_dns,
            "timeout": timeout
        }), 200

    elif status == "invalid":
        return jsonify({
            "status": "invalid",
            "message": "DNSSEC records are missing or not validated",
            "domain": domain_input,
            "ascii_domain": domain_ascii,
            "dns": upstream_dns,
            "timeout": timeout,
            "output": output
        }), 400

    elif status == "timeout":
        return jsonify({
            "status": "error",
            "message": "DNSSEC validation timed out",
            "domain": domain_input,
            "ascii_domain": domain_ascii,
            "dns": upstream_dns,
            "timeout": timeout,
            "output": output
        }), 504

    else:  # system error
        return jsonify({
            "status": "error",
            "message": "DNSSEC validation failed due to system error",
            "domain": domain_input,
            "ascii_domain": domain_ascii,
            "dns": upstream_dns,
            "timeout": timeout,
            "output": output
        }), 500

@app.route("/healthz")
def health() -> Tuple[str, int]:
    return "OK", 200

# ─── Main Entrypoint ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starting DNSSEC Checker Flask Server")
    app.run(host="::", port=8080, use_reloader=False)
