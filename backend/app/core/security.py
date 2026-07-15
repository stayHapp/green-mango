"""密码哈希、校验和随机会话 token 工具。"""

import base64
import hashlib
import hmac
import secrets

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_BYTES = 32


def hash_password(password: str) -> str:
    """使用 scrypt（内存困难型密码哈希算法）保存密码。

    入参：password 为待哈希明文密码，必填，建议至少 8 个字符。
    返回值：str：包含算法参数、随机盐与哈希结果的可持久化字符串。
    异常：密码为空时抛出 ValueError；系统密码学随机源异常时向上抛出。

    使用示例：`stored = hash_password("example-password")`。
    """
    if not password:
        raise ValueError("密码不能为空。")
    salt = secrets.token_bytes(SALT_BYTES)
    derived_key = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=KEY_BYTES
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii")
    encoded_key = base64.urlsafe_b64encode(derived_key).decode("ascii")
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${encoded_salt}${encoded_key}"


def verify_password(password: str, stored_hash: str) -> bool:
    """校验明文密码与已保存的 scrypt 哈希。

    入参：password 为待校验明文密码；stored_hash 为 `hash_password` 生成的字符串，均必填。
    返回值：bool：参数合法且密码匹配时返回 True，否则返回 False。
    异常：格式、Base64 或算法参数异常均被捕获并返回 False，避免认证接口泄露内部错误。
    """
    try:
        algorithm, n_text, r_text, p_text, encoded_salt, encoded_key = stored_hash.split("$")
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected_key = base64.urlsafe_b64decode(encoded_key.encode("ascii"))
        actual_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n_text),
            r=int(r_text),
            p=int(p_text),
            dklen=len(expected_key),
        )
        return hmac.compare_digest(actual_key, expected_key)
    except (ValueError, TypeError):
        return False


def generate_access_token() -> str:
    """生成适合作为 Bearer 凭证的高熵随机 token。

    入参：无。
    返回值：str：URL 安全的随机 token。
    异常：系统密码学随机源不可用时由 secrets 模块抛出异常。
    """
    return secrets.token_urlsafe(48)


def hash_access_token(token: str) -> str:
    """将访问 token 转换为数据库保存的 SHA-256 摘要。

    入参：token 为客户端提交的原始访问 token，必填。
    返回值：str：64 位十六进制摘要；数据库不保存原始 token。
    异常：token 无法编码为 UTF-8 时由 Python 抛出异常。
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
