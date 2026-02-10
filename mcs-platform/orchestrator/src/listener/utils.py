"""Listener utilities."""
import pickle
import codecs
import base64

def normalize_message_id(message_id: str) -> str:
    """Normalize RFC 5322 Message-ID by stripping angle brackets.

    Message-ID in headers may appear as '<local@domain>'. For consistent
    storage and lookup we use the inner value (no brackets).
    """
    if not message_id or not isinstance(message_id, str):
        return message_id or ""
    s = message_id.strip()
    if len(s) >= 2 and s.startswith("<") and s.endswith(">"):
        return s[1:-1].strip()
    return s

def encode_special_data(data):
    """编码包含特殊字符的数据"""
    # 先pickle序列化，再base64编码
    pickled = pickle.dumps(data)
    encoded = base64.b64encode(pickled).decode('utf-8')
    return encoded

def decode_special_data(encoded_str):
    """解码base64编码的数据"""
    decoded = base64.b64decode(encoded_str)
    return pickle.loads(decoded)