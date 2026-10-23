import pytest
from app.security.ssrf_protection import validate_network_target, is_ip_blocked

def test_loopback_and_localhost_blocked():
    assert is_ip_blocked("127.0.0.1") is True
    assert is_ip_blocked("127.0.0.50") is True
    assert is_ip_blocked("::1") is True

    safe, msg, _ = validate_network_target("http://127.0.0.1:8000")
    assert safe is False

    safe_host, _, _ = validate_network_target("http://localhost/admin")
    assert safe_host is False

def test_private_subnets_blocked():
    assert is_ip_blocked("10.10.10.10") is True
    assert is_ip_blocked("172.16.0.1") is True
    assert is_ip_blocked("192.168.1.254") is True

    safe_p1, _, _ = validate_network_target("http://10.0.0.1")
    assert safe_p1 is False

    safe_p2, _, _ = validate_network_target("http://192.168.1.1")
    assert safe_p2 is False

def test_cloud_metadata_blocked():
    assert is_ip_blocked("169.254.169.254") is True

    safe_meta, _, _ = validate_network_target("http://169.254.169.254/latest/meta-data/")
    assert safe_meta is False

    safe_gcp, _, _ = validate_network_target("http://metadata.google.internal/computeMetadata/v1/")
    assert safe_gcp is False

def test_prohibited_schemes_blocked():
    safe_file, msg, _ = validate_network_target("file:///etc/passwd")
    assert safe_file is False
    assert "scheme" in msg.lower()

    safe_ftp, msg_ftp, _ = validate_network_target("ftp://internal-server.local")
    assert safe_ftp is False
