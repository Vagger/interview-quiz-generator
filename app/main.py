import json
import os
import random
import secrets
import sqlite3
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parent.parent
LESSONS = json.loads((ROOT / 'content/lessons.json').read_text())
QUESTIONS = json.loads((ROOT / 'content/questions.json').read_text())
TOPICS = {x['id']: x for x in LESSONS}
assert len({q['id'] for q in QUESTIONS}) == len(QUESTIONS)
assert all(q['topic'] in TOPICS and 0 <= q['answer'] < len(q['options']) for q in QUESTIONS)
app = FastAPI(title='Daily Java')
app.mount('/static', StaticFiles(directory=ROOT / 'app/static'), name='static')
templates = Jinja2Templates(directory=str(ROOT / 'app/templates'))


@contextmanager
def db():
    path = Path(os.environ.get('QUIZ_DB', str(ROOT / 'data/practice.sqlite3')))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, created TEXT NOT NULL, questions TEXT NOT NULL, answers TEXT)')
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def get_session(sid):
    with db() as conn:
        row = conn.execute('SELECT * FROM sessions WHERE id = ?', (sid,)).fetchone()
    if row is None:
        raise HTTPException(404, 'Practice session not found')
    return dict(row)


def render(request, name, **context):
    return templates.TemplateResponse(request=request, name=name, context={'topics': TOPICS, **context})


def summary():
    with db() as conn:
        rows = conn.execute('SELECT * FROM sessions WHERE answers IS NOT NULL ORDER BY created DESC, rowid DESC').fetchall()
    stats = defaultdict(lambda: {'correct': 0, 'total': 0})
    attempts = []
    for row in rows:
        questions, answers = json.loads(row['questions']), json.loads(row['answers'])
        correct = sum(answers[q['id']] == q['answer'] for q in questions)
        attempts.append({**dict(row), 'correct': correct, 'total': len(questions)})
        for q in questions:
            stats[q['topic']]['total'] += 1
            stats[q['topic']]['correct'] += answers[q['id']] == q['answer']
    focus = sorted(stats.items(), key=lambda x: (x[1]['correct'] / x[1]['total'], -x[1]['total']))
    return attempts, focus


@app.get('/')
def home(request: Request):
    attempts, focus = summary()
    return render(request, 'home.html', attempts=attempts, focus=focus)


@app.post('/practice')
async def start(request: Request):
    form = await request.form()
    topic = form.get('topic', '')
    retry = form.get('retry', '')
    if retry:
        old = get_session(retry)
        questions = json.loads(old['questions'])
        if form.get('mistakes') == 'yes':
            if old['answers'] is None:
                raise HTTPException(400, 'Complete the session first')
            answers = json.loads(old['answers'])
            questions = [q for q in questions if answers[q['id']] != q['answer']]
            if not questions:
                raise HTTPException(400, 'No mistakes to retry')
    else:
        if topic and topic not in TOPICS:
            raise HTTPException(400, 'Unknown topic')
        pool = [q for q in QUESTIONS if not topic or q['topic'] == topic]
        # Round-robin across shuffled topics keeps a mixed session balanced.
        groups = defaultdict(list)
        for q in random.sample(pool, len(pool)):
            groups[q['topic']].append(q)
        order = random.sample(list(groups), len(groups))
        questions = []
        while len(questions) < min(10, len(pool)):
            for key in order:
                if groups[key] and len(questions) < 10:
                    questions.append(groups[key].pop())
    sid = secrets.token_urlsafe(24)
    with db() as conn:
        conn.execute('INSERT INTO sessions VALUES (?, ?, ?, NULL)', (sid, datetime.now(timezone.utc).isoformat(timespec='seconds'), json.dumps(questions)))
    return RedirectResponse('/practice/' + sid, status_code=303)


@app.get('/practice/{sid}')
def quiz(request: Request, sid: str):
    session = get_session(sid)
    if session['answers'] is not None:
        return RedirectResponse('/results/' + sid, status_code=303)
    return render(request, 'quiz.html', session=session, questions=json.loads(session['questions']))


@app.post('/practice/{sid}')
async def submit(request: Request, sid: str):
    session = get_session(sid)
    if session['answers'] is not None:
        return RedirectResponse('/results/' + sid, status_code=303)
    form = await request.form()
    answers = {}
    for q in json.loads(session['questions']):
        try:
            value = int(form[q['id']])
            if value < 0 or value >= len(q['options']):
                raise ValueError()
            answers[q['id']] = value
        except (KeyError, ValueError, TypeError):
            raise HTTPException(400, 'Please choose one valid answer for every question. Go back to finish your session.')
    with db() as conn:
        conn.execute('UPDATE sessions SET answers = ? WHERE id = ? AND answers IS NULL', (json.dumps(answers), sid))
    return RedirectResponse('/results/' + sid, status_code=303)


@app.get('/results/{sid}')
def results(request: Request, sid: str):
    session = get_session(sid)
    if session['answers'] is None:
        return RedirectResponse('/practice/' + sid, status_code=303)
    questions, answers = json.loads(session['questions']), json.loads(session['answers'])
    correct = sum(answers[q['id']] == q['answer'] for q in questions)
    stats = defaultdict(lambda: {'correct': 0, 'total': 0})
    for q in questions:
        stats[q['topic']]['total'] += 1
        stats[q['topic']]['correct'] += answers[q['id']] == q['answer']
    return render(request, 'results.html', session=session, questions=questions, answers=answers, correct=correct, stats=stats)


@app.get('/lessons')
def lessons(request: Request):
    return render(request, 'lessons.html', lessons=LESSONS)


@app.get('/lessons/{topic}')
def lesson(request: Request, topic: str):
    if topic not in TOPICS:
        raise HTTPException(404, 'Lesson not found')
    return render(request, 'lesson.html', lesson=TOPICS[topic])


@app.get('/progress')
def progress(request: Request):
    attempts, focus = summary()
    return render(request, 'progress.html', attempts=attempts, focus=focus)
