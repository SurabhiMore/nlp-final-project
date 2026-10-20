# Reply check: before and after (issue #28)

- Questions: 64 held-out questions frozen at commit 3bc6f54 (2026-10-20T11:26:50+00:00), 8 passages each, from `eval/fixtures/frozen_passages.json`
- Model replies: 128 from openai/gpt-oss-120b, one per question and mode, in `eval/results/grounding_replies.jsonl`
- Before and after score the same replies. Before is the reply handling on main at 3bc6f54; after adds `check_reply` in `pipeline/persona.py`.
- Reproduce: `python -m eval.eval_grounding` (no model calls). Fresh replies: `--collect`, then the same command.

## all (128 replies)

| Metric | Before | After | Better is |
|---|---|---|---|
| Grounded answer accuracy | 0.922 | 0.922 | higher |
| Answerable questions answered correctly | 0.891 | 0.891 | higher |
| Trap questions declined | 1.000 | 1.000 | higher |
| Unnecessary declines (support was in the passages) | 0 | 0 | lower |
| Declines that still state the answer without a source | 1 | 0 | lower |
| Answers shown with no valid citation | 0 | 0 | lower |
| Unreadable replies shown as raw text | 0 | 0 | lower |
| Invalid citation ids sent by the model (all removed) | 0 | 0 | info |
| Replies that crashed the reply handling | 0 | 0 | lower |

Changed by the check: decline_that_answers 2.

## all/persona (64 replies)

| Metric | Before | After | Better is |
|---|---|---|---|
| Grounded answer accuracy | 0.922 | 0.922 | higher |
| Answerable questions answered correctly | 0.891 | 0.891 | higher |
| Trap questions declined | 1.000 | 1.000 | higher |
| Unnecessary declines (support was in the passages) | 0 | 0 | lower |
| Declines that still state the answer without a source | 1 | 0 | lower |
| Answers shown with no valid citation | 0 | 0 | lower |
| Unreadable replies shown as raw text | 0 | 0 | lower |
| Invalid citation ids sent by the model (all removed) | 0 | 0 | info |
| Replies that crashed the reply handling | 0 | 0 | lower |

Changed by the check: decline_that_answers 1.

## all/neutral (64 replies)

| Metric | Before | After | Better is |
|---|---|---|---|
| Grounded answer accuracy | 0.922 | 0.922 | higher |
| Answerable questions answered correctly | 0.891 | 0.891 | higher |
| Trap questions declined | 1.000 | 1.000 | higher |
| Unnecessary declines (support was in the passages) | 0 | 0 | lower |
| Declines that still state the answer without a source | 0 | 0 | lower |
| Answers shown with no valid citation | 0 | 0 | lower |
| Unreadable replies shown as raw text | 0 | 0 | lower |
| Invalid citation ids sent by the model (all removed) | 0 | 0 | info |
| Replies that crashed the reply handling | 0 | 0 | lower |

Changed by the check: decline_that_answers 1.

## t-rex/neutral (32 replies)

| Metric | Before | After | Better is |
|---|---|---|---|
| Grounded answer accuracy | 0.875 | 0.875 | higher |
| Answerable questions answered correctly | 0.826 | 0.826 | higher |
| Trap questions declined | 1.000 | 1.000 | higher |
| Unnecessary declines (support was in the passages) | 0 | 0 | lower |
| Declines that still state the answer without a source | 0 | 0 | lower |
| Answers shown with no valid citation | 0 | 0 | lower |
| Unreadable replies shown as raw text | 0 | 0 | lower |
| Invalid citation ids sent by the model (all removed) | 0 | 0 | info |
| Replies that crashed the reply handling | 0 | 0 | lower |

Changed by the check: decline_that_answers 1.

## t-rex/persona (32 replies)

| Metric | Before | After | Better is |
|---|---|---|---|
| Grounded answer accuracy | 0.875 | 0.875 | higher |
| Answerable questions answered correctly | 0.826 | 0.826 | higher |
| Trap questions declined | 1.000 | 1.000 | higher |
| Unnecessary declines (support was in the passages) | 0 | 0 | lower |
| Declines that still state the answer without a source | 1 | 0 | lower |
| Answers shown with no valid citation | 0 | 0 | lower |
| Unreadable replies shown as raw text | 0 | 0 | lower |
| Invalid citation ids sent by the model (all removed) | 0 | 0 | info |
| Replies that crashed the reply handling | 0 | 0 | lower |

Changed by the check: decline_that_answers 1.

## van-gogh/neutral (32 replies)

| Metric | Before | After | Better is |
|---|---|---|---|
| Grounded answer accuracy | 0.969 | 0.969 | higher |
| Answerable questions answered correctly | 0.957 | 0.957 | higher |
| Trap questions declined | 1.000 | 1.000 | higher |
| Unnecessary declines (support was in the passages) | 0 | 0 | lower |
| Declines that still state the answer without a source | 0 | 0 | lower |
| Answers shown with no valid citation | 0 | 0 | lower |
| Unreadable replies shown as raw text | 0 | 0 | lower |
| Invalid citation ids sent by the model (all removed) | 0 | 0 | info |
| Replies that crashed the reply handling | 0 | 0 | lower |

Changed by the check: none.

## van-gogh/persona (32 replies)

| Metric | Before | After | Better is |
|---|---|---|---|
| Grounded answer accuracy | 0.969 | 0.969 | higher |
| Answerable questions answered correctly | 0.957 | 0.957 | higher |
| Trap questions declined | 1.000 | 1.000 | higher |
| Unnecessary declines (support was in the passages) | 0 | 0 | lower |
| Declines that still state the answer without a source | 0 | 0 | lower |
| Answers shown with no valid citation | 0 | 0 | lower |
| Unreadable replies shown as raw text | 0 | 0 | lower |
| Invalid citation ids sent by the model (all removed) | 0 | 0 | info |
| Replies that crashed the reply handling | 0 | 0 | lower |

Changed by the check: none.

## Every reply the check changed

| Exhibit | Mode | Question | Answerable | Rule | Before (status: shown text) | After | Grounded before → after |
|---|---|---|---|---|---|---|---|
| t-rex | persona | tr-03: What does the rex in your name mean? | yes | decline_that_answers | not_in_sources: My name means "king"—the Latin word rex, used to call me the king of the dinosaurs. | not_in_sources: My sources do not say anything about that. | False → False |
| t-rex | neutral | tr-21: What is the capital of France? | no | decline_that_answers | declined: I’m the museum’s guide for Tyrannosaurus rex, here to answer questions about that dinosaur | declined: I can only answer questions about Tyrannosaurus rex and the museum. | True → True |

## Regressions (grounded before, not after)

None.

## Still wrong after the check

| Exhibit | Mode | Question | Status | Support in passages | Why (automatic) |
|---|---|---|---|---|---|
| t-rex | persona | tr-03: What does the rex in your name mean? | not_in_sources | no | declined; search did not give a supporting passage |
| t-rex | neutral | tr-03: What does the rex in your name mean? | not_in_sources | no | declined; search did not give a supporting passage |
| t-rex | persona | tr-09: How strong was your bite? | answered | no | answer is missing a key fact (may be wording; check by hand) |
| t-rex | neutral | tr-09: How strong was your bite? | answered | no | answer is missing a key fact (may be wording; check by hand) |
| t-rex | persona | tr-26: Which horned dinosaur was among your primary prey targets? | answered | no | answer is missing a key fact (may be wording; check by hand) |
| t-rex | neutral | tr-26: Which horned dinosaur was among your primary prey targets? | answered | no | answer is missing a key fact (may be wording; check by hand) |
| t-rex | persona | tr-28: Did you hunt primarily during the day or at night? | not_in_sources | no | declined; search did not give a supporting passage |
| t-rex | neutral | tr-28: Did you hunt primarily during the day or at night? | not_in_sources | no | declined; search did not give a supporting passage |
| van-gogh | persona | vg-08: What did the countryside around Arles remind you of? | answered | no | answer is missing a key fact (may be wording; check by hand) |
| van-gogh | neutral | vg-08: What did the countryside around Arles remind you of? | answered | no | answer is missing a key fact (may be wording; check by hand) |
