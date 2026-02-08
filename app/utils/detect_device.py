def detect_device_type(user_agent:str) -> str:
    if not user_agent:
        return "Unknown"
    ua=user_agent.lower()
    if "ipad" in  ua or "tablet" in ua:
        return "tablet"

    if "mobile" in ua or "android" in ua or "iphone" in ua:
        return "mobile"
    if "windows" in ua or "macintosh" in ua or "linux" in ua:
        return "desktop"
    return "unknown"