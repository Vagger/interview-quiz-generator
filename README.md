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

- 192 questions across 32 Java chapters, including code-reading exercises and practical scenarios.
- A searchable handbook in six parts, with chapter sections, worked examples, pitfalls, official references, and previous/next navigation.
- Fresh quizzes that prioritize unseen and less-practiced questions, balance topic coverage, and shuffle answer choices. Exact retakes preserve their original questions and choice order. Chapter practice and mistake-only retries are also available.
- SQLite session history and topic accuracy, including sample counts. Retakes count toward aggregate scores.
- Question snapshots preserve historical explanations and answers when content changes.

The handbook covers language foundations, data and functional Java, the standard library and persistence, concurrency, JVM diagnostics, and application engineering. It is a broad study companion, not an exhaustive Java specification or a seniority certification. Quiz selection is randomized from authored content; it does not generate questions with AI. The daily button starts a fresh session on every use.

## Content and persistence

Edit `content/questions.json` and `content/lessons.json` to extend the bank. Questions have stable IDs, revisions, a track, Java version, topic, zero-based answer index, and explanations. Keep IDs unique and increment revisions when changing a question. Lessons contain official source links. Restart the app after editing content. Each lesson has a part, level, ordered sections, example, pitfall, and official source; every lesson must have linked questions. Questions can include an optional `code` snippet. Content validation runs at startup and in tests.

Progress lives in `data/practice.sqlite3` (ignored by Git). Set `QUIZ_DB` to override the location. Back up that file to preserve history; stop the app and delete it to reset. Unsubmitted sessions keep their question selection but not unsubmitted answers.

This version shares one learning history across everyone using the server. Keep it bound to localhost; authentication and per-user history are required before public hosting. Lessons and questions assume Java 21. Other subjects can reuse the content structure, but track selection and Java-specific labels need implementation before adding another audience.

## Verify

```sh
make test
```

Tests use temporary SQLite files and do not modify your practice history.

## Handbook coverage

1. **Language foundations:** types and numeric precision, strings, object semantics, object-oriented design, exceptions, records/enums/sealed types, and pattern matching.
2. **Data and functional Java:** collection choices, equality, generics, lambdas, streams, collectors, and Optional.
3. **Standard library and persistence:** dates and clocks, file I/O, HTTP clients, JDBC transactions, serialization and DTOs.
4. **Concurrency:** visibility and atomics, locks, executors and interruption, CompletableFuture, and Java 21 virtual threads.
5. **JVM and diagnostics:** bytecode and class loading, memory and garbage collection, profiling and JFR.
6. **Reliable applications:** testing, reflection and annotations, modules, builds and API design, and security.

Freshness uses completed attempts from the shared local history. Questions with fewer prior exposures are preferred, with random tie-breaking and topic variety. Starting an unfinished session does not mark its questions as practiced. Retakes count as exposure. Correct answers are remapped when choices shuffle and stored in the session snapshot.

The integration tests cover every chapter’s practice flow, search and filtering, correct-answer preservation after shuffling, saved-session retakes, and progression through the question bank without early repeats.
