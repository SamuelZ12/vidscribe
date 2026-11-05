# usage: python3 check_transcript.py TRANSCRIPT.srt QUESTIONS.json
# Flags hard-set questions whose answer words are said anywhere, or whose anchor words are said within 60 s of anchor_s.
# Word hits are candidates for hand review, not verdicts (common words like "blue" can be said for unrelated reasons).
import json, re, sys

STOP = set("a an and are as at be by for from in is it of on or that the this to with was what which who how its into over under than then there these those your you".split())
WINDOW = 60

def secs(t):
    h, m, s = t.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)

def norm(text):  # "3,000" and "3000" must match
    return re.sub(r"(?<=\d),(?=\d{3})", "", text.lower())

def cues(path):
    for block in re.split(r"\n\s*\n", open(path, encoding="utf-8").read().strip()):
        lines = block.splitlines()
        for i, line in enumerate(lines):
            if "-->" in line:
                a, b = (x.strip() for x in line.split("-->"))
                yield secs(a), secs(b), norm(" ".join(lines[i + 1:]))
                break

def words(text):
    return [w for w in re.findall(r"[a-z0-9][a-z0-9.'%-]*", norm(text)) if w not in STOP and (len(w) > 2 or w.isdigit())]

def hits(ws, cs):
    return [(round(a), w) for w in ws for a, b, txt in cs if re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", txt)]

cs = list(cues(sys.argv[1]))
flagged = 0
for q in json.load(open(sys.argv[2], encoding="utf-8")):
    lo, hi = q["anchor_s"]
    ans = hits(words(q["answer"]), cs)
    anc = hits(words(q["anchor"]), [c for c in cs if c[1] >= lo - WINDOW and c[0] <= hi + WINDOW])
    flagged += bool(ans or anc)
    print(f"{q['qid']}: {'FLAG' if ans or anc else 'ok'}")
    for t, w in ans: print(f"  answer word '{w}' said at {t}s")
    for t, w in anc: print(f"  anchor word '{w}' said at {t}s (anchor {lo}-{hi}s)")
sys.exit(1 if flagged else 0)
