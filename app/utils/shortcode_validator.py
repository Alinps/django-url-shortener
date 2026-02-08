import re

SHORT_CODE_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
RESERVED_CODES = {"admin", "login", "signup", "dashboard", "api"}

def is_valid_custom_code(code: str) -> bool:
    if not SHORT_CODE_REGEX.match(code):
        return False
    if code.lower() in RESERVED_CODES:
        return False
    return True