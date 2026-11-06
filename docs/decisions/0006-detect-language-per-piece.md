# ADR-0006: Detect the language of every piece by default

## Status
Accepted

## Date
2026-11-05

## Context
Without `-l`, vidscribe passed no language, and `mlx_audio.stt.generate` filled in its default `--language en`. Every 30 s piece was therefore prompted with the literal tag `language en`, so the language was never detected. `-l zh` produced the tag `language zh`, which isn't one of the model's 30 full names (`Chinese`, `Hindi`, ...).

The [language test](../measurements.md#language-default-forced-en-vs-auto-detect) (8 real clips plus 3 spliced ones) found:
- Forcing `en` didn't hurt English or Mandarin, including mixed English–Mandarin speech: CER against human subtitles was the same within 0.005.
- On music it turned the audio into "oh, oh, ..." loops: 6 cut-off warnings, about 9× slower, and ~2000 characters of junk. Auto-detect returned nothing there.
- mlx-audio's own auto-detect locks every later piece to the first piece's language, so music after English speech still looped.

## Decision
- Without `-l`, each piece is detected separately: the model is passed `language=None`, and the per-piece hook clears the language mlx-audio would lock in.
- `-l` takes short codes or full names; codes map to Qwen3-ASR's names (`zh` → `Chinese`, `hi` → `Hindi`, `en` → `English`, ...). Full names pass through unchanged.

## Alternatives considered
- **Keep forced `en`.** Byte-identical to master, but music and non-speech keep producing slow loops, now only bounded by the truncation fix.
- **mlx-audio's auto-detect alone** (`language=None` without the hook). One line, but it loops whenever the first piece is English.

## Consequences
- Normal runs are no longer byte-identical to master. English and Mandarin text changes only in punctuation and spacing: quote marks, spaces around English words in Chinese, digits written as words (`1.19` → `一点一九`).
- Hindi: English terms come out in Devanagari without punctuation (`VideoWriter` → `वीडियो राइट करता`). `-l en` gives the old Latin-script output.
- `-m` Whisper models also get `language=None` and detect the language themselves; they used to be forced to English. Not tested: no Whisper model was downloaded.
- If mlx-audio changes its internals, the hook is skipped with a warning and mlx-audio's locking auto-detect applies.
