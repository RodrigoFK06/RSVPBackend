import pytest
import httpx
from app.services import rsvp_service

class DummySession:
    def __init__(self, topic, text, words, user_id=None):
        self.topic = topic
        self.text = text
        self.words = words
        self.user_id = user_id
        self.id = 'dummy'
    async def insert(self):
        pass

@pytest.mark.asyncio
async def test_ask_gemini_for_rsvp_http_error(monkeypatch):
    async def mock_post(self, url, headers=None, json=None):
        request = httpx.Request('POST', url)
        return httpx.Response(status_code=500, request=request)
    monkeypatch.setattr(httpx.AsyncClient, 'post', mock_post)
    monkeypatch.setattr(rsvp_service, 'RsvpSession', DummySession)
    with pytest.raises(Exception) as exc:
        await rsvp_service.ask_gemini_for_rsvp('topic')
    assert 'Error communicating with AI service' in str(exc.value)

@pytest.mark.asyncio
async def test_ask_gemini_for_rsvp_network_error(monkeypatch):
    async def mock_post(self, url, headers=None, json=None):
        request = httpx.Request('POST', url)
        raise httpx.RequestError('boom', request=request)
    monkeypatch.setattr(httpx.AsyncClient, 'post', mock_post)
    monkeypatch.setattr(rsvp_service, 'RsvpSession', DummySession)
    with pytest.raises(Exception) as exc:
        await rsvp_service.ask_gemini_for_rsvp('topic')
    assert 'Network error communicating with AI service' in str(exc.value)

@pytest.mark.asyncio
async def test_ask_gemini_for_rsvp_malformed_response(monkeypatch):
    async def mock_post(self, url, headers=None, json=None):
        request = httpx.Request('POST', url)
        return httpx.Response(status_code=200, json={'invalid': 'data'}, request=request)
    monkeypatch.setattr(httpx.AsyncClient, 'post', mock_post)
    monkeypatch.setattr(rsvp_service, 'RsvpSession', DummySession)
    with pytest.raises(Exception) as exc:
        await rsvp_service.ask_gemini_for_rsvp('topic')
    assert 'Malformed response from AI service' in str(exc.value)
