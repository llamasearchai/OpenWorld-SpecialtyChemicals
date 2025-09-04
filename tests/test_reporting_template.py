from openworld_specialty_chemicals.reporting import generate_certificate


def test_generate_certificate_template_renders():
    html = generate_certificate([
        {"time": 0, "species": "SO4", "value": 5, "limit": 1}
    ], site="Plant A")
    assert "Compliance Certificate" in html and "Plant A" in html and "SO4" in html


