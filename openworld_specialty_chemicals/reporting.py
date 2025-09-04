from __future__ import annotations
from typing import List, Dict


def generate_certificate(alerts: List[Dict], site: str) -> str:
    compliant = len(alerts) == 0
    status = "COMPLIANT" if compliant else "NON-COMPLIANT"
    rows = "".join(
        f"<tr><td>{a.get('time','')}</td><td>{a.get('species','')}</td><td>{a.get('value','')}</td><td>{a.get('limit','')}</td></tr>"
        for a in alerts
    )
    html = f"""
<!doctype html>
<html><head><meta charset=\"utf-8\"><title>Compliance Certificate</title></head>
<body>
<h1>Compliance Certificate</h1>
<p>Site: {site}</p>
<h2>Status: {status}</h2>
<table><tr><th>Time</th><th>Species</th><th>Value</th><th>Limit</th></tr>{rows}</table>
</body></html>
"""
    return html

