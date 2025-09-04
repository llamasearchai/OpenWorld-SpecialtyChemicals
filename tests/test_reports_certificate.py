from openworld_specialty_chemicals.reports.certificate import generate_certificate

def test_generate_certificate(tmp_path):
    out = tmp_path / "c.html"
    alerts = [{"species":"SO4","type":"exceedance","level":"warning","value":260.0,"limit":250.0,"action":"do something"}]
    path = generate_certificate(alerts, site="Plant A", out_path=str(out))
    s = out.read_text()
    assert "Compliance Certificate" in s and "Plant A" in s and path == str(out)


