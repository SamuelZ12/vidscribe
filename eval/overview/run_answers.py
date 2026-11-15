"""Run the answer agents: python3 run_answers.py [workers] [set ...]. Builds each folder afresh, then one Codex agent per folder.
Labels are written to the keys folder, which is unreadable (mode 000) while agents run."""
import json, os, random, sys, time
import harness as h

workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
lab = f'{h.KEYS}/labels.json'
os.chmod(h.KEYS, 0o700)
if os.path.exists(lab):                      # a re-run keeps the labels and only redoes folders without answers
    saved = json.load(open(lab)); labels = saved['labels']
    only = {f'{s}_{v}_{l}' for s in labels for v in labels[s] for l in labels[s][v].values()
            if h.answers(f'{s}_{v}_{l}') is None}
else:
    seed = int.from_bytes(os.urandom(8), 'big')
    labels, only = h.make_labels(seed), None
    json.dump({'seed': seed, 'labels': labels}, open(lab, 'w'), indent=1)
sets = sys.argv[2:] or list(h.SETS)
todo = {f'{s}_{v}_{l}' for s in sets for v in labels[s] for l in labels[s][v].values()}
only = todo if only is None else only & todo
jobs = h.answer_jobs(labels, only=only)
random.Random(1).shuffle(jobs)               # mix sets and arms over the run
print(f'{len(jobs)} agents, {workers} at a time', flush=True)
os.chmod(h.KEYS, 0)
t = time.time()
try:
    done = h.run_pool(jobs, workers)
finally:
    os.chmod(h.KEYS, 0o700)
bad = [n for n, rc, s in done if rc != 0 or h.answers(n) is None]
print(f'done in {round(time.time() - t)} s; failed or no answers: {bad}')
