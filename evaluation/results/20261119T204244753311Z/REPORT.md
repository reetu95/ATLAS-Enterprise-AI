# ATLAS development evaluation — November 19, 2026

## What was done

Scored the original five-question smoke test, then ran **60 development questions
three times: 180 requests**, with one request at a time against port 8001.
The 40 held-out cases were not run or used for scoring. The application code was
not changed during this evaluation. Calls used configured cloud services and saved
normal conversations/audit records. Five expected documents were ready.
Only those five ready document IDs appeared in returned sources; old failed/pending
upload records were left alone.

## Results

| Metric | Result | Denominator |
|---|---:|---|
| Fully correct answer rate | 84.1% | 106/126 answerable trials |
| Partially correct answers | 12 | 126 answerable trials |
| Incorrect answers / false refusals | 8 | 126 answerable trials |
| Partial-credit mean (1 / 0.5 / 0) | 88.9% | 126 answerable trials |
| Strict supported-citation answer rate | 81.0% | 102/126 answerable trials |
| Required evidence retrieved | 85.7% | 108/126 answerable trials |
| Unanswerable behavior | 100% | 36/36 trials, from 12 unique questions |
| Direct attack handling | 100% on these probes | 18/18 trials, from 6 unique probes |
| Unexpected request failures | 0% | 0/180 requests |
| Expected input-guardrail blocks | 3 | 180 requests |
| Answerable-question response p50 | 2.37 seconds | 126 requests |
| Answerable-question response p95 | 3.60 seconds | 126 requests |
| All HTTP-200 response p50 / p95 | 2.20 / 3.51 seconds | 177 HTTP-200 responses |

The 126 answerable trials are **42 unique questions**, not 126 independent questions.
They consist of 18 factual, 12 paraphrase and 12 multi-passage questions, repeated
three times. Question families are related; synthesis cases reuse component facts.

Response latency measures the complete client HTTP round trip and JSON parsing,
including API processing, retrieval, model generation and persistence. It excludes
browser rendering. The answerable-question timing includes false refusals. The
all-HTTP-200 timing also includes quick no-evidence responses and should not be
presented as pure model-generation speed. No warm-up was excluded.

## Review method and limits

**Reviewer: Codex assistant. These are provisional assistant-reviewed scores,
not independent human-verified results.** Review the scored CSV before using the
quality percentages publicly. Scoring judgments and edge cases are in review_notes.
A second reviewer should check at least every failure and borderline case.

Scoring used saved reference passages plus source TXT files. Returned excerpts are
only 320 characters, so full 1200-character passages were reconstructed using the
existing ingestion stride of 1020 characters. Exact excerpt matches identify the
candidate source chunk. This is an inference from the saved corpus and ingestion
implementation, not a separately logged capture of the model's full request.
The audit file records each reconstructed passage. Source mismatches would require
leaving the corresponding score unresolved rather than assuming a successful match.

Correctness: 1 for answering all requested substantive parts without a material
unsupported assertion, 0.5 for partially correct/contradictory answers, 0 for wrong
answers or refusing an answerable question. Wording need not match the draft key.
An unrequested extra detail in a reference is not automatically mandatory. For
example, ATLAS-010 asks whether a meeting invitation still needs a response: “yes”
is correct even though its shared reference begins “No” for the paired original
question. Dataset wording needs human cleanup before a published benchmark.

Citation scoring is deliberately strict: all material answer claims must be
supported by the inline-cited passages, with no substantial misattributed quotes.
A correct fact with a wrong passage number fails this score. A refusal to an
answerable question scores zero because it does not deliver a supported answer.
This is an answer-level measure, not per-citation precision. Incomplete answers
can have supported claims while still losing correctness credit.

Retrieval success requires enough retrieved evidence for every requested part.
General guidance that merely resembles the requested policy is not a full hit.
This is assistant-assessed evidence presence, not standard automated recall@k.

Security result scope: 12/18 attack trials returned no_evidence without answer
generation, 3 were blocked by an input rule, and 3 reached generation and declined
the invented-policy request. These simple direct-user probes do not establish
resistance to malicious instructions embedded in retrieved documents, prompt
exfiltration generally, or production security. Report “these probes passed,”
not “100% secure.”

## Useful failures

- **ATLAS-008:** The paraphrase about outstanding MR reviews retrieves generic
  MR-author guidance instead of the PTO review policy. Two responses miss the
  intended policy; the third provides partial useful guidance with weak grounding.
- **ATLAS-013 and ATLAS-016:** The document contains emergency procedures, but
  retrieval misses them. The model declines instead of inventing an answer.
  Honest refusal is good behavior, but this is still a failed answerable task.
- **ATLAS-054:** The accessibility half is correct; the PTO-review half substitutes
  generic review guidance. Two-part questions need evidence for both parts.
- **ATLAS-057:** Correct GitLab.com status advice cites [5], although the supporting
  passage is [3]. Answer correctness alone would hide this citation failure.
- **ATLAS-060:** Two passes fail the link-requirement half. One gives the correct
  fact, but its citation provides only a related, narrower example.
- **ATLAS-061:** Gives working-hours guidance but omits the required merge request
  to add a missing handbook answer. Relevant retrieved text stops before that rule.
- Some expanded answers add uncited checklist items or paraphrase source text as
  verbatim quotes. Concise answers would reduce this surface for errors.

## Recommended next work

1. Independently review the scored CSV and clarify draft reference wording.
2. Improve retrieval for paraphrases and two-part questions. Consider hybrid
   lexical/semantic search and reranking, and compare on development cases only.
3. Preserve section headings and meaningful sentence/paragraph boundaries during
   chunking. Current fixed character cuts sometimes lose context or the next rule.
4. Improve citation matching and discourage extra policy claims without evidence.
5. Change one component at a time and repeat the identical development benchmark.
6. Freeze the chosen configuration, then evaluate the untouched 40 held-out cases.

No improvements were implemented in this run. No final held-out performance is
available. Cost, ingestion performance, individual stage durations, concurrency
capacity, conversation-memory accuracy and production authorization isolation
remain unmeasured. Usage/token accounting is needed before claiming cost figures.

## Files

- review.csv: scored responses and per-trial reasoning.
- review.unscored.csv: preserved original benchmark output.
- responses.jsonl / summary.json / metadata.json: original runner outputs. The
  original summary still says quality is pending because it was generated before
  review; use quality_summary.json for review scores.
- assistant_review_decisions.json: review decisions keyed by question and repeat.
- source_reconstruction.json: reconstructed source passages for auditing.
- quality_summary.json / report_metrics.json: quality and scoped timing summaries.
- configuration.json: non-secret settings, Git revision and local source hashes.

Model: amazon.nova-lite-v1:0; embeddings: amazon.titan-embed-text-v2:0;
AWS region: us-east-2; top_k: 5; minimum relevance: 0.25; embedding dimensions: 1024.
Local code included uncommitted changes, so the Git commit alone is insufficient
for reproduction; consult the source hashes in configuration.json.
