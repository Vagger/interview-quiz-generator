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
    assert len({q['topic'] for q in questions}) == 10
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
    assert len(questions) == 6
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


def test_handbook_search_navigation_and_chapter_practice(client):
    page = client.get('/lessons')
    assert page.status_code == 200
    for topic, lesson in TOPICS.items():
        assert '/lessons/' + topic in page.text
        detail = client.get('/lessons/' + topic)
        assert lesson['sections'][0]['title'] in detail.text
        path = start(client, topic=topic)
        questions = json.loads(stored(path)['questions'])
        expected = [q for q in QUESTIONS if q['topic'] == topic]
        assert len(questions) == min(10, len(expected))
        assert {q['id'] for q in questions} == {q['id'] for q in expected}
        assert any(q.get('code') for q in questions)
        assert '42' in detail.text or 'Worked example' in detail.text
    search = client.get('/lessons', params={'q': 'deadlock'})
    assert '/lessons/locks' in search.text
    assert '/lessons/strings' not in search.text
    empty = client.get('/lessons', params={'q': 'no-such-java-concept-12345'})
    assert 'No chapters found' in empty.text
    part = TOPICS['types']['part']
    filtered = client.get('/lessons', params={'part': part})
    assert '/lessons/types' in filtered.text
    assert '/lessons/jdbc' not in filtered.text
    assert '&lt;script&gt;' in client.get('/lessons', params={'q': '<script>'}).text


def test_freshness_and_shuffled_answer_integrity(client):
    canonical = {q['id']: q for q in QUESTIONS}
    seen = set()
    # Every question remains unseen during these first nineteen full sessions.
    for _ in range(len(QUESTIONS) // 10):
        path = start(client)
        questions = json.loads(stored(path)['questions'])
        assert len({q['topic'] for q in questions}) == 10
        ids = {q['id'] for q in questions}
        assert len(ids) == 10
        assert not seen.intersection(ids)
        seen.update(ids)
        for q in questions:
            original = canonical[q['id']]
            assert q['options'][q['answer']] == original['options'][original['answer']]
            assert set(q['options']) == set(original['options'])
        response = client.post(path, data={q['id']: str(q['answer']) for q in questions})
        assert '10 / 10 correct' in response.text
    # Exhausting unseen questions still produces a full, nonduplicated session.
    path = start(client)
    questions = json.loads(stored(path)['questions'])
    assert len({q['id'] for q in questions}) == 10
    assert set(canonical) - seen <= {q['id'] for q in questions}


def test_invalid_content_rejected(tmp_path):
    from app.content import load_content
    from app.main import ROOT
    lessons = json.loads((ROOT / 'content/lessons.json').read_text())
    questions = json.loads((ROOT / 'content/questions.json').read_text())
    (tmp_path / 'lessons.json').write_text(json.dumps(lessons))
    questions[0]['topic'] = 'missing'
    (tmp_path / 'questions.json').write_text(json.dumps(questions))
    with pytest.raises(ValueError, match='Unknown lesson'):
        load_content(tmp_path)


def test_topic_chart_signals_and_lesson_links(client):
    from app.main import LESSONS
    from app.progress_chart import topic_chart
    signals = [('types', {'correct': 4, 'total': 5}),
               ('strings', {'correct': 3, 'total': 5}),
               ('runtime', {'correct': 0, 'total': 5}),
               ('generics', {'correct': 1, 'total': 1})]
    chart = topic_chart(LESSONS, signals)
    by_id = {item['id']: item for item in chart['items']}
    assert by_id['types']['state'] == 'strength'
    assert by_id['strings']['state'] == 'building'
    assert by_id['runtime']['state'] == 'focus'
    assert by_id['generics']['state'] == 'early'
    assert by_id['jdbc']['state'] == 'unpracticed'
    assert chart['practiced'] == 4
    assert sum(len(group['items']) for group in chart['groups']) == len(LESSONS)
    empty = client.get('/progress')
    assert empty.status_code == 200
    assert 'Complete a quiz' in empty.text
    assert empty.text.count('class="topic-sector ') == len(LESSONS)
    for topic in TOPICS:
        assert 'href="/lessons/' + topic + '"' in empty.text
    path = start(client, topic='types')
    questions = json.loads(stored(path)['questions'])
    client.post(path, data={q['id']: str(q['answer']) for q in questions})
    page = client.get('/progress')
    assert 'Strengths · 6/6 correct · 100%' in page.text
    assert '1/32' in page.text
