import streamlit as st
import json
import os
import plotly.graph_objects as go

st.set_page_config(
    page_title="Weekly App Review Pulse — Groww",
    page_icon="📊",
    layout="wide",
)

THEME_COLORS = ["#00D09C", "#4A90D9", "#F5A623", "#7B61FF", "#E74C3C"]
RATING_COLORS = ["#00D09C", "#55D6A9", "#F4B400", "#F5A623", "#E74C3C"]
RATING_DATA = [
    {"star": 5, "count": 107},
    {"star": 4, "count": 30},
    {"star": 3, "count": 44},
    {"star": 2, "count": 25},
    {"star": 1, "count": 174},
]

ACTION_ITEMS = [
    {
        "text": "Implement trailing stop-loss orders and expand technical indicator libraries to match competitor features.",
        "tag": "Feature Gaps",
        "color": "#00D09C",
    },
    {
        "text": "Redesign chart navigation to prevent accidental scalper mode triggers and ensure back buttons remain visible.",
        "tag": "UI/UX",
        "color": "#4A90D9",
    },
    {
        "text": "Audit support workflows to reduce automated responses and improve resolution times for critical account errors.",
        "tag": "Support",
        "color": "#F5A623",
    },
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(BASE_DIR, "data_seed")


@st.cache_data
def load_themes():
    with open(os.path.join(SEED_DIR, "themes.json"), "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_pulse():
    with open(os.path.join(SEED_DIR, "pulse.md"), "r", encoding="utf-8") as f:
        return f.read()


def stars_html(rating, size=14):
    full = int(rating)
    half = 0.3 <= (rating - full) < 0.8
    html = ""
    for i in range(5):
        if i < full:
            html += f'<span style="color:#F5A623;font-size:{size}px;">&#9733;</span>'
        elif i == full and half:
            html += f'<span style="color:#F5A623;font-size:{size}px;">&#9733;</span>'
        else:
            html += f'<span style="color:#DDE0E6;font-size:{size}px;">&#9733;</span>'
    return html


# ── Global CSS ──
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="st-"] { font-family: 'Inter', sans-serif !important; }
.block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 1280px; }
h1, h2, h3 { letter-spacing: -0.02em !important; }

/* Nav bar */
.nav-bar {
    display:flex; align-items:center; justify-content:space-between;
    padding:12px 0; margin-bottom:8px; border-bottom:1px solid #E8EBF0;
}
.nav-brand { display:flex; align-items:center; gap:10px; }
.nav-brand-icon { color:#00D09C; font-size:24px; }
.nav-brand-text { font-size:18px; font-weight:700; color:#1A1A2E; }
.nav-right { display:flex; align-items:center; gap:16px; }
.period-badge {
    display:inline-flex; align-items:center; gap:6px;
    padding:5px 14px; border-radius:20px; border:1px solid #E8EBF0;
    font-size:12px; font-weight:500; color:#52586B; background:#F5F6FA;
}
.groww-logo { font-size:18px; font-weight:700; color:#00D09C; }

/* Stat cards */
.stat-card {
    background:#fff; border-radius:14px; padding:20px;
    box-shadow:0 1px 3px rgba(0,0,0,0.04),0 4px 12px rgba(0,0,0,0.04);
    border:1px solid #E8EBF0; height:100%;
}
.stat-label { font-size:11px; font-weight:600; color:#8A8FA3; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:12px; }
.stat-value { font-size:30px; font-weight:700; color:#1A1A2E; letter-spacing:-0.03em; line-height:1.1; }
.stat-sub { font-size:12px; color:#8A8FA3; margin-top:4px; }

/* Section cards */
.section-card {
    background:#fff; border-radius:14px; padding:24px;
    box-shadow:0 1px 3px rgba(0,0,0,0.04),0 4px 12px rgba(0,0,0,0.04);
    border:1px solid #E8EBF0; margin-bottom:16px;
}
.section-title { font-size:17px; font-weight:700; color:#1A1A2E; margin-bottom:4px; }
.section-subtitle { font-size:12px; color:#8A8FA3; margin-bottom:16px; }

/* Theme items */
.theme-item {
    padding:16px; border-radius:12px; background:#F5F6FA;
    margin-bottom:12px; border-left:4px solid transparent;
}
.theme-name { font-size:15px; font-weight:700; color:#1A1A2E; }
.theme-desc { font-size:13px; color:#52586B; line-height:1.5; margin-top:8px; }
.pill {
    font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px;
    display:inline-block; margin-left:8px;
}
.progress-outer { width:100%; height:6px; background:#E8EBF0; border-radius:4px; margin:10px 0 8px; overflow:hidden; }
.progress-inner { height:100%; border-radius:4px; }

/* Action items */
.action-item { display:flex; gap:14px; padding:14px 16px; border-radius:12px; background:#F5F6FA; margin-bottom:10px; }
.action-num {
    width:28px; height:28px; border-radius:50%; background:#1A1A2E; color:#fff;
    font-size:13px; font-weight:700; display:flex; align-items:center; justify-content:center;
    flex-shrink:0;
}
.action-text { font-size:14px; font-weight:600; line-height:1.5; color:#1A1A2E; }

/* Quote items */
.quote-item { padding:16px; border-radius:12px; background:#F5F6FA; margin-bottom:12px; border-left:4px solid transparent; }
.quote-text { font-size:14px; font-style:italic; line-height:1.6; color:#1A1A2E; }
.quote-text::before { content:'\\201C'; font-size:20px; color:#8A8FA3; margin-right:2px; }
.quote-text::after { content:'\\201D'; font-size:20px; color:#8A8FA3; margin-left:2px; }

/* Alert box */
.alert-box {
    display:flex; align-items:center; gap:8px; padding:10px 14px; border-radius:10px;
    background:rgba(231,76,60,0.12); font-size:12px; font-weight:500; color:#93000a;
    margin-top:12px;
}

/* Rating row */
.rating-row { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.rating-label { width:40px; font-size:13px; font-weight:600; color:#1A1A2E; text-align:right; }
.rating-bar-outer { flex:1; height:8px; background:#E8EBF0; border-radius:4px; overflow:hidden; }
.rating-bar-inner { height:100%; border-radius:4px; }
.rating-val { font-size:12px; font-weight:600; color:#52586B; min-width:90px; text-align:right; }
.rating-val-crit { font-size:12px; font-weight:700; color:#E74C3C; min-width:90px; text-align:right; }

/* Hide Streamlit defaults */
#MainMenu {visibility:hidden;} footer {visibility:hidden;} header {visibility:hidden;}
</style>
""",
    unsafe_allow_html=True,
)


data = load_themes()
themes = data["themes"]
total_reviews = data["metadata"]["review_count"]
theme_count = data["metadata"]["theme_count"]

total_weighted = sum(t["avg_rating"] * t["count"] for t in themes)
total_rated = sum(t["count"] for t in themes)
avg_rating = round(total_weighted / total_rated, 1) if total_rated else 0

# ── NAV BAR ──
st.markdown(
    """
<div class="nav-bar">
    <div class="nav-brand">
        <span class="nav-brand-icon">📊</span>
        <span class="nav-brand-text">Weekly App Review Pulse</span>
    </div>
    <div class="nav-right">
        <span class="period-badge">📅 Aug 8 – Oct 16, 2026</span>
        <span class="groww-logo">Groww</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── STAT CARDS ──
c1, c2, c3, c4 = st.columns(4, gap="medium")

with c1:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-label">Reviews Analyzed</div>
        <div class="stat-value">{total_reviews}</div>
        <div class="stat-sub">Play Store reviews</div>
    </div>""",
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-label">Themes Identified</div>
        <div class="stat-value">{theme_count}</div>
        <div class="stat-sub">LLM-clustered categories</div>
    </div>""",
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""<div class="stat-card">
        <div class="stat-label">Avg Rating</div>
        <div class="stat-value">{avg_rating} {stars_html(avg_rating, 18)}</div>
        <div class="stat-sub" style="color:#E74C3C;">-0.3 vs. previous cycle</div>
    </div>""",
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        """<div class="stat-card">
        <div class="stat-label">Analysis Window</div>
        <div class="stat-value">10 wks</div>
        <div class="stat-sub">Aug 8 – Oct 16, 2026</div>
    </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── MAIN TWO-COLUMN LAYOUT ──
left_col, right_col = st.columns([7, 5], gap="large")

# ── LEFT COLUMN ──
with left_col:
    # Top Themes
    st.markdown(
        f"""<div class="section-card">
        <div class="section-title">🏷️ Top Themes</div>
        <div class="section-subtitle">Ranked by review volume ({total_reviews} total)</div>
    """,
        unsafe_allow_html=True,
    )

    for i, theme in enumerate(themes[:3]):
        color = THEME_COLORS[i]
        pct = round(theme["count"] / total_reviews * 100)
        pill_bg = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.12)"
        st.markdown(
            f"""<div class="theme-item" style="border-left-color:{color}">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <span class="theme-name">{theme['label']}</span>
                    <span class="pill" style="background:{pill_bg};color:{color};">{theme['count']} reviews</span>
                </div>
                <div style="font-size:13px;font-weight:700;">{stars_html(theme['avg_rating'])} {theme['avg_rating']:.1f}</div>
            </div>
            <div class="progress-outer">
                <div class="progress-inner" style="width:{pct}%;background:{color};"></div>
            </div>
            <div style="display:flex;justify-content:flex-end;font-size:12px;font-weight:700;color:#8A8FA3;margin-top:-4px;">{pct}%</div>
            <div class="theme-desc">{theme['description']}</div>
        </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Suggested Actions
    st.markdown(
        """<div class="section-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div class="section-title">💡 Suggested Actions</div>
                <div class="section-subtitle">Data-informed interventions for product sprint</div>
            </div>
            <span class="pill" style="background:rgba(0,208,156,0.12);color:#00533c;">Q4 Priority</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    for i, action in enumerate(ACTION_ITEMS):
        pill_bg = f"rgba({int(action['color'][1:3],16)},{int(action['color'][3:5],16)},{int(action['color'][5:7],16)},0.12)"
        st.markdown(
            f"""<div class="action-item">
            <div class="action-num">{i+1}</div>
            <div>
                <div class="action-text">{action['text']}</div>
                <div style="margin-top:6px;"><span class="pill" style="background:{pill_bg};color:{action['color']};">{action['tag']}</span></div>
            </div>
        </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ── RIGHT COLUMN ──
with right_col:
    # User Voices
    st.markdown(
        """<div class="section-card">
        <div class="section-title">💬 User Voices</div>
        <div class="section-subtitle">Verbatim quotes from Play Store reviews</div>
    """,
        unsafe_allow_html=True,
    )

    quote_data = [
        {"text": "Customer care is not easy to reach nor is able to solve the issues properly.", "rating": 2, "color": THEME_COLORS[2]},
        {"text": "Scalper button placement is terrible; whenever I hit back from a chart, it accidentally triggers scalping.", "rating": 2, "color": THEME_COLORS[1]},
        {"text": "I'm talking about Trade directly from charts i.e., like Dhan you can simply drag drop SL and target levels.", "rating": 3, "color": THEME_COLORS[0]},
    ]

    for q in quote_data:
        st.markdown(
            f"""<div class="quote-item" style="border-left-color:{q['color']}">
            <div style="margin-bottom:6px;">{stars_html(q['rating'], 13)}</div>
            <div class="quote-text">{q['text']}</div>
        </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Review Distribution (Donut)
    st.markdown(
        f"""<div class="section-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div class="section-title">🍩 Review Distribution</div>
                <div class="section-subtitle">Across {theme_count} theme clusters</div>
            </div>
            <span class="pill" style="background:#F5F6FA;color:#52586B;">{total_reviews} Total</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    fig = go.Figure(
        data=[
            go.Pie(
                labels=[t["label"] for t in themes],
                values=[t["count"] for t in themes],
                hole=0.6,
                marker=dict(colors=THEME_COLORS[: len(themes)]),
                textinfo="percent",
                textfont=dict(size=11, family="Inter"),
                hovertemplate="<b>%{label}</b><br>%{value} reviews (%{percent})<extra></extra>",
                sort=False,
            )
        ]
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(size=11, family="Inter"),
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[
            dict(
                text=f"<b>{total_reviews}</b><br><span style='font-size:11px;color:#8A8FA3;'>reviews</span>",
                x=0.5,
                y=0.5,
                font=dict(size=22, family="Inter", color="#1A1A2E"),
                showarrow=False,
            )
        ],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # Rating Breakdown
    st.markdown(
        f"""<div class="section-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div class="section-title">📊 Rating Breakdown</div>
                <div class="section-subtitle">Star tier distribution</div>
            </div>
            <span class="pill" style="background:#F5F6FA;color:#52586B;">{avg_rating} Avg</span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    rating_total = sum(r["count"] for r in RATING_DATA)
    for i, r in enumerate(RATING_DATA):
        pct = round(r["count"] / rating_total * 100, 1)
        color = RATING_COLORS[i]
        is_critical = r["star"] == 1 and pct > 40
        val_class = "rating-val-crit" if is_critical else "rating-val"
        st.markdown(
            f"""<div class="rating-row">
            <div class="rating-label">{r['star']} <span style="color:#F5A623;">&#9733;</span></div>
            <div class="rating-bar-outer"><div class="rating-bar-inner" style="width:{pct}%;background:{color};"></div></div>
            <div class="{val_class}">{r['count']} ({pct}%)</div>
        </div>""",
            unsafe_allow_html=True,
        )

    one_star_pct = round(RATING_DATA[-1]["count"] / rating_total * 100, 1)
    if one_star_pct > 30:
        st.markdown(
            f"""<div class="alert-box">
            ⚠️ 1-star ratings represent {one_star_pct}% of feedback — heavily driven by order execution freezes and support gaps.
        </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ── PULSE TEXT (expandable) ──
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
with st.expander("📄 View Full Pulse Note"):
    st.markdown(load_pulse())

# ── FOOTER ──
st.markdown(
    """<div style="display:flex;justify-content:space-between;font-size:12px;color:#8A8FA3;
    border-top:1px solid #E8EBF0;padding:16px 0;margin-top:16px;">
    <span>Groww Product Intelligence &bull; Weekly App Review Pulse</span>
    <span>Updated weekly &bull; Internal analytics</span>
</div>""",
    unsafe_allow_html=True,
)
