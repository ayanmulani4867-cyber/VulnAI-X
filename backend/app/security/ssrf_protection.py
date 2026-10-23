import ipaddress
import socket
import urllib.parse
from typing import Tuple, List, Optional
import httpx
import httpcore
from httpcore._backends.anyio import AnyIOBackend
from app.config import settings

# Disallowed IP networks for strict SSRF protection
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
    ipaddress.ip_network("10.0.0.0/8"),         # RFC 1918 Private-use
    ipaddress.ip_network("100.64.0.0/10"),      # Shared Address Space
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-Local (Cloud Metadata: 169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 Private-use
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # Documentation (TEST-NET-1)
    ipaddress.ip_network("192.88.99.0/24"),     # 6to4 Relay Anycast
    ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 Private-use
    ipaddress.ip_network("198.18.0.0/15"),      # Network Interconnect Device Benchmark
    ipaddress.ip_network("198.51.100.0/24"),    # Documentation (TEST-NET-2)
    ipaddress.ip_network("203.0.113.0/24"),     # Documentation (TEST-NET-3)
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved
    ipaddress.ip_network("255.255.255.255/32"), # Limited Broadcast
    # IPv6
    ipaddress.ip_network("::1/128"),            # Loopback
    ipaddress.ip_network("::/128"),             # Unspecified
    ipaddress.ip_network("fe80::/10"),          # Link-local unicast
    ipaddress.ip_network("fc00::/7"),           # Unique local address
    ipaddress.ip_network("ff00::/8"),           # Multicast
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata.internal",
    "instance-data",
    "169.254.169.254"
}

class SSRFSecurityError(Exception):
    """Raised when a target fails SSRF validation or attempts forbidden network access."""
    pass

def is_ip_blocked(ip_str: str) -> bool:
    """
    Returns True if the IP address belongs to a prohibited/internal range.
    Handles IPv4, IPv6, and IPv4-mapped IPv6 addresses.
    """
    if settings.ALLOW_PRIVATE_LAB_TARGETS:
        return False

    try:
        ip = ipaddress.ip_address(ip_str)

        # Built-in RFC property checks
        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return True

        # Check IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
        if ip.version == 6 and ip.ipv4_mapped:
            mapped_v4 = ip.ipv4_mapped
            if mapped_v4.is_loopback or mapped_v4.is_private or mapped_v4.is_link_local or mapped_v4.is_multicast or mapped_v4.is_reserved:
                return True
            for net in BLOCKED_IP_NETWORKS:
                if mapped_v4 in net:
                    return True

        # Check against explicitly blocked networks
        for net in BLOCKED_IP_NETWORKS:
            if ip in net:
                return True

        return False
    except ValueError:
        return True

def resolve_hostname(hostname: str) -> List[str]:
    """Resolves hostname to IP addresses."""
    try:
        addrinfo = socket.getaddrinfo(hostname, None)
        ips = [info[4][0] for info in addrinfo]
        return list(set(ips))
    except (socket.gaierror, socket.herror) as e:
        raise SSRFSecurityError(f"DNS resolution failed for hostname '{hostname}': {str(e)}")

def validate_network_target(url_or_host: str) -> Tuple[bool, str, List[str]]:
    """
    Validates a URL or hostname against SSRF attacks.
    Returns: (is_safe, canonical_url_or_host, resolved_ips)
    Fails closed if IP is blocked or cannot be resolved.
    """
    if not url_or_host:
        return False, "Target cannot be empty", []

    target_url = url_or_host.strip()
    if "://" in target_url:
        parsed = urllib.parse.urlparse(target_url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False, f"Prohibited URL scheme: {parsed.scheme}. Only HTTP/HTTPS permitted.", []
    else:
        target_url = f"https://{url_or_host}"
        parsed = urllib.parse.urlparse(target_url)

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid host in target URL", []

    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES:
        return False, f"Access to restricted hostname '{hostname_lower}' is blocked.", []

    # Lab bypass
    if settings.ALLOW_PRIVATE_LAB_TARGETS:
        return True, target_url, ["127.0.0.1"]

    # Check direct IP addresses
    try:
        direct_ip = ipaddress.ip_address(hostname_lower)
        if is_ip_blocked(str(direct_ip)):
            return False, f"Direct IP '{direct_ip}' belongs to restricted network range. Blocked to prevent SSRF.", [str(direct_ip)]
        return True, target_url, [str(direct_ip)]
    except ValueError:
        pass # Not a raw IP literal, proceed to DNS resolution

    # Resolve and verify all IP addresses
    try:
        ips = resolve_hostname(hostname_lower)
        if not ips:
            return False, f"No IP addresses found for hostname '{hostname_lower}'", []

        for ip in ips:
            if is_ip_blocked(ip):
                return False, f"Target '{hostname_lower}' resolves to restricted IP: {ip}. Blocked to prevent SSRF.", ips

        return True, target_url, ips
    except SSRFSecurityError as e:
        return False, str(e), []

class AntiRebindingNetworkBackend(AnyIOBackend):
    """
    Custom network backend that intercepts socket connections at the TCP layer.
    Pins connections to pre-validated IP addresses, completely preventing DNS rebinding.
    """
    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: Optional[float] = None,
        local_address: Optional[str] = None,
        socket_options = None
    ):
        # 1. Emergency stop check
        if settings.EMERGENCY_STOP:
            raise SSRFSecurityError("Emergency stop is active. Network connection aborted.")

        # 2. Check if host is direct IP
        try:
            ip_obj = ipaddress.ip_address(host)
            if is_ip_blocked(str(ip_obj)):
                raise SSRFSecurityError(f"TCP connection to blocked IP '{host}' rejected.")
            target_connect_ip = str(ip_obj)
        except ValueError:
            # Host is a domain name. Resolve and validate at connection time.
            if host.lower() in BLOCKED_HOSTNAMES:
                raise SSRFSecurityError(f"TCP connection to restricted hostname '{host}' blocked.")

            if not settings.ALLOW_PRIVATE_LAB_TARGETS:
                resolved_ips = resolve_hostname(host)
                if not resolved_ips:
                    raise SSRFSecurityError(f"DNS resolution returned no IPs for '{host}'.")

                for ip in resolved_ips:
                    if is_ip_blocked(ip):
                        raise SSRFSecurityError(
                            f"DNS Rebinding or SSRF detected: Host '{host}' resolved to restricted IP '{ip}' during TCP connect."
                        )
                # Pin to first validated safe IP to eliminate DNS rebinding race conditions
                target_connect_ip = resolved_ips[0]
            else:
                target_connect_ip = host

        return await super().connect_tcp(
            remote_host=target_connect_ip,
            remote_port=port,
            timeout=timeout,
            local_host=local_address,
            socket_options=socket_options
        )

def create_safe_async_client(timeout: int = 15) -> httpx.AsyncClient:
    """Creates an httpx.AsyncClient with AntiRebindingNetworkBackend attached."""
    transport = httpx.AsyncHTTPTransport(verify=True)
    transport._pool._network_backend = AntiRebindingNetworkBackend()
    return httpx.AsyncClient(
        transport=transport,
        follow_redirects=False,
        timeout=timeout
    )

async def safe_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[dict] = None,
    data: Optional[bytes] = None,
    timeout: int = 15,
    max_redirects: int = 5,
    scope_check_fn: Optional[callable] = None
) -> httpx.Response:
    """
    Executes an HTTP request with strict hop-by-hop SSRF and redirect validation.
    Protects against DNS rebinding, internal network scanning, and redirect scope escapes.
    """
    current_url = url
    redirect_count = 0
    client = create_safe_async_client(timeout=timeout)

    try:
        while redirect_count <= max_redirects:
            # 1. Pre-flight SSRF target validation
            is_safe, msg, _ = validate_network_target(current_url)
            if not is_safe:
                raise SSRFSecurityError(f"SSRF violation: {msg}")

            # 2. Redirect scope enforcement check if callback provided
            if scope_check_fn is not None:
                is_authorized, scope_msg = scope_check_fn(current_url)
                if not is_authorized:
                    raise SSRFSecurityError(f"Redirect escaped authorized scope: {scope_msg}")

            # 3. Perform HTTP request via Anti-Rebinding transport
            response = await client.request(
                method=method,
                url=current_url,
                headers=headers,
                content=data
            )

            # 4. Hop-by-hop redirect inspection
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    return response
                next_url = urllib.parse.urljoin(current_url, location)
                current_url = next_url
                redirect_count += 1
                method = "GET"  # Standard redirect behavior
            else:
                return response

        raise SSRFSecurityError(f"Exceeded maximum redirects ({max_redirects})")
    finally:
        await client.aclose()
