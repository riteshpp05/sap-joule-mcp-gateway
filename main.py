"""
main.py
-------
ASGI Application Entrypoint.
Delegates to the unified server:app gateway.
"""

from server import app

if __name__ == "__main__":
    import os
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("server:app", host=host, port=port, reload=True)
