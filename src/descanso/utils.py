def ensure_trailing_slash(url: str) -> str:
    if url.endswith("/"):
        return url
    return url + "/"
