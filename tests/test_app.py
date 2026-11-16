import json
import sqlite3

import pytest
from fastapi.testclient import TestClient
from app.main import app, QUESTIONS, TOPICS


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('QUIZ_DB', str(tmp_path / 'practice.db'))
    with TestClient(app) as client:
        yield client


def start(client, **data):
    response = client.post('/practice', data=data, follow_redirects=False)
    assert response.status_code == 303
    return response.headers['location']


def stored(path):
    from app.main import get_session
    return get_session(path.rsplit('/', 1)[1])


def test_complete_learning_loop(client):
    assert client.get('/').status_code == 200
    path = start(client)
    session = stored(path)
    questions = json.loads(session['questions'])
    assert len(questions) == 10
    assert len({q['topic'] for q in questions}) == 6
    page = client.get(path).text
    assert 'Finish &amp; review' in page
    assert questions[0]['explanation'] not in page
    answers = {q['id']: str(q['answer']) for q in questions}
    answers[questions[0]['id']] = str((questions[0]['answer'] + 1) % 3)
    response = client.post(path, data=answers)
    assert response.status_code == 200
    assert '9 / 10 correct' in response.text
    assert questions[0]['explanation'] in response.text
    assert '/lessons/' + questions[0]['topic'] in response.text
    assert '1 completed sessions' in client.get('/progress').text
    # Duplicate submit must not overwrite the completed attempt.
    client.post(path, data={q['id']: str(q['answer']) for q in questions})
    assert json.loads(stored(path)['answers']) == {k: int(v) for k, v in answers.items()}
    retry = start(client, retry=session['id'])
    assert stored(retry)['questions'] == session['questions']
    mistakes = start(client, retry=session['id'], mistakes='yes')
    assert [q['id'] for q in json.loads(stored(mistakes)['questions'])] == [questions[0]['id']]
    # New client sees persisted history.
    with TestClient(app) as another:
        assert '9/10 correct' in another.get('/progress').text


def test_validation_and_topic_practice(client):
    path = start(client, topic='concurrency')
    questions = json.loads(stored(path)['questions'])
    assert len(questions) == 3
    assert all(q['topic'] == 'concurrency' for q in questions)
    assert client.post(path, data={}).status_code == 400
    assert stored(path)['answers'] is None
    assert client.post(path, data={q['id']: '-1' for q in questions}).status_code == 400
    assert client.post('/practice', data={'topic': 'unknown'}).status_code == 400
    assert client.get('/practice/missing').status_code == 404
    assert client.get('/lessons/missing').status_code == 404
    for topic in TOPICS:
        assert client.get('/lessons/' + topic).status_code == 200


def test_content_integrity():
    assert len({q['id'] for q in QUESTIONS}) == len(QUESTIONS)
    for q in QUESTIONS:
        assert q['topic'] in TOPICS
        assert q['revision'] >= 1
        assert len(q['options']) == len(set(q['options']))
        assert 0 <= q['answer'] < len(q['options'])
        assert q['explanation']
