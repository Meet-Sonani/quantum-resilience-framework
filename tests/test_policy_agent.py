import json
from dataclasses import dataclass

from quantum_resilience_framework.models import AssetRole, CryptoAsset, Inventory, QuantumVulnerability
from quantum_resilience_framework.policy_agent import build_request, generate_policy_briefing, parse_response


def _sample_inventory() -> Inventory:
    asset = CryptoAsset(
        asset_id="T-01", name="RSA-2048", role=AssetRole.KEY_EXCHANGE,
        location="test fixture", data_sensitivity_years=10, migration_timeline_years=3,
    )
    asset.vulnerability = QuantumVulnerability.BROKEN
    asset.urgency_score = 8
    asset.recommendation = "Recommend ML-KEM-512 (FIPS 203)."
    return Inventory(system_name="Test System", assets=[asset], crqc_horizon_years=15)


def test_build_request_includes_processed_fields_not_raw_reclassification():
    request = build_request(_sample_inventory())

    assert request["model"] == "claude-sonnet-4-6"
    assert "system" in request
    user_content = request["messages"][0]["content"]
    parsed = json.loads(user_content)

    asset_payload = parsed["assets"][0]
    # the agent must receive the pipeline's own numbers, not recompute them
    assert asset_payload["urgency_score"] == 8
    assert asset_payload["vulnerability"] == "broken"
    assert asset_payload["recommendation"] == "Recommend ML-KEM-512 (FIPS 203)."


def test_parse_response_handles_clean_json():
    raw = '{"analysis": "test", "recommendations": []}'
    assert parse_response(raw) == {"analysis": "test", "recommendations": []}


def test_parse_response_strips_accidental_markdown_fence():
    raw = '```json\n{"analysis": "test", "recommendations": []}\n```'
    assert parse_response(raw) == {"analysis": "test", "recommendations": []}


@dataclass
class _FakeTextBlock:
    type: str
    text: str


class _FakeResponse:
    def __init__(self, text: str):
        self.content = [_FakeTextBlock(type="text", text=text)]


class _FakeMessages:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return _FakeResponse(self._response_text)


class _FakeClient:
    def __init__(self, response_text: str):
        self.messages = _FakeMessages(response_text)


def test_generate_policy_briefing_uses_injected_client_and_parses_result():
    fake_response = json.dumps({
        "analysis": "RSA-2048 key exchange is the priority.",
        "recommendations": [
            {"asset_id": "T-01", "priority_rank": 1, "rationale": "Highest urgency score."}
        ],
    })
    client = _FakeClient(fake_response)

    result = generate_policy_briefing(_sample_inventory(), client)

    assert result["recommendations"][0]["asset_id"] == "T-01"
    assert client.messages.last_request["model"] == "claude-sonnet-4-6"
