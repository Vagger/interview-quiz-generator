# Daily Java

A local, single-user Java 21 practice app built with FastAPI, Jinja templates, and SQLite. Take a balanced ten-question quiz, review explanations, study linked lessons, retry mistakes, and revisit saved results.

## Run

Requires Python 3.9+ (a current supported Python release is recommended).

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1
```

Open http://127.0.0.1:8000. No API keys or external services are required.

## Included

- 18 starter questions across equality/collections, generics, streams, concurrency, exceptions, and runtime semantics.
- Six concise lessons with code, pitfalls, and official Java references.
- Fresh balanced quizzes, exact retakes, topic practice, and mistake-only retries.
- SQLite session history and topic accuracy, including sample counts. Retakes count toward aggregate scores.
- Question snapshots preserve historical explanations and answers when content changes.

This is an initial practice slice, not a comprehensive senior Java assessment. Quiz selection is randomized from authored content; it does not generate questions with AI. The daily button starts a fresh session on every use.

## Content and persistence

Edit `content/questions.json` and `content/lessons.json` to extend the bank. Questions have stable IDs, revisions, a track, Java version, topic, zero-based answer index, and explanations. Keep IDs unique and increment revisions when changing a question. Lessons contain official source links. Restart the app after editing content.

Progress lives in `data/practice.sqlite3` (ignored by Git). Set `QUIZ_DB` to override the location. Back up that file to preserve history; stop the app and delete it to reset. Unsubmitted sessions keep their question selection but not unsubmitted answers.

This version shares one learning history across everyone using the server. Keep it bound to localhost; authentication and per-user history are required before public hosting. Lessons and questions assume Java 21. Other subjects can reuse the content structure, but track selection and Java-specific labels need implementation before adding another audience.

## Verify

```sh
pip install -r requirements-dev.txt
pytest -q
```

Tests use temporary SQLite files and do not modify your practice history.
