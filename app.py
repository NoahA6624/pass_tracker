"""
Pass Recorder - Florida Gators Match Tracker
Standalone companion app for recording successful passes.
Run: streamlit run pass_app.py --server.port 8502
Access from phone: http://[laptop-ip]:8502
"""

import streamlit as st
import json
import os
import time
from datetime import datetime, timezone

# ─────────────────────────────────────────────
# FILE PATH CONSTANTS
# ─────────────────────────────────────────────
PASS_EVENTS_FILE = "event_logs/pass_events.json"
SETTINGS_FILE    = "assets/settings.json"

MY_TEAM = "Florida Gators"

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Pass Recorder",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;700;900&display=swap');

:root {
    --gator-orange: #FA4616;
    --gator-blue:   #0021A5;
    --dark-bg:      #0d0d0d;
    --card-bg:      #161616;
    --border:       #2a2a2a;
    --text-muted:   #888;
    --text-bright:  #f0f0f0;
    --success:      #00ff88;
}

.stApp {
    background-color: var(--dark-bg);
    color: var(--text-bright);
    font-family: 'Inter', sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }

/* Hide Streamlit's back button, deploy button, and toolbar */
[data-testid="stSidebarNav"] { display: none; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
a[href*="/_stcore/"] { display: none !important; }
.st-emotion-cache-h4xjwg { display: none !important; }
.st-emotion-cache-1dp5vir { display: none !important; }
/* The back/forward nav bar that can appear at top */
[data-testid="stPageLink"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
}

/* Big tap-friendly buttons — explicit dark bg, never white-on-white */
.stButton > button {
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 900 !important;
    font-size: 1.6rem !important;
    min-height: 7rem !important;
    width: 100% !important;
    transition: transform 0.1s ease !important;
    background: #1a1a1a !important;
    border: 3px solid #3a3a3a !important;
    color: #FA4616 !important;
}
.stButton > button:active { transform: scale(0.96) !important; }
.stButton > button:hover  { border-color: #FA4616 !important; }

/* Gators pass button */
.btn-gator > button {
    background: #FA4616 !important;
    color: #0021A5 !important;
    min-height: 6rem !important;
    border-color: #c73510 !important;
}

/* Clock control buttons */
.btn-clock > button {
    font-size: 1.4rem !important;
    min-height: 3.5rem !important;
    color: #FA4616 !important;
    background: #1a1a1a !important;
    border: 2px solid #3a3a3a !important;
}
.btn-clock > button:hover {
    background: #242424 !important;
    border-color: #FA4616 !important;
    color: #FA4616 !important;
}
.btn-clock > button:focus,
.btn-clock > button:active {
    background: #1a1a1a !important;
    color: #FA4616 !important;
    outline: none !important;
    box-shadow: none !important;
}

/* Clock display */
.clock-bar {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    text-align: center;
    margin-bottom: 0.75rem;
}
.clock-val {
    font-family: 'Bebas Neue', monospace;
    font-size: 3.5rem;
    letter-spacing: 0.1em;
    line-height: 1;
}
.clock-live    { color: var(--success); }
.clock-stopped { color: #ff4444; }
.clock-meta {
    font-size: 0.8rem;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    margin-top: 0.3rem;
}

/* Count display */
.count-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem;
    text-align: center;
    margin-bottom: 0.75rem;
}
.count-label {
    font-size: 0.7rem;
    color: var(--text-muted);
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.count-val {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem;
    line-height: 1.1;
}

/* Team label */
.team-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.3rem;
    letter-spacing: 0.08em;
    margin: 0.75rem 0 0.4rem 0;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid var(--border);
}
.label-gators { color: var(--gator-orange); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def load_json(path: str, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(path: str, data):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def format_clock(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"

def tick_clock():
    if st.session_state.clock_running and st.session_state.clock_last_tick is not None:
        now = time.time()
        st.session_state.clock_seconds  += now - st.session_state.clock_last_tick
        st.session_state.clock_last_tick = now

def log_pass(team: str):
    now_local  = datetime.now()
    now_utc    = datetime.now(timezone.utc)
    clock_secs = st.session_state.clock_seconds
    elapsed    = (time.time() - st.session_state.clock_start_epoch) if st.session_state.clock_start_epoch else 0.0
    entry = {
        "event_type":                  "Pass",
        "team":                        team,
        "period":                      st.session_state.period,
        "game_clock":                  format_clock(clock_secs),
        "game_clock_seconds":          round(clock_secs, 1),
        "elapsed_since_start":         format_clock(elapsed),
        "elapsed_since_start_seconds": round(elapsed, 1),
        "local_time":                  now_local.strftime("%Y-%m-%d %H:%M:%S"),
        "utc_time":                    now_utc.strftime("%Y-%m-%d %H:%M:%SZ"),
    }
    passes = load_json(PASS_EVENTS_FILE, [])
    passes.append(entry)
    save_json(PASS_EVENTS_FILE, passes)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

def init_state():
    defaults = {
        "clock_running":     False,
        "clock_seconds":     0.0,
        "clock_last_tick":   None,
        "clock_start_epoch": None,
        "period":            1,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
tick_clock()

# ─────────────────────────────────────────────
# LOAD SETTINGS
# ─────────────────────────────────────────────

settings      = load_json(SETTINGS_FILE, {})
opp_name      = settings.get("opponent_name", "Opponent")
opp_primary   = settings.get("opponent_color", "#6633CC")
opp_secondary = settings.get("opponent_color_secondary", "#FFFFFF")

st.markdown(f"""
<style>
.btn-opp > button {{
    background: {opp_primary} !important;
    color: {opp_secondary} !important;
    border-color: {opp_primary} !important;
}}
.label-opp {{ color: {opp_primary}; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CLOCK DISPLAY
# ─────────────────────────────────────────────

clock_str     = format_clock(st.session_state.clock_seconds)
period_suffix = {1: "ST", 2: "ND", 3: "RD"}.get(st.session_state.period, "TH")
clock_cls     = "clock-live" if st.session_state.clock_running else "clock-stopped"
status        = "🟢 LIVE" if st.session_state.clock_running else "🔴 STOPPED"

st.markdown(f"""
<div class="clock-bar">
    <div class="clock-val {clock_cls}">{clock_str}</div>
    <div class="clock-meta">{status} &nbsp;|&nbsp; {st.session_state.period}{period_suffix} HALF</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CLOCK CONTROLS
# ─────────────────────────────────────────────

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown('<div class="btn-clock">', unsafe_allow_html=True)
    if not st.session_state.clock_running:
        if st.button("▶ Start Clock", key="start", use_container_width=True):
            now = time.time()
            if st.session_state.clock_start_epoch is None:
                st.session_state.clock_start_epoch = now
            st.session_state.clock_last_tick = now
            st.session_state.clock_running   = True
            st.rerun()
    else:
        if st.button("⏸ Stop Clock", key="stop", use_container_width=True):
            tick_clock()
            st.session_state.clock_running   = False
            st.session_state.clock_last_tick = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="btn-clock">', unsafe_allow_html=True)
    if st.button("↺ Clock Reset", key="reset", use_container_width=True):
        st.session_state.clock_running     = False
        st.session_state.clock_seconds     = 0.0
        st.session_state.clock_last_tick   = None
        st.session_state.clock_start_epoch = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    st.markdown(f'<div style="text-align:center;font-family:Bebas Neue,sans-serif;font-size:1.8rem;padding-top:0.3rem;color:#FA4616;">{st.session_state.period}</div>', unsafe_allow_html=True)

with c4:
    st.markdown('<div class="btn-clock">', unsafe_allow_html=True)
    if st.button("◀◀ Previous Period", key="prev_period", use_container_width=True):
        if st.session_state.period > 1:
            st.session_state.period -= 1
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with c5:
    st.markdown('<div class="btn-clock">', unsafe_allow_html=True)
    if st.button("▶▶ Next Period", key="next_period", use_container_width=True):
        st.session_state.period += 1
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

    # ─────────────────────────────────────────────
    # PASS COUNTS
    # ─────────────────────────────────────────────
tab_pass, tab_settings = st.tabs(["⚽  PASS RECORDER", "⚙️  SETTINGS"])

with tab_pass:
    passes_data = load_json(PASS_EVENTS_FILE, [])
    gator_count = sum(1 for p in passes_data if p.get("team") == MY_TEAM)
    opp_count   = sum(1 for p in passes_data if p.get("team") == opp_name)

    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown(f"""
        <div class="count-card">
            <div class="count-label">Gators Passes</div>
            <div class="count-val" style="color:#FA4616;">{gator_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with cc2:
        st.markdown(f"""
        <div class="count-card">
            <div class="count-label">{opp_name[:14]} Passes</div>
            <div class="count-val" style="color:{opp_primary};">{opp_count}</div>
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # PASS BUTTONS
    # ─────────────────────────────────────────────
    pass1, pass2 = st.columns(2)
    with pass1:
        st.markdown('<div class="team-label label-gators">🐊 FLORIDA GATORS</div>', unsafe_allow_html=True)
        st.markdown('<div class="btn-gator">', unsafe_allow_html=True)
        if st.button("⚽  GATORS PASS", key="gator_pass", use_container_width=True):
            log_pass(MY_TEAM)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    with pass2:
        st.markdown(f'<div class="team-label label-opp">{opp_name.upper()}</div>', unsafe_allow_html=True)
        st.markdown('<div class="btn-opp">', unsafe_allow_html=True)
        if st.button(f"⚽  {opp_name.upper()} PASS", key="opp_pass", use_container_width=True):
            log_pass(opp_name)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # AUTO-REFRESH
    # ─────────────────────────────────────────────

    auto = st.checkbox("Auto-refresh clock (1s)", value=False)
    if auto and st.session_state.clock_running:
        time.sleep(1)
        st.rerun()

with tab_settings:
    st.markdown("**⚙️ MATCH SETTINGS**")
    st.caption("Changes take effect on next app reload.")

    with st.form("pass_settings_form"):
        opp_name_input = st.text_input("Opponent Name", value=opp_name)
        sc1, sc2 = st.columns(2)
        with sc1:
            opp_color_input = st.color_picker(
                "Opponent Primary Color (button background)",
                value=opp_primary
            )
        with sc2:
            opp_color_secondary_input = st.color_picker(
                "Opponent Secondary Color (button text)",
                value=opp_secondary
            )

        submitted = st.form_submit_button("💾 SAVE SETTINGS", use_container_width=True)
        if submitted:
            settings["opponent_name"]            = opp_name_input
            settings["opponent_color"]           = opp_color_input
            settings["opponent_color_secondary"] = opp_color_secondary_input
            import os
            os.makedirs(os.path.dirname(SETTINGS_FILE) if os.path.dirname(SETTINGS_FILE) else ".", exist_ok=True)
            with open(SETTINGS_FILE, "w") as _f:
                import json as _json
                _json.dump(settings, _f, indent=2)
            st.success("Settings saved! Reload the app to see button color changes.")

    st.markdown("---")
    st.markdown("**📁 PASS DATA**")
    passes_total = load_json(PASS_EVENTS_FILE, [])
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Passes Logged", len(passes_total))
        st.caption(f"Saved to: `{PASS_EVENTS_FILE}`")
    with c2:
        if st.button("🗑️ Clear All Passes", use_container_width=True):
            save_json(PASS_EVENTS_FILE, [])
            st.warning("All pass events cleared.")
            st.rerun()

    st.markdown("---")
    st.markdown("**📂 FILE PATHS**")
    st.code(f'''
PASS_EVENTS_FILE = "{PASS_EVENTS_FILE}"
SETTINGS_FILE    = "{SETTINGS_FILE}"
''', language="python")