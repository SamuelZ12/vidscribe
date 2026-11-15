"""Harness for the overview-sheets eval (eval/README.md, "Overview sheets").

Builds one folder per video, set and arm under $VSOV/ans, runs one fresh Codex agent in each
(`codex exec`), and reads what each agent opened and ran from its JSONL log.
Layout expected under $VSOV (default /tmp/vsov): src/<ID>.mp4, new/{tr,frames}, cur/{tr,frames}
(runs of the branch script and of master's), bin/p1/vidscribe (branch), bin/p2/vidscribe (master),
SKILL.new.md, SKILL.master.md.
"""
import base64, concurrent.futures as cf, glob, hashlib, json, os, random, re, shutil, subprocess, time

V = os.environ.get('VSOV', '/tmp/vsov')
RUN = os.path.expanduser('~/.cache/vsov-run')   # logs and keys live outside /tmp, which the agents' sandbox can write
LOGS, KEYS = f'{RUN}/logs', f'{RUN}/keys'
REPO = os.environ.get('VSREPO') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL, EFFORT = 'gpt-6.1-sol', 'medium'
SETS = {'clips': 'eval/clips/questions', 'main': 'eval/questions', 'hard': 'eval/hard/questions'}
ARMS = ('transcript', 'vidscribe', 'current')
SRC = {'transcript': 'new', 'vidscribe': 'new', 'current': 'cur'}      # whose run feeds the folder
BIN = {'transcript': None, 'vidscribe': 'p1', 'current': 'p2'}         # which script is `vidscribe`
SKILL = {'vidscribe': 'SKILL.new.md', 'current': 'SKILL.master.md'}


def ids(set_):
    return [l.strip() for l in open(f"{V}/{'clips' if set_ == 'clips' else 'long'}.ids") if l.strip()]


def secs(t):
    if isinstance(t, (int, float)): return float(t)
    s = 0.0
    for p in str(t).split(':'): s = s * 60 + float(p)
    return s


def questions(set_, vid):
    """Questions with references, in one shape: qid, kind, question, answer, time_s, visible_s."""
    q = json.load(open(f'{REPO}/{SETS[set_]}/{vid}.json'))
    out = []
    for x in (q['questions'] if isinstance(q, dict) else q):
        kind = x.get('kind') or ('hard' if set_ == 'hard' else 'visual' if x['qid'].startswith('v') else x['qid'])
        t = secs(x['time_s'] if 'time_s' in x else x['time'])
        out.append({'qid': x['qid'], 'kind': kind, 'question': x['question'], 'answer': x['answer'],
                    'time_s': t, 'visible_s': x.get('visible_s') or [t, t]})
    return out


def skill_body(arm):
    s = open(f'{V}/{SKILL[arm]}').read()
    return s[s.index('# vidscribe'):].rstrip()


PROMPT_TRANSCRIPT = '''# Goal
You are testing how well an AI agent can answer questions about a video using only its transcript. Answer honestly from your folder; a wrong guess is worse than "unknown".

# Your folder: {F}/
- transcript.srt: the full timestamped transcript.
- questions.json: {N} questions.

# Rules
- Use ONLY the files inside your folder. Do not open anything else under {V}, do not search the web, do not open any video or image.
- Answer each question. If the transcript does not give the answer, answer exactly "unknown". Do not guess from general knowledge.

# Output
Write {F}/answers.json: a JSON list of {{"qid", "question", "answer", "frame": null, "confidence": "high"|"low"}}.
'''

PROMPT_SKILL = '''# Goal
You are testing how well an AI agent can answer questions about a video using the vidscribe skill below. vidscribe has already been run on the video (step 1 is done) and its output is in your folder. Answer honestly from your folder; a wrong guess is worse than "unknown".

# Your folder: {F}/
- transcript.srt: the full timestamped transcript.
- frames/: the run's frames folder (`<dir>` in the skill): index.txt, {WHAT}, and video.mp4. Do not open video.mp4 directly; use the skill's vidscribe commands.
- questions.json: {N} questions.

# The vidscribe skill
{SKILL}

# Rules
- Use ONLY files inside your folder and the `vidscribe {F}/frames --at` and `--scan` commands. Do not open anything else under {V}, do not search the web, do not run ffmpeg or any other tool on the video.
- Answer each question. If the frames and transcript do not show the answer, answer exactly "unknown". Do not guess from general knowledge.

# Output
Write {F}/answers.json: a JSON list of {{"qid", "question", "answer", "frame": "<file name you used, or null>", "confidence": "high"|"low"}}.
In your final message, state how many of the {ORIG} you viewed out of how many exist, how many extra frames you extracted and viewed, and how many scan sheets you viewed.
'''


def frames_desc(arm, fdir):
    """The folder line's description of the default pictures, with the folder's real counts."""
    if arm == 'vidscribe':
        sheets = len(glob.glob(f'{fdir}/overview_*.jpg'))
        tiles = sum(1 for _ in open(f'{fdir}/index.txt'))
        return f'the overview sheets ({sheets} sheets, {tiles} tiles)', 'overview sheets'
    n = len([f for f in glob.glob(f'{fdir}/*.jpg') if not re.match(r'(at|scan)_', os.path.basename(f))])
    return f'the frames ({n})', 'original frames'


def prompt(arm, folder, nq, fdir=None):
    if arm == 'transcript':
        return PROMPT_TRANSCRIPT.format(F=folder, N=nq, V=V)
    what, orig = frames_desc(arm, fdir or f'{folder}/frames')
    return PROMPT_SKILL.format(F=folder, N=nq, V=V, WHAT=what, ORIG=orig, SKILL=skill_body(arm))


def build(folder, arm, srt, frames_src, video, qs):
    """A fresh answer folder: transcript, the arm's frames folder with its own copy of the video, questions."""
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder)
    shutil.copy(srt, f'{folder}/transcript.srt')
    if arm != 'transcript':
        os.makedirs(f'{folder}/frames')
        for f in os.listdir(frames_src):
            if not f.startswith('video.'): shutil.copy(f'{frames_src}/{f}', f'{folder}/frames/{f}')
        subprocess.run(['cp', '-c', video, f'{folder}/frames/video.mp4'], check=True)  # APFS clone: no extra space
    json.dump([{'qid': q['qid'], 'question': q['question']} for q in qs], open(f'{folder}/questions.json', 'w'),
              ensure_ascii=False, indent=1)


def run_agent(name, folder, text, bindir=None, timeout=3600, logdir=None):
    """One fresh Codex agent in `folder`. Returns (name, exit code, seconds)."""
    logdir = logdir or LOGS
    os.makedirs(logdir, exist_ok=True)
    env = dict(os.environ)
    # Codex runs commands as `/bin/zsh -lc`. With the owner's profile the login shell puts ~/.local/bin (the installed
    # vidscribe) ahead of bindir, as in the first 2026-11-15 run; an empty ZDOTDIR makes it skip the profile.
    # See eval/README.md, "Overview sheets".
    if bindir:
        os.makedirs(f'{V}/zdot', exist_ok=True)
        env['PATH'], env['ZDOTDIR'] = f'{bindir}:{env["PATH"]}', f'{V}/zdot'
    cmd = ['codex', 'exec', '--ignore-user-config', '-m', MODEL, '-c', f'model_reasoning_effort="{EFFORT}"',
           '-s', 'workspace-write', '-C', folder, '--skip-git-repo-check', '--json', '--color', 'never',
           '-o', f'{logdir}/{name}.final.md', '-']
    t = time.time()
    with open(f'{logdir}/{name}.jsonl', 'w') as out, open(f'{logdir}/{name}.err', 'w') as err:
        try:
            rc = subprocess.run(cmd, input=text.encode(), stdout=out, stderr=err, env=env, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            rc = -9
    # the --json stream leaves out image views; the session file has them. Move it next to the log, so that
    # later agents cannot read it in ~/.codex/sessions
    tid = next((e.get('thread_id') for e in events(f'{logdir}/{name}.jsonl') if e.get('type') == 'thread.started'), None)
    for f in glob.glob(os.path.expanduser(f'~/.codex/sessions/*/*/*/rollout-*-{tid}.jsonl')) if tid else []:
        shutil.move(f, f'{logdir}/{name}.session.jsonl')
    return name, rc, round(time.time() - t)


def events(path):
    for l in open(path):
        try: yield json.loads(l)
        except ValueError: pass


def run_pool(jobs, workers=8):
    """jobs: (name, folder, prompt, bindir). Prints one line per finished agent, as each finishes."""
    done = []
    with cf.ThreadPoolExecutor(workers) as ex:
        for fut in cf.as_completed([ex.submit(run_agent, *j) for j in jobs]):
            name, rc, s = fut.result()
            done.append((name, rc, s)); print(f'{name}\trc={rc}\t{s}s', flush=True)
    return done


def audit(name, folder, logdir=None):
    """What one agent did, from its logs: images it was shown (matched to files by content), commands, tokens."""
    logdir = logdir or LOGS
    disk = {}
    for f in glob.glob(f'{folder}/**/*', recursive=True):
        if os.path.isfile(f) and not f.endswith('.mp4'):
            disk.setdefault(hashlib.sha256(open(f, 'rb').read()).hexdigest(), os.path.relpath(f, folder))
    viewed, scripts = [], []
    sess = f'{logdir}/{name}.session.jsonl'
    for e in events(sess) if os.path.exists(sess) else []:
        p = e.get('payload') or {}
        if p.get('type') in ('custom_tool_call', 'function_call'):
            scripts.append(str(p.get('input') or p.get('arguments') or ''))
        if p.get('type') in ('custom_tool_call_output', 'function_call_output'):
            out = p.get('output')
            if isinstance(out, str):
                try: out = json.loads(out)
                except ValueError: out = []
            for part in out if isinstance(out, list) else []:
                if isinstance(part, dict) and part.get('type') == 'input_image':
                    b = base64.b64decode(part['image_url'].split(',', 1)[1])
                    viewed.append(disk.get(hashlib.sha256(b).hexdigest(), '?'))
    cmds, usage, other = [], {}, []
    for e in events(f'{logdir}/{name}.jsonl'):
        it = e.get('item') or {}
        if e.get('type') == 'item.completed' and it.get('type') == 'command_execution':
            c = it['command']
            m = re.match(r"""^\S*sh -lc (['"])(.*)\1$""", c, re.S)
            cmds.append(re.sub(r'^rtk (proxy )?', '', m.group(2) if m else c))
        elif e.get('type') == 'item.completed' and it.get('type') not in ('agent_message', 'reasoning', 'file_change', 'todo_list'):
            other.append(it.get('type'))
        if e.get('type') == 'turn.completed': usage = e.get('usage') or {}
    base = lambda v: os.path.basename(v)
    uniq = sorted(set(viewed))
    kind = lambda pat: [v for v in uniq if re.match(pat, base(v))]
    # anything that reaches outside the folder, touches the video without vidscribe, or leaves the machine
    own = re.escape(folder.rstrip('/'))
    strip = lambda c: re.sub(rf'{own}|{re.escape(V)}/bin/p\d/vidscribe', '', c)
    outside = r'/tmp\b|/Users/|/var/|/private/|/Volumes/|(^|[\s"\'=(])~|\$HOME|\$\{HOME|\.\.(/|\s|$)|\bcd\s+/|\bfind\s+/'
    leak = [c for c in cmds if re.search(outside, strip(c))
            or re.search(r'\b(ffmpeg|ffprobe|curl|wget|yt-dlp|mdfind|locate)\b|(^|&&|;|\|)\s*open\s', c)
            or (re.search(r'video\.mp4', c) and not re.search(r'^\s*ls\b', c))]
    # images opened from scripts: every quoted picture or video path must sit in the folder
    for s in scripts:
        for p in re.findall(r'''["'`]([^"'`\n]*\.(?:jpe?g|png|webp|gif|mp4))["'`]''', s):
            if re.search(outside, strip(p)) or p.endswith('.mp4'): leak.append(f'script path: {p}')
    return {'images_shown': len(viewed), 'files_viewed': uniq, 'unmatched': viewed.count('?'),
            'overview_viewed': len(kind(r'overview_\d+\.jpg$')), 'orig_viewed': len(kind(r'\d{3}_.*\.jpg$')),
            'at_viewed': len(kind(r'at_.*\.jpg$')), 'scan_viewed': len(kind(r'scan_.*\.jpg$')),
            'at_calls': sum(1 for c in cmds if re.search(r'vidscribe\b.*--at\b', c)),
            'scan_calls': sum(1 for c in cmds if re.search(r'vidscribe\b.*--scan\b', c)),
            'commands': cmds, 'other_items': other, 'leak': leak, 'usage': usage}


PROMPT_CHECK = '''# Goal
Check that the reference answers to questions about a video are still on screen in this download of it. The questions were written on an earlier download; a new download can differ (re-encodes, edits, shifted times).

# Your folder: {F}/
- refs.json: one entry per question: set, qid, question, answer (the reference answer), time_s (when the answer was on screen in the earlier download) and visible_s (the span it was on screen).
- frames/video.mp4: the video. Do not open it directly. Pull full-size frames with `vidscribe {F}/frames --at <seconds or M:SS>` and view them. A range with a count gives that many frames (`--at 8:10-8:20/8`); batch with commas.

# Steps
For each entry, pull the frame at time_s and view it. If the reference answer cannot be read there, look up to 60 s either side of time_s, then decide.

# Rules
- Use only your folder and the `vidscribe {F}/frames --at` command. Do not open anything else under {V}, do not search the web, do not run ffmpeg or any other tool on the video.
- verdict "ok": a full-size frame you viewed shows the reference answer. Give that frame's time as seen_s.
- verdict "gone": the reference answer is not on screen within 60 s of time_s in this download.
- Judge only whether the reference answer is on screen, not whether the question is good.

# Output
Write {F}/time_check.json: a JSON list of {{"set", "qid", "verdict": "ok"|"gone", "seen_s": <seconds or null>, "note": "<what the frame shows>"}}.
'''


def build_check(vid):
    """Time-check folder for one video: the video and every question whose answer is on screen."""
    folder = f'{V}/chk/{vid}'
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(f'{folder}/frames')
    subprocess.run(['cp', '-c', f'{V}/src/{vid}.mp4', f'{folder}/frames/video.mp4'], check=True)
    refs = [dict(q, set=s) for s in SETS if vid in ids(s) for q in questions(s, vid) if q['kind'] != 'speech']
    refs = [{k: r[k] for k in ('set', 'qid', 'question', 'answer', 'time_s', 'visible_s')} for r in refs]
    json.dump(refs, open(f'{folder}/refs.json', 'w'), ensure_ascii=False, indent=1)
    return folder, PROMPT_CHECK.format(F=folder, V=V), len(refs)


def make_labels(seed):
    """Folder labels a/b/c per set and video, shuffled over the arms. Kept outside the agents' folders."""
    rnd = random.Random(seed)
    labels = {}
    for s in SETS:
        labels[s] = {}
        for v in ids(s):
            l = ['a', 'b', 'c']; rnd.shuffle(l)
            labels[s][v] = dict(zip(ARMS, l))
    return labels


def answer_jobs(labels, dropped=(), only=None):
    """Build every answer folder afresh and return its job. dropped: (set, video, qid) left out of every arm."""
    jobs = []
    for s in SETS:
        for v in ids(s):
            qs = [q for q in questions(s, v) if (s, v, q['qid']) not in dropped]
            for arm in ARMS:
                name = f'{s}_{v}_{labels[s][v][arm]}'
                if only is not None and name not in only: continue
                folder, src = f'{V}/ans/{name}', SRC[arm]
                build(folder, arm, f'{V}/{src}/tr/{v}.srt', f'{V}/{src}/frames/{v}', f'{V}/src/{v}.mp4', qs)
                jobs.append((name, folder, prompt(arm, folder, len(qs)), BIN[arm] and f'{V}/bin/{BIN[arm]}'))
    return jobs


def answers(name, base=None):
    """An agent's answers by qid, or None when the file is missing or unreadable."""
    try:
        a = json.load(open(f'{base or V + "/ans"}/{name}/answers.json'))
        return {x['qid']: x for x in a}
    except (OSError, ValueError, KeyError, TypeError):
        return None


# The blind grader of every earlier run (eval/README.md, "Grader"): one call per question, sees one candidate.
GRADE_SYS = ("You grade answers to questions about a video. You get a question, the reference answer, and one candidate answer. "
             "Score: 1 = correct (matches the reference in substance), 0.5 = partially correct (some key part right, some missing or wrong), "
             "0 = wrong, or 'unknown'. Return JSON.")
GRADE_SCHEMA = {"type": "object", "properties": {"score": {"type": "number", "enum": [0, 0.5, 1]}, "reason": {"type": "string"}},
                "required": ["score", "reason"]}


def grade_items(labels, dropped=()):
    """One item per set, video, arm and question, with the agent's answer ('unknown' when it gave none)."""
    items = []
    for s in SETS:
        for v in ids(s):
            for arm in ARMS:
                got = answers(f'{s}_{v}_{labels[s][v][arm]}') or {}
                for q in questions(s, v):
                    if (s, v, q['qid']) in dropped: continue
                    a = got.get(q['qid']) or {}
                    ans = a.get('answer')
                    items.append({'set': s, 'vid': v, 'arm': arm, 'qid': q['qid'], 'kind': q['kind'],
                                  'answer': ans if isinstance(ans, str) and ans.strip() else 'unknown',
                                  'confidence': a.get('confidence'), 'frame': a.get('frame'),
                                  'prompt': f"Question: {q['question']}\nReference answer: {q['answer']}\nCandidate answer: {ans or 'unknown'}"})
    return items


def is_unknown(ans):
    return (ans or '').strip().strip('."\'').lower() in ('unknown', '')


def summarize(items):
    """Per set and arm: score, questions, wrong answers that are not 'unknown', and score by kind."""
    out = {}
    for it in items:
        r = out.setdefault(it['set'], {}).setdefault(it['arm'], {'score': 0, 'n': 0, 'wrong': 0, 'unknown': 0, 'kind': {}})
        r['score'] += it['score']; r['n'] += 1
        r['wrong'] += it['score'] == 0 and not is_unknown(it['answer'])
        r['unknown'] += is_unknown(it['answer'])
        k = r['kind'].setdefault(it['kind'], [0, 0]); k[0] += it['score']; k[1] += 1
    return out
