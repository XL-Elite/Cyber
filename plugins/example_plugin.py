def run():
    """Example plugin for CyberOS.
    This plugin is intentionally safe and only returns a string.
    Plugins must provide a run() function that returns serializable data.
    """
    return {"status": "ok", "message": "example plugin executed (safe placeholder)"}