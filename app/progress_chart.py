"""A topic map: equal-size sectors, with color encoding practice accuracy."""
from math import cos, pi, sin

STATES = (
    ('focus', 'Focus areas'),
    ('building', 'Building confidence'),
    ('strength', 'Strengths'),
    ('early', 'Early signals'),
    ('unpracticed', 'Not practiced yet'),
)


def topic_chart(lessons, focus):
    stats = dict(focus)
    items = []
    count = len(lessons)
    for index, lesson in enumerate(lessons):
        stat = stats.get(lesson['id'], {'correct': 0, 'total': 0})
        total, correct = stat['total'], stat['correct']
        accuracy = round(100 * correct / total) if total else None
        if not total:
            state = 'unpracticed'
        elif total < 5:
            state = 'early'
        elif correct / total >= .8:
            state = 'strength'
        elif correct / total >= .6:
            state = 'building'
        else:
            state = 'focus'
        label = dict(STATES)[state]
        score = f'{correct}/{total} correct · {accuracy}%' if total else 'No answers yet'
        start, end = 2 * pi * index / count - pi / 2, 2 * pi * (index + 1) / count - pi / 2
        def point(radius, angle):
            return f'{200 + radius * cos(angle):.3f},{200 + radius * sin(angle):.3f}'
        path = (f'M {point(174, start)} A 174,174 0 0 1 {point(174, end)} '
                f'L {point(100, end)} A 100,100 0 0 0 {point(100, start)} Z')
        middle = (start + end) / 2
        items.append({'id': lesson['id'], 'title': lesson['title'], 'number': index + 1,
                      'state': state, 'label': label, 'score': score, 'path': path,
                      'x': 200 + 137 * cos(middle), 'y': 200 + 137 * sin(middle),
                      'total': total})
    groups = [{'state': state, 'label': label, 'items': [item for item in items if item['state'] == state]}
              for state, label in STATES]
    return {'items': items, 'groups': groups, 'practiced': sum(item['total'] > 0 for item in items), 'total': count}
