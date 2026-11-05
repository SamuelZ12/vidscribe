# ADR-0001: Stay local; no hosted video model

## Status
Accepted

## Date
2026-11-05

## Context
A hosted video model reads audio and picture together and would close part of the gap that frames leave: on [Omni2Web](https://arxiv.org/html/2609.23417)'s instruction-recovery track, Gemini 3.5 Flash scored 18.2 with the transcript only, 38.1 with silent video + transcript and 47.5 with native audio + video. Gemini Flash behind a flag was the obvious way to get that.

## Decision
Don't add one. Transcription and frame work run on the device: no API keys, no cloud service; the network is only used to download the model once and to fetch URLs.

## Alternatives considered
- **Gemini Flash behind a flag (escalate when frames aren't enough).** Rejected: paid, and it sends the user's media off the device.

## Consequences
- vidscribe stays free, and media never leaves the device.
- The local design borrows the idea instead: Google's [agentic video](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-agentic-video-in-gemini/) scans cheaply, then inspects; vidscribe does the same with `--scan` (contact sheets) and `--at` (full frames). See [ADR-0004](0004-frames-on-demand.md) and [ADR-0005](0005-no-ocr.md).
- The remaining gap between frames + transcript and native audio + video (38.1 vs 47.5 on Omni2Web) stays.
