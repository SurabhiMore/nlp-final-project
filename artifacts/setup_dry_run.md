# Setup dry run

Can someone get Echoes.ai running from the README alone? Part of #74. This is a dry run by the
team, not the setup test with a person from outside the team, which #74 still needs.

## How it was run

November 17, on a MacBook (Apple M5, 16 GB, macOS 26.6) with a fast connection. We followed
"Run it locally", Option A, in the README on a fresh clone, in a new folder with nothing cached:
no pip cache and no speech models. There was no model key, so `.env` was set to
`LLM_PROVIDER=offline`, which the README offers for trying it without a key.

## Time for each step

| Step | Time | Result |
|---|---|---|
| `git clone` | under 1 s | |
| `python3.12 -m venv .venv` | 1 s | |
| `pip install -r requirements.txt` | 43 s | 242 packages downloaded |
| `python -m spacy download en_core_web_sm` | 17 s | |
| `cp .env.example .env`, set `LLM_PROVIDER=offline` | under 1 s | |
| `python -m eval.datasets --check` | under 1 s | 0 problems in either exhibit |
| `uvicorn app.server:app`, until `/health` is ok | 2 s | |
| First typed question | under 1 s | Answered with 8 passages |
| First spoken question | 28 s | Downloads Whisper small, then heard the question right |
| Second spoken question | 3 s | |
| First spoken answer | 22 s | Downloads the Kokoro voice |
| Second spoken answer | 2 s | |
| `python -m pytest` | 4 s | All tests passed |
| **From clone to a spoken answer** | **about 2 minutes** | |

The install takes 1.4 GB, and the speech models another 777 MB. On a slower connection the pip
install and the two model downloads take longer, since they make up almost all of the time.

## Problems found

An earlier run on November 16 found three problems, all fixed in the README in PR #75:

1. `python -m venv .venv` failed: `python` does not exist on a Mac, and `python3` is 3.9, below
   the 3.10 minimum. The README now uses `python3.12` and says how to get it.
2. Nothing said where to get a model key. The README now says how to get a free Groq key, and
   names the model we report numbers for.
3. The server stopped on its first spoken answer, because the clone was in a folder whose path
   was too long for espeak-ng, which Kokoro uses (over 160 characters to its data). The README
   now says to clone into a shorter folder if that happens.

This run, with the fixed README, found no new problems.

## Not tested here

- A person who does not know the project, which is what #74 asks for
- Answers from a real model, since there was no key
- Windows and Linux, and the Docker option
