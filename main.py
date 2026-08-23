"""Thin entry point for the SMTP Test Tool web application.

Usage::

    python main.py
"""

from smtp_tool import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
