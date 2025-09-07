from openworld_specialty_chemicals.logging import uvicorn_log_config


def test_uvicorn_log_config_json():
    cfg = uvicorn_log_config(True)
    assert isinstance(cfg, dict)
    assert cfg.get("formatters", {}).get("json") is not None
    assert "uvicorn.access" in cfg.get("loggers", {})

def test_uvicorn_log_config_text():
    cfg = uvicorn_log_config(False)
    assert cfg == {}

