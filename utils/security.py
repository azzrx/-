"""密码哈希与校验工具（使用 bcrypt）
"""
import bcrypt


def hash_password(password: str) -> str:
    """使用 bcrypt 对明文密码进行哈希，返回 utf-8 字符串"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """验证明文密码与 bcrypt 哈希是否匹配"""
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    try:
        return bcrypt.checkpw(password, hashed)
    except ValueError:
        return False
