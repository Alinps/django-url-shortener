from django.conf import settings

BASE62_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
BASE = len(BASE62_CHARS)

"""converts positive integer to base 62 string"""
def encode_base62(num: int) -> str:
    if num == 0:
        return BASE62_CHARS[0]
    encode = []
    while num>0:
        remainder=num%BASE
        encode.append(BASE62_CHARS[remainder])
        num=num//BASE
    #reverse because we built it backwards
    return "".join(reversed(encode))


def obfuscate_id(num):
    return num ^ settings.SHORTCODE_SECRET