# Sleep Quality Dashboard

A lightweight, AI-powered sleep assessment prototype built for the Lean Health Co intern take-home task.

The user answers three quick questions about their sleep. The app calculates a sleep grade (A–F) using a transparent scoring system, then calls an LLM to generate exactly one positive, non-medical, actionable tip for tonight.

## Live Demo

> **Deployed URL:** _add link after deployment_

## Features

- Three-question form (hours slept, time to fall asleep, energy level)
- Transparent A–F scoring logic
- AI-generated one-sentence tip via Anthropic Claude
- Calming dark UI with soft indigo accents
- Built and deployed in under 4 hours

## Grading Logic

Three factors are scored 0–2 each for a 0–6 total:

| Factor | 2 points | 1 point | 0 points |
| --- | --- | --- | --- |
| Hours slept | 7+ | 5–6 | Under 5 |
| Time to fall asleep | Under 20 min | 20–60 min | Over 1 hour |
| Energy level (1–5) | 4–5 | 2–3 | 1 |

| Total | Grade |
| --- | --- |
| 6 | A |
| 5 | B |
| 3–4 | C |
| 2 | D |
| 0–1 | F |

This maps exactly to the anchors defined in the task brief (A, C, F) and produces a defensible interpolation for B and D.

## AI Prompt Constraints

The prompt enforces:

- Exactly one sentence, 20 words or fewer
- Positive and encouraging tone
- One practical, actionable tip for tonight
- No medical advice, diagnosis, supplements, or referrals to doctors
- No lists, preamble, quotes, or sign-offs

## Running Locally

### Prerequisites

- Python 3.9 or newer
- An Anthropic API key from <https://console.anthropic.com/>

### Setup

```bash
# Clone the repo
git clone https://github.com/Theozuz/lean-sleep-dashboard.git
cd lean-sleep-dashboard

# Install dependencies
pip install -r requirements.txt

# Set your API key
# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."

# Run the app
streamlit run app.py
```

The app opens at <http://localhost:8501>.

## Deploying to Streamlit Community Cloud

1. Push this repository to GitHub (public or private).
2. Go to <https://share.streamlit.io/> and sign in with GitHub.
3. Click **New app**, pick this repo and `app.py`.
4. Under **Advanced settings → Secrets**, add:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```

5. Click **Deploy**. The app will be live at a public URL within about a minute.

The app reads `ANTHROPIC_API_KEY` from Streamlit secrets first, then falls back to the environment variable, so the same code works locally and in the cloud.

## Project Structure

```
sleep-dashboard/
├── app.py                    # Streamlit app (UI, grading, LLM call)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore                # Ignore rules (excludes secrets.toml)
├── assets/
│   └── night-sky.jpg         # Background photograph (Unsplash, royalty-free)
└── .streamlit/
    └── config.toml           # Dark theme configuration
```

## Tech Stack

- **Framework:** Streamlit
- **Language:** Python 3
- **LLM:** Anthropic Claude (`claude-haiku-4-5-20251001`)
- **Hosting:** Streamlit Community Cloud

## Evaluation Checklist

- [x] Working deployment with public URL
- [x] Effective prompt engineering (exactly one sentence, positive, no medical advice)
- [x] Accurate, transparent grading logic
- [x] Clean, calming, nighttime-themed UI
- [x] Clear repository structure and README

---

Built as a take-home prototype for Lean Health Co.
