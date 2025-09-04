from openworld_specialty_chemicals.agents.fake_agent import FakeAdviceAgent


def test_fake_advice_agent():
    agent = FakeAdviceAgent()
    alerts = [
        {"species": "SO4", "value": 260.0, "limit": 250.0},
        {"species": "As", "value": 0.02, "limit": 0.01}
    ]
    result = agent.advise(alerts)
    assert "actions" in result
    assert "rationale" in result
    assert len(result["actions"]) > 0
    assert any("SO4" in action for action in result["actions"])
    assert any("As" in action for action in result["actions"])


def test_fake_advice_agent_empty_alerts():
    agent = FakeAdviceAgent()
    result = agent.advise([])
    assert result["actions"] == ["Check process"]
    assert "rationale" in result
