"""外部 HTTPS 服务使用的可信证书上下文。"""

import ssl
from pathlib import Path

import certifi


SYSTEM_CA_BUNDLE_CANDIDATES = (
    Path("/etc/pki/tls/certs/ca-bundle.crt"),
    Path("/etc/ssl/certs/ca-certificates.crt"),
)


def create_external_ssl_context() -> ssl.SSLContext:
    """创建同时信任应用证书库和操作系统证书链的 SSL 上下文。

    入参：无。
    返回值：ssl.SSLContext：启用主机名与证书校验的 HTTPS 客户端上下文。
    异常：基础证书库损坏或无法加载时由 Python SSL 模块抛出异常。
    """
    context = ssl.create_default_context(cafile=certifi.where())
    for bundle_path in SYSTEM_CA_BUNDLE_CANDIDATES:
        # CentOS 7 的 curl 可能依赖系统证书链，存在时将其与应用证书库合并。
        if bundle_path.is_file():
            context.load_verify_locations(cafile=str(bundle_path))
    return context
