# Daily Java

A local, single-user Java 21 practice app built with FastAPI, Jinja templates, and SQLite. Take a balanced ten-question quiz, review explanations, study linked lessons, retry mistakes, and revisit saved results.

## Run

Requires Python 3.9+ (a current supported Python release is recommended) and Make.

From the repository directory, run:

```sh
make run
```

This creates the virtual environment, installs dependencies, and starts the app with automatic code reload. No environment activation is needed. Open http://127.0.0.1:8000 and press Ctrl+C in the terminal to stop. No API keys or external services are required. The first setup needs internet access to download dependencies; later runs reuse them.

| Command | Purpose |
| --- | --- |
| `make` or `make help` | List commands |
| `make setup` | Install app dependencies without starting the server |
| `make run` | Set up and start the app |
| `make run PORT=8001` | Use a different local port |
| `make test` | Install test dependencies and run tests |
| `make clean` | Remove the environment and test cache, keeping saved results |

Dependencies are installed again when their requirements files change. To choose a Python interpreter for a new environment, use `make setup PYTHON=python3.12`.

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
make test
```

Tests use temporary SQLite files and do not modify your practice history.
