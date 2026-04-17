"""
Sleep Quality Dashboard
An AI-powered sleep assessment prototype for Lean Health Co.
"""

import base64
import os
from pathlib import Path

import streamlit as st
from anthropic import Anthropic

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Sleep Quality Dashboard",
    page_icon="🌙",
    layout="centered",
    initial_sidebar_state="collapsed",
)

MODEL_NAME = "claude-haiku-4-5-20251001"
MAX_TOKENS = 120

FALL_ASLEEP_OPTIONS = {
    "Under 20 minutes": "under_20",
    "20 to 60 minutes": "20_to_60",
    "Over an hour": "over_60",
}

GRADE_COLORS = {
    "A": "#86efac",   # moonlit mint
    "B": "#a5b4fc",   # moonlight indigo
    "C": "#c4b5fd",   # soft violet
    "D": "#fcd34d",   # warm amber, gentle warning
    "F": "#fca5a5",   # muted rose
}

GRADE_HEADLINES = {
    "A": "Excellent sleep quality",
    "B": "Solid night overall",
    "C": "Room to improve",
    "D": "Rough night",
    "F": "Significant sleep debt",
}


# ---------------------------------------------------------------------------
# Visual design
# ---------------------------------------------------------------------------

def _background_image_data_uri() -> str:
    """
    Inline the night-sky photo as a base64 data URI so it renders regardless
    of CDN blocks, CSP rules, or ad-blockers. Falls back to the remote Unsplash
    URL if the local file is missing.
    """
    local = Path(__file__).parent / "assets" / "night-sky.jpg"
    if local.exists():
        encoded = base64.b64encode(local.read_bytes()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
    return "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1800&q=75"


_BG_IMAGE_URL = _background_image_data_uri()

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Fraunces:wght@300;400;500;600&display=swap');

    :root {
        --bg-deep: #030611;
        --bg-mid: #060b1a;
        --text-primary: #eef1f8;
        --text-muted: #94a0ba;
        --moon-glow: #b8c4ff;
        --violet-glow: #c4b5fd;
        --surface: rgba(255, 255, 255, 0.05);
        --surface-strong: rgba(255, 255, 255, 0.07);
        --border-soft: rgba(184, 196, 255, 0.12);
        --border-strong: rgba(184, 196, 255, 0.28);
    }

    /* ------------ Hide Streamlit chrome ------------ */
    header[data-testid="stHeader"] { background: transparent; height: 0; }
    [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }
    #MainMenu, footer { visibility: hidden; }
    .stDeployButton { display: none; }
    [data-testid="stStatusWidget"] { display: none; }

    /* ------------ Global background: real night-sky photo + subtle overlay ------------
       IMPORTANT: the photo lives on .stApp::before. For it to be visible,
       .stApp's direct-child containers (stAppViewContainer, stMain, block-container)
       MUST be transparent, otherwise they paint over the pseudo-element.
    */
    html, body {
        background-color: #03050e;
        color: var(--text-primary);
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    }
    .stApp {
        background-color: #03050e;
        color: var(--text-primary);
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
        /* perspective turns .stApp into a 3-D scroll context.
           Children at different Z-depths scroll at different speeds,
           giving the starfield a parallax effect relative to the content. */
        perspective: 8px;
        perspective-origin: center top;
        overflow-x: hidden;
        overflow-y: auto;
        height: 100vh;
    }
    /* Inner Streamlit containers: transparent + no independent scrolling.
       All scrolling must happen on .stApp so the perspective parallax works
       with a single scrollbar. */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    section.main,
    .main {
        background: transparent !important;
        overflow: visible !important;
        height: auto !important;
        max-height: none !important;
    }
    /* Keep content in the normal Z-plane so it scrolls at full speed */
    [data-testid="stAppViewContainer"] {
        transform: translateZ(0);
    }

    /* Background photograph.
       translateZ(-4px) pushes the image behind the content plane.
       scale(1.5) compensates for the apparent shrink at that depth.
       Net effect: the starfield scrolls at ~67% of content speed. */
    .stApp::before {
        content: "";
        position: absolute;
        top: -20px; left: -20px; right: -20px;
        height: 200vh;
        pointer-events: none;
        z-index: -1;
        transform-origin: center top;
        transform: translateZ(-4px) scale(1.5);
        background-image:
            linear-gradient(180deg, rgba(3, 5, 14, 0.40) 0%, rgba(3, 5, 14, 0.20) 35%, rgba(3, 5, 14, 0.60) 100%),
            url('__BG_IMAGE_URL__');
        background-size: cover, cover;
        background-position: center top, center top;
        background-repeat: no-repeat, no-repeat;
    }

    /* Content area above starfield */
    .block-container {
        position: relative;
        z-index: 1;
        padding-top: 5rem;
        padding-bottom: 5rem;
        max-width: 760px;
    }

    /* ------------ Typography ------------ */
    .hero-eyebrow {
        font-size: 12px;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: var(--moon-glow);
        font-weight: 600;
        margin-bottom: 1rem;
        opacity: 0;
        animation: fadeUp 0.7s ease-out 0.1s forwards;
    }
    .hero-title {
        font-family: 'Fraunces', Georgia, serif;
        font-weight: 400;
        font-size: 62px;
        line-height: 1.02;
        letter-spacing: -2px;
        color: #f4f6fc;
        margin: 0 0 1.75rem 0;
        opacity: 0;
        animation: fadeUp 0.7s ease-out 0.2s forwards;
    }
    .hero-title em {
        font-style: italic;
        font-weight: 300;
        color: var(--moon-glow);
    }
    .hero-subtitle {
        font-size: 17px;
        line-height: 1.65;
        color: var(--text-muted);
        max-width: 540px;
        margin: 0 0 3rem 0;
        opacity: 0;
        animation: fadeUp 0.7s ease-out 0.3s forwards;
    }
    .hero-subtitle em {
        font-style: italic;
        color: var(--moon-glow);
        font-weight: 500;
    }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(14px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* ------------ Section labels (echoes Lean Health sectioning) ------------ */
    .section-label {
        font-size: 11px;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        color: var(--moon-glow);
        font-weight: 600;
        margin: 2.5rem 0 0.75rem 0;
        opacity: 0.9;
    }

    /* ------------ Glass form wrapper ------------ */
    /* Streamlit form inner div — make it transparent so our wrapper shows */
    [data-testid="stForm"] > div {
        background: transparent !important;
        border-color: transparent !important;
    }
    /* Glass style on the form itself */
    [data-testid="stForm"] {
        background: rgba(10, 14, 28, 0.55) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 16px !important;
        padding: 2.25rem 2.25rem 1.5rem 2.25rem !important;
        backdrop-filter: blur(10px) saturate(140%) !important;
        -webkit-backdrop-filter: blur(10px) saturate(140%) !important;
        box-shadow: 0 20px 60px -20px rgba(0, 0, 0, 0.6) !important;
        opacity: 0;
        animation: fadeUp 0.7s ease-out 0.4s forwards;
    }

    /* Widget labels */
    [data-testid="stWidgetLabel"] label p,
    label p {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        font-size: 15px !important;
    }

    /* Number input and select */
    [data-baseweb="input"] > div,
    [data-baseweb="select"] > div {
        background: rgba(6, 10, 24, 0.7) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
    }
    [data-baseweb="input"] input,
    [data-baseweb="select"] * {
        color: var(--text-primary) !important;
    }
    [data-baseweb="input"] > div:focus-within,
    [data-baseweb="select"] > div:focus-within {
        border-color: var(--moon-glow) !important;
        box-shadow: 0 0 0 3px rgba(184, 196, 255, 0.18) !important;
    }

    /* Slider */
    [data-testid="stSlider"] [role="slider"] {
        background: var(--moon-glow) !important;
        box-shadow: 0 0 0 6px rgba(184, 196, 255, 0.2) !important;
    }
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="progressbar"] + div {
        background: linear-gradient(90deg, var(--moon-glow), var(--violet-glow)) !important;
    }

    /* Primary button */
    .stButton > button, .stFormSubmitButton > button {
        width: 100%;
        background: linear-gradient(135deg, #818cf8 0%, #a78bfa 100%) !important;
        color: #0a0f1f !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.95rem 1rem !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 8px 24px -8px rgba(129, 140, 248, 0.55) !important;
        transition: transform 0.15s ease, box-shadow 0.2s ease !important;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 12px 30px -8px rgba(129, 140, 248, 0.75) !important;
    }
    .stButton > button:active, .stFormSubmitButton > button:active {
        transform: translateY(0);
    }

    /* Captions */
    [data-testid="stCaptionContainer"] {
        color: var(--text-muted) !important;
        font-size: 13px !important;
    }

    /* ------------ Grade card ------------ */
    .grade-card {
        margin-top: 1.25rem;
        padding: 3rem 2.25rem 2.5rem 2.25rem;
        text-align: center;
        background: rgba(10, 14, 28, 0.6);
        border: 1px solid var(--border-soft);
        border-radius: 20px;
        backdrop-filter: blur(12px) saturate(140%);
        -webkit-backdrop-filter: blur(12px) saturate(140%);
        box-shadow: 0 20px 60px -20px rgba(0, 0, 0, 0.7);
        animation: fadeUp 0.6s ease-out forwards;
    }
    .grade-letter {
        font-family: 'Fraunces', Georgia, serif;
        font-size: 140px;
        font-weight: 400;
        line-height: 1;
        letter-spacing: -5px;
        margin: 0;
        text-shadow: 0 0 60px currentColor;
    }
    .grade-headline {
        font-size: 19px;
        color: var(--text-primary);
        margin-top: 0.5rem;
        letter-spacing: 0.3px;
        font-weight: 500;
    }

    /* ------------ Insight card ------------ */
    .insight-card {
        margin-top: 1rem;
        padding: 1.75rem 2rem;
        background: rgba(10, 14, 28, 0.55);
        border: 1px solid var(--border-soft);
        border-left: 3px solid var(--violet-glow);
        border-radius: 16px;
        backdrop-filter: blur(10px) saturate(140%);
        -webkit-backdrop-filter: blur(10px) saturate(140%);
        animation: fadeUp 0.6s ease-out 0.15s forwards;
        opacity: 0;
    }
    .insight-label {
        color: var(--violet-glow);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .insight-text {
        color: var(--text-primary);
        font-size: 17px;
        line-height: 1.55;
        font-weight: 400;
    }

    /* ------------ Footer ------------ */
    .footer-note {
        text-align: center;
        color: var(--text-muted);
        font-size: 12px;
        margin-top: 3rem;
        letter-spacing: 0.3px;
    }

    /* Error */
    [data-testid="stAlert"] {
        background: rgba(252, 165, 165, 0.08) !important;
        border: 1px solid rgba(252, 165, 165, 0.25) !important;
        border-radius: 12px !important;
        color: #fecaca !important;
    }
</style>
"""

st.markdown(
    CUSTOM_CSS.replace("__BG_IMAGE_URL__", _BG_IMAGE_URL),
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Grading logic
# ---------------------------------------------------------------------------

def _score_hours(hours: float) -> int:
    if hours >= 7:
        return 2
    if hours >= 5:
        return 1
    return 0


def _score_latency(latency_key: str) -> int:
    return {"under_20": 2, "20_to_60": 1, "over_60": 0}[latency_key]


def _score_energy(energy: int) -> int:
    if energy >= 4:
        return 2
    if energy >= 2:
        return 1
    return 0


def calculate_sleep_grade(hours: float, latency_key: str, energy: int) -> str:
    """
    Score-based grading over three factors (0-2 points each, max 6).

    Anchors from the task brief:
      - A: 7+h, <20min to fall asleep, energy 4-5  -> 6 points
      - C: 5-6h, 20-60min to fall asleep, energy 2-3 -> 3 points
      - F: <5h, >60min to fall asleep, energy 1      -> 0 points

    B and D are the interpolated bands between those anchors.

    Special case: Zero hours of sleep. Latency is meaningless (they never
    slept). Best possible grade is D; drops to F when energy <= 2.
    """
    if hours == 0:
        return "F" if energy <= 2 else "D"

    total = _score_hours(hours) + _score_latency(latency_key) + _score_energy(energy)

    if total >= 6:
        return "A"
    if total >= 5:
        return "B"
    if total >= 3:
        return "C"
    if total >= 2:
        return "D"
    return "F"


# ---------------------------------------------------------------------------
# AI insight
# ---------------------------------------------------------------------------

def _get_api_key() -> str | None:
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def _classify_scenario(hours: float, latency_key: str, energy: int) -> str:
    """
    Pick the dominant issue the tip should address. Ordered by severity of
    the limiting factor, so the tip focuses where it will matter most.
    """
    if hours == 0:
        return "zero_hours"         # no sleep at all — unique handling
    if latency_key == "over_60":
        return "slow_onset"         # falling asleep is the main problem
    if hours < 5:
        return "short_sleep"        # not enough sleep
    if hours >= 7 and energy <= 2:
        return "good_quantity_low_energy"   # slept enough but feels tired
    if hours >= 7 and latency_key == "under_20" and energy >= 4:
        return "excellent"          # reinforce what works
    if latency_key == "20_to_60":
        return "moderate_onset"     # some trouble winding down
    return "general_improve"


# Focus topics and example "shape" of advice for each scenario.
# The model still generates the actual sentence; these steer it toward
# topics that actually match the user's situation.
_SCENARIO_BRIEFS = {
    "zero_hours": {
        "focus": (
            "gently acknowledging that no sleep happened and framing "
            "tonight as a calm, warm chance to begin recovering; suggest "
            "one small concrete pre-bed ritual (dim lights, early bedtime, "
            "slow breathing, no screens in the last hour) that makes "
            "tonight feel inviting; if they feel okay right now, warmly "
            "note that tonight's rest is where the real recovery begins"
        ),
        "avoid": (
            "alarming or clinical language, dire warnings about "
            "consequences, shaming, or phrases that sound like a doctor; "
            "the tip should feel like a warm friend encouraging an early "
            "night, NOT a lecture"
        ),
    },
    "slow_onset": {
        "focus": (
            "falling asleep faster tonight — techniques that calm the "
            "nervous system before bed (slow breathing, warm shower, dim "
            "light, putting the phone down earlier)"
        ),
        "avoid": "generic sleep-duration advice (they slept long enough, the issue is sleep onset)",
    },
    "short_sleep": {
        "focus": (
            "getting to bed earlier tonight and protecting tomorrow — "
            "concrete wind-down timing anchored to the {hours}-hour shortfall"
        ),
        "avoid": "advice that ignores how little sleep they got",
    },
    "good_quantity_low_energy": {
        "focus": (
            "sleep QUALITY rather than quantity — bedroom environment "
            "(temperature, darkness, noise), consistent bedtime, or exposure "
            "to natural light in the morning to recalibrate"
        ),
        "avoid": "telling them to sleep longer (they already slept {hours} hours)",
    },
    "excellent": {
        "focus": (
            "reinforcing the positive pattern tonight — protect whatever is "
            "working so tomorrow is another good night"
        ),
        "avoid": "scolding or prescribing changes; this person is doing well",
    },
    "moderate_onset": {
        "focus": (
            "shaving 10-15 minutes off tonight's sleep-onset time — a single "
            "pre-bed ritual (reading, breathing, stretching) done 30 minutes "
            "before lights out"
        ),
        "avoid": "heavy interventions; this is a nudge, not a protocol",
    },
    "general_improve": {
        "focus": (
            "one concrete thing to try tonight based on their specific "
            "numbers — lean on whichever number is weakest"
        ),
        "avoid": "vague platitudes; pick one anchor number and speak to it",
    },
}


def get_ai_insight(grade: str, hours: float, latency_label: str, energy: int) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not configured. Set it in Streamlit secrets or your environment."
        )

    client = Anthropic(api_key=api_key)
    latency_key = FALL_ASLEEP_OPTIONS.get(latency_label, latency_label)
    scenario = _classify_scenario(hours, latency_key, energy)
    brief = _SCENARIO_BRIEFS[scenario]
    focus = brief["focus"].format(hours=hours)
    avoid = brief["avoid"].format(hours=hours)

    # The three constraints below are lifted VERBATIM from the task brief:
    #   "exactly one sentence, entirely positive, and free from any medical advice"
    system_prompt = (
        "You are a sleep wellness coach writing one personalised tip for one "
        "user. The output MUST strictly satisfy these three constraints:\n\n"
        "  1. EXACTLY ONE SENTENCE. One sentence only, ending in one period. "
        "No semicolons chaining multiple ideas, no lists, no bullets, "
        "no preamble, no sign-off, no quotation marks.\n"
        "  2. ENTIRELY POSITIVE. Warm, encouraging, and affirming. Never "
        "alarming, never scolding, never shaming. Frame everything as a "
        "gentle invitation rather than a correction.\n"
        "  3. FREE FROM ANY MEDICAL ADVICE. No diagnoses, no mention of "
        "disorders or conditions, no medications, no supplements, no "
        "dosages, no clinical language, no referrals to doctors or "
        "specialists, no claims about treating or curing anything.\n\n"
        "Additional requirements:\n"
        "  - The sentence must reference at least one of the user's own "
        "numbers (hours slept, time to fall asleep, or energy level) so it "
        "feels personal, not templated.\n"
        "  - The advice must be a concrete, practical action the user can "
        "take TONIGHT.\n"
        "  - Keep it to 28 words or fewer.\n"
        "  - Vary sentence structure across requests; do not always open the "
        "same way.\n\n"
        "Output only the sentence itself, nothing else."
    )

    # The question is phrased as the user proposed: dynamic, natural,
    # and it forces the model to reason about THIS person specifically.
    user_prompt = (
        f"A person slept {hours} hours last night, took {latency_label.lower()} "
        f"to fall asleep, and rates their energy today at {energy} out of 5 "
        f"(1 = exhausted, 5 = fully rested). Their overall sleep grade is {grade}.\n\n"
        f"Write one personalised sentence of advice for THEIR night tonight.\n\n"
        f"FOCUS THE ADVICE ON: {focus}.\n"
        f"AVOID: {avoid}.\n\n"
        f"Write the sentence now."
    )

    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        temperature=0.9,  # encourage variation so repeat submissions feel fresh
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return message.content[0].text.strip()


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero-eyebrow">Lean Health · Sleep Assessment</div>
    <h1 class="hero-title">
        Feel <em>rested</em><br>
        through your<br>
        sleep journey.
    </h1>
    <p class="hero-subtitle">
        Three quick questions, one honest grade, and a personalised
        suggestion designed around <em>your</em> night.
    </p>
    <div class="section-label">The Assessment</div>
    """,
    unsafe_allow_html=True,
)

with st.form("sleep_form", clear_on_submit=False):
    hours_slept = st.number_input(
        "Hours of sleep last night",
        min_value=0.0,
        max_value=24.0,
        value=7.0,
        step=0.5,
        format="%.1f",
        help="Enter 0 for a sleepless night (time-to-fall-asleep will be ignored).",
    )

    latency_label = st.selectbox(
        "Time to fall asleep",
        list(FALL_ASLEEP_OPTIONS.keys()),
        index=0,
    )

    energy_level = st.slider(
        "Energy level today (1 = exhausted, 5 = fully rested)",
        min_value=1,
        max_value=5,
        value=3,
    )
    st.caption(f"Current selection: **{energy_level} / 5**")

    submitted = st.form_submit_button(
        "Reveal my sleep grade",
        type="primary",
    )

if submitted:
    latency_key = FALL_ASLEEP_OPTIONS[latency_label]
    grade = calculate_sleep_grade(hours_slept, latency_key, energy_level)
    color = GRADE_COLORS[grade]
    headline = GRADE_HEADLINES[grade]

    zero_hours = hours_slept == 0

    st.markdown(
        f"""
        <div class='section-label'>Your Grade</div>
        <div class='grade-card'>
            <div class='grade-letter' style='color:{color};'>{grade}</div>
            <div class='grade-headline'>{headline}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if zero_hours:
        st.caption("Time to fall asleep was not factored in (0 hours logged).")

    with st.spinner("Composing a tip tailored to tonight..."):
        try:
            insight = get_ai_insight(grade, hours_slept, latency_label, energy_level)
            st.markdown(
                f"""
                <div class='section-label'>Tonight's Suggestion</div>
                <div class='insight-card'>
                    <div class='insight-label'>Personalised for your night</div>
                    <div class='insight-text'>{insight}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception as exc:
            st.error(f"Could not generate a tip right now: {exc}")

st.markdown(
    "<div class='footer-note'>For general wellness only. Not medical advice.</div>",
    unsafe_allow_html=True,
)

