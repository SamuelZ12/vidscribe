"""Re-run of the `vidscribe` arm with the shipped script (eval/README.md, "Overview sheets: re-run of the `vidscribe` arm").

python3 rerun.py [workers]: builds one folder per video and set under $VSOV/rerun from ship/{tr,frames} (the shipped
script's output) and runs one fresh Codex agent in each. `vidscribe` on the agents' PATH is bin/p4/vidscribe, a wrapper
that appends each call to $VSOV/p4calls.log and runs the shipped script. Earlier answers, logs and keys have mode 000
meanwhile. report() and grade_items() are for after the run.
"""
import json, os, random, re, sys, time
import harness as h

ANS, LOGS, CALLS = f'{h.V}/rerun', f'{h.RUN}/logs-rerun', f'{h.V}/p4calls.log'
HIDE = [f'{h.V}/ans', f'{h.V}/ans6', h.KEYS, h.LOGS, f'{h.RUN}/logs6']
h.SKILL['vidscribe'] = 'SKILL.ship.md'


def folders():
    return [(s, v, f'{s}_{v}_s') for s in h.SETS for v in h.ids(s)]


def jobs(only=None):
    out = []
    for s, v, name in folders():
        if only is not None and name not in only: continue
        folder, qs = f'{ANS}/{name}', h.questions(s, v)
        h.build(folder, 'vidscribe', f'{h.V}/ship/tr/{v}.srt', f'{h.V}/ship/frames/{v}', f'{h.V}/src/{v}.mp4', qs)
        out.append((name, folder, h.prompt('vidscribe', folder, len(qs)), f'{h.V}/bin/p4', 3600, LOGS))
    return out


def report():
    """Per agent, from its logs: pictures that exist and that it was shown, its vidscribe calls with exit codes, leak flags."""
    out = {}
    for s, v, name in folders():
        folder = f'{ANS}/{name}'
        a = h.audit(name, folder, LOGS)
        n = lambda pat: len([f for f in os.listdir(f'{folder}/frames') if re.match(pat, f)])
        calls = []
        for e in h.events(f'{LOGS}/{name}.jsonl'):
            it = e.get('item') or {}
            if e.get('type') == 'item.completed' and it.get('type') == 'command_execution' and re.search(r'vidscribe\b.*--(at|scan)\b', it['command']):
                m = re.match(r"""^\S*sh -lc (['"])(.*)\1$""", it['command'], re.S)
                c = re.sub(r'^rtk (proxy )?', '', m.group(2) if m else it['command'])
                calls.append({'command': c.replace(folder, '<F>'), 'exit': it.get('exit_code')})
        u = a['usage']
        out[name] = {'set': s, 'vid': v, 'overview': n(r'overview_\d+\.jpg$'), 'overview_viewed': a['overview_viewed'],
                     'at_files': n(r'at_.*\.jpg$'), 'at_viewed': a['at_viewed'], 'at_calls': a['at_calls'],
                     'scan_files': n(r'scan_.*\.jpg$'), 'scan_viewed': a['scan_viewed'], 'scan_calls': a['scan_calls'],
                     'images_shown': a['images_shown'], 'unmatched': a['unmatched'], 'files_viewed': a['files_viewed'],
                     'input_tokens': u.get('input_tokens'), 'cached_input_tokens': u.get('cached_input_tokens'),
                     'output_tokens': u.get('output_tokens'), 'other_items': a['other_items'], 'leak': a['leak'], 'calls': calls}
    return out


def grade_items():
    """One item per question, with the agent's answer and the first run's scores of both picture arms on that question."""
    first = json.load(open(f'{h.REPO}/eval/overview/grades.json'))
    items = []
    for s, v, name in folders():
        got = h.answers(name, ANS) or {}
        for q in h.questions(s, v):
            a = got.get(q['qid']) or {}
            ans = a.get('answer')
            items.append({'set': s, 'vid': v, 'name': name, 'qid': q['qid'], 'kind': q['kind'],
                          'answer': ans if isinstance(ans, str) and ans.strip() else 'unknown',
                          'confidence': a.get('confidence'), 'frame': a.get('frame'),
                          'first_run': first[s][v]['vidscribe'][q['qid']]['score'], 'current': first[s][v]['current'][q['qid']]['score'],
                          'prompt': f"Question: {q['question']}\nReference answer: {q['answer']}\nCandidate answer: {ans or 'unknown'}"})
    return items


if __name__ == '__main__':
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    todo = jobs({name for _, _, name in folders() if h.answers(name, ANS) is None})   # a second call redoes folders without answers
    random.Random(1).shuffle(todo)               # mix sets over the run
    print(f'{len(todo)} agents, {workers} at a time', flush=True)
    modes = {p: os.stat(p).st_mode & 0o777 for p in HIDE if os.path.exists(p)}
    for p in modes: os.chmod(p, 0)
    t = time.time()
    try:
        done = h.run_pool(todo, workers)
    finally:
        for p, m in modes.items(): os.chmod(p, m)
    bad = [n for n, rc, s in done if rc != 0 or h.answers(n, ANS) is None]
    print(f'done in {round(time.time() - t)} s; failed or no answers: {bad}')
