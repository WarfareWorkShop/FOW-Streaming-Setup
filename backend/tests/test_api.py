from __future__ import annotations

from typing import Any

import pytest


def test_chat_requires_auth(client):
    response = client.post('/api/chat', json={'message': 'Hola'})
    assert response.status_code == 401


def test_chat_returns_ai_response(client, auth_headers, monkeypatch):
    monkeypatch.setattr('backend.app.generate_ai_response', lambda *args, **kwargs: 'Victoria asegurada')

    response = client.post('/api/chat', json={'message': 'hola', 'provider': 'openai'}, headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()['response'] == 'Victoria asegurada'


def test_chat_rejects_long_message(client, auth_headers):
    payload = {'message': 'a' * 5001}
    response = client.post('/api/chat', json=payload, headers=auth_headers)
    assert response.status_code == 413


def test_scenario_advice_endpoint(client, auth_headers, monkeypatch):
    monkeypatch.setattr('backend.tactics.generate_ai_response', lambda *args, **kwargs: 'Usa humo defensivo')

    response = client.post(
        '/api/tactics/scenario-advice',
        json={
            'battleState': {
                'turn': '3',
                'player': 'Aliados',
                'objective': 'Controlar el puente',
                'enemyDisposition': 'Tigres en la colina',
                'weather': 'Lluvioso',
                'terrain': 'Bosques densos',
                'units': [{'name': 'Sherman', 'role': 'Blindados', 'strength': '4 tanques'}],
            }
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert 'Usa humo defensivo' in response.get_json()['analysis']


def test_battle_log_lifecycle(client, auth_headers):
    create_response = client.post(
        '/api/tactics/logs',
        json={
            'title': 'Operación Market Garden',
            'scenario': 'Defensa nocturna',
            'entries': [
                {'timestamp': '2024-01-01T00:00:00Z', 'source': 'voice', 'content': 'Iniciar bombardeo'},
            ],
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 201

    list_response = client.get('/api/tactics/logs', headers=auth_headers)
    assert list_response.status_code == 200
    logs = list_response.get_json()['logs']
    assert logs and logs[0]['title'] == 'Operación Market Garden'

    delete_response = client.delete(f"/api/tactics/logs/{logs[0]['id']}", headers=auth_headers)
    assert delete_response.status_code == 200

    final_response = client.get('/api/tactics/logs', headers=auth_headers)
    assert final_response.status_code == 200
    assert final_response.get_json()['logs'] == []
