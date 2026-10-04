import pytest
import requests

from app.auth import identity


class FakeResponse:
    def __init__(self, status):
        self.status_code = status
        self.ok = 200 <= status < 300


@pytest.fixture
def no_sleep(monkeypatch):
    sleeps = []
    monkeypatch.setattr(identity.time, "sleep", lambda s: sleeps.append(s))
    return sleeps


def _script(monkeypatch, outcomes):
    calls = []

    def fake_post(url, json=None, timeout=None):
        calls.append(url)
        outcome = outcomes[min(len(calls) - 1, len(outcomes) - 1)]
        if isinstance(outcome, Exception):
            raise outcome
        return FakeResponse(outcome)

    monkeypatch.setattr(identity.requests, "post", fake_post)
    return calls


def test_returns_immediately_on_success(monkeypatch, no_sleep):
    calls = _script(monkeypatch, [200])
    assert identity._post("/auth/login", {}).status_code == 200
    assert len(calls) == 1 and no_sleep == []


def test_retries_a_502_then_succeeds(monkeypatch, no_sleep):
    calls = _script(monkeypatch, [502, 200])
    assert identity._post("/auth/login", {}).status_code == 200
    assert len(calls) == 2 and no_sleep == [identity.RETRY_DELAY_SECONDS]


def test_retries_connection_errors(monkeypatch, no_sleep):
    calls = _script(monkeypatch, [requests.ConnectionError(), requests.Timeout(), 200])
    assert identity._post("/auth/login", {}).status_code == 200
    assert len(calls) == 3


def test_gives_up_with_waking_message_after_all_attempts(monkeypatch, no_sleep):
    calls = _script(monkeypatch, [503])
    with pytest.raises(identity.IdentityError) as exc:
        identity._post("/auth/login", {})
    assert str(exc.value) == identity.WAKING_MESSAGE
    assert len(calls) == identity.ATTEMPTS


@pytest.mark.parametrize("status", [400, 401, 409, 500])
def test_does_not_retry_real_answers(monkeypatch, no_sleep, status):
    calls = _script(monkeypatch, [status])
    assert identity._post("/auth/login", {}).status_code == status
    assert len(calls) == 1


def test_invalid_credentials_still_surface_on_401(monkeypatch, no_sleep):
    _script(monkeypatch, [401])
    with pytest.raises(identity.InvalidCredentials):
        identity.authenticate("a@b.co", "wrong")
