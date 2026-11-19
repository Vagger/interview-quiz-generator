"""Load and validate the handbook and its linked practice bank."""
import json
from pathlib import Path


def load_content(directory: Path):
    lessons = json.loads((directory / 'lessons.json').read_text())
    questions = json.loads((directory / 'questions.json').read_text())
    topic_ids = [lesson['id'] for lesson in lessons]
    if len(topic_ids) != len(set(topic_ids)):
        raise ValueError('Lesson IDs must be unique')
    question_ids = set()
    prompts = set()
    covered = set()
    for lesson in lessons:
        for field in ('title', 'part', 'level', 'body', 'sections', 'code', 'pitfall', 'source'):
            if not lesson.get(field):
                raise ValueError(f'Missing lesson {field}: {lesson["id"]}')
        section_ids = [s['id'] for s in lesson['sections']]
        if len(set(section_ids)) != len(section_ids):
            raise ValueError(f'Duplicate section IDs: {lesson["id"]}')
        for section in lesson['sections']:
            if not section.get('title') or not section.get('paragraphs'):
                raise ValueError(f'Empty section: {lesson["id"]}')
    for question in questions:
        qid = question['id']
        signature = (question['prompt'], question.get('code', ''))
        if qid in question_ids or signature in prompts:
            raise ValueError(f'Duplicate question ID or prompt: {qid}')
        question_ids.add(qid)
        prompts.add(signature)
        if question['topic'] not in topic_ids:
            raise ValueError(f'Unknown lesson: {qid}')
        covered.add(question['topic'])
        options = question['options']
        if (len(options) < 3 or len(set(options)) != len(options)
                or not all(isinstance(option, str) and option.strip() for option in options)
                or type(question['answer']) is not int
                or not 0 <= question['answer'] < len(options)):
            raise ValueError(f'Invalid options or answer: {qid}')
        if not question.get('explanation') or not question.get('source'):
            raise ValueError(f'Missing explanation or source: {qid}')
        if question.get('revision', 0) < 1:
            raise ValueError(f'Invalid revision: {qid}')
    if set(topic_ids) != covered:
        raise ValueError('Every lesson must have practice questions')
    return lessons, questions
