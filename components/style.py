"""All CSS of the app, mobile-first (375px first, then wider screens).

Palette (see .streamlit/config.toml):
  Steel Azure  #064789  dark band, headings, dark text
  Rich Cerulean #427AA1 active tab, links, secondary buttons
  Alice Blue   #EBF2FA  page background
  Sage Green   #679436  best price, savings, totals
  Lime Moss    #A5BE00  the main call to action (Search)
Layout reference: a dark band on top with pill tabs and a white horizontal search bar.
"""

import streamlit as st

NAVY = "#064789"
CERULEAN = "#427AA1"
ALICE = "#EBF2FA"
SAGE = "#679436"
LIME = "#A5BE00"
INK = "#0B2A47"
LINE = "#D3E0EE"
VERMILION = SAGE   # kept for older imports: the highlight colour is now Sage Green

CSS = f"""
<style>
:root {{--navy:{NAVY}; --cerulean:{CERULEAN}; --alice:{ALICE}; --sage:{SAGE}; --lime:{LIME};
        --ink:{INK}; --line:{LINE};}}
[data-testid="stToolbar"], [data-testid="stDecoration"], footer {{display:none !important;}}
header[data-testid="stHeader"] {{background: transparent;}}
.stApp {{background:var(--alice);}}
.block-container {{padding: 0 1rem 3rem; max-width: 760px;}}
a {{color:var(--cerulean);}}
h1, h2, h3, h4 {{color:var(--navy);}}

/* ---------- dark band (full width) with the top bar */
.st-key-hero, .st-key-band {{background:var(--navy); color:#fff; padding:1rem 0 1.4rem;
    box-shadow:0 0 0 100vmax var(--navy); clip-path:inset(-100vmax -100vmax 0 -100vmax);
    margin-bottom:1.2rem;}}
.st-key-hero h1, .st-key-hero h2, .st-key-hero h3, .st-key-band h1, .st-key-band h2 {{color:#fff;}}
.st-key-hero label p, .st-key-band label p {{color:#cfe0f0 !important; font-size:.8rem !important;}}
.topbar {{display:flex; justify-content:space-between; align-items:center; gap:12px; padding:.3rem 0 .9rem;}}
.logo {{display:flex; align-items:center; gap:8px; color:#fff !important; text-decoration:none !important;
        font-weight:800; font-size:1.3rem; letter-spacing:-.01em;}}
.logo-mark {{width:26px; height:26px; border-radius:8px; background:var(--lime); position:relative; flex:none;}}
.logo-mark::before {{content:""; position:absolute; left:6px; top:5px; width:9px; height:9px; border:2.5px solid var(--navy);
                     border-radius:50%;}}
.logo-mark::after {{content:""; position:absolute; left:16px; top:15px; width:6px; height:2.5px; background:var(--navy);
                    transform:rotate(45deg); border-radius:2px;}}
.top-links {{display:flex; align-items:center; gap:14px; font-size:.88rem; flex-wrap:wrap; justify-content:flex-end;}}
.top-links a {{color:#fff !important; text-decoration:none !important; font-weight:600;}}
a.avatar-link {{display:inline-flex; align-items:center; gap:6px;}}
.avatar {{display:inline-flex; width:26px; height:26px; border-radius:50%; background:var(--cerulean); color:#fff;
          font-size:.72rem; font-weight:800; align-items:center; justify-content:center; flex:none;}}
.avatar.big {{width:56px; height:56px; font-size:1.3rem; background:var(--lime); color:var(--navy);}}
.profile-head {{display:flex; align-items:center; gap:14px; margin:.4rem 0 .2rem;}}
.profile-head .pn {{font-size:1.4rem; font-weight:800; color:#fff; line-height:1.2;}}
.profile-head .pc2 {{color:#cfe0f0; font-size:.9rem;}}
.section-h {{font-size:1.25rem; font-weight:800; color:var(--navy); margin:1.2rem 0 .5rem;}}
.chip {{background:rgba(255,255,255,.13); border-radius:8px; padding:.35rem .7rem; font-size:.8rem; color:#fff;
        white-space:nowrap;}}
.st-key-band .rh-q {{color:#fff;}}
.st-key-band .rh-sub, .st-key-band .muted {{color:#cfe0f0 !important;}}
.st-key-band a.rh-back {{color:#cfe0f0 !important;}}
.st-key-band details.tr summary, .st-key-band .tr-in {{color:#dbe7f3;}}
.st-key-band .tr-in a {{color:var(--lime);}}
.st-key-band div[data-testid="stPopover"] button, .st-key-band div[data-testid="stButton"] button {{
    background:transparent; color:#fff; border:1px solid rgba(255,255,255,.5);}}

/* ---------- pill tabs (Link paste · Sourcing · Messages) */
.st-key-home_tab [role="radiogroup"] {{gap:.45rem;}}
.st-key-home_tab button {{min-width:0 !important; min-height:2.5rem; padding:0 .8rem !important; font-weight:700;
    border-radius:999px !important; background:transparent !important; color:#fff !important;
    border:1px solid rgba(255,255,255,.45) !important;}}
.st-key-home_tab button[aria-checked="true"] {{background:var(--cerulean) !important; border-color:var(--cerulean) !important;}}
.st-key-home_tab button p {{font-size:.84rem !important; white-space:nowrap; color:#fff !important;}}

/* ---------- search bar in the band */
.hero-title {{color:#fff; font-weight:800; line-height:1.15; letter-spacing:-.02em;
             font-size:clamp(1.65rem, 6.5vw, 2.4rem); margin:1.1rem 0 1rem;}}
.hero-sub {{color:#cfe0f0; margin:-.4rem 0 1rem; font-size:.95rem;}}
.st-key-hero div[data-testid="stForm"] {{border:none; padding:0;}}
.st-key-hero [data-testid="stTextInputRootElement"] input {{font-size:1rem; color:var(--ink);}}

/* ---------- how it works (below the band on the home page) */
.how {{display:grid; grid-template-columns:1fr; gap:10px; margin:.2rem 0 1rem;}}
.how-card {{background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px 16px;}}
.how-n {{display:inline-flex; width:26px; height:26px; border-radius:50%; background:var(--lime); color:var(--navy);
         font-weight:800; align-items:center; justify-content:center; font-size:.85rem; margin-bottom:6px;}}
.how-t {{font-weight:800; color:var(--navy); margin-bottom:2px;}}
.how-d {{color:#5b6f84; font-size:.88rem; line-height:1.4;}}
@media (min-width: 640px) {{ .how {{grid-template-columns:repeat(3, 1fr);}} }}

/* ---------- How SourceScan works (questions that open on tap) */
.faq {{margin:2rem 0 1rem;}}
.faq-title {{font-size:1.6rem; font-weight:800; color:var(--navy); margin:0 0 .6rem; padding:0;}}
.faq-cols {{display:grid; grid-template-columns:1fr; column-gap:2rem;}}
.faq-h {{font-size:.78rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; color:var(--cerulean);
         margin:1.1rem 0 .1rem;}}
details.faq-q {{border-bottom:1px solid #c5d3e2;}}
details.faq-q summary {{list-style:none; cursor:pointer; display:flex; justify-content:space-between; gap:12px;
                       padding:14px 2px; font-weight:700; color:var(--ink);}}
details.faq-q summary::-webkit-details-marker {{display:none;}}
details.faq-q summary::after {{content:""; flex:none; width:8px; height:8px; margin:5px 4px 0 0;
    border-right:2px solid var(--ink); border-bottom:2px solid var(--ink); transform:rotate(45deg);
    transition:transform .2s;}}
details.faq-q[open] summary::after {{transform:rotate(225deg); margin-top:9px;}}
.faq-a {{padding:0 2px 14px; color:#4b5d70; line-height:1.55; font-size:.92rem;}}
@media (min-width: 760px) {{ .faq-cols {{grid-template-columns:1fr 1fr;}} }}
.st-key-hero div[data-testid="stFormSubmitButton"] button, .st-key-hero .st-key-lp_go button {{
    height:2.5rem; min-height:2.5rem; border-radius:10px; font-size:1.05rem; font-weight:800; background:var(--lime) !important;
    border-color:var(--lime) !important; color:var(--navy) !important;}}
.st-key-hero div[data-testid="stFormSubmitButton"] button p, .st-key-hero .st-key-lp_go button p {{color:var(--navy) !important;}}
.hero-foot {{color:#cfe0f0; font-size:.8rem; margin-top:.8rem;}}
.st-key-hero div[data-testid="stFileUploader"] section {{background:#fff;}}
.st-key-hero div[data-testid="stExpander"] {{background:#fff; border-radius:10px;}}
.st-key-hero div[data-testid="stButton"] button[kind="tertiary"] p {{color:#dbe7f3 !important; text-decoration:underline;}}

/* ---------- white cards on Alice Blue */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {{background:#fff;}}
.tag {{display:inline-block; padding:2px 10px; border-radius:999px; font-size:.75rem; font-weight:600;
      margin-right:6px; border:1px solid var(--line);}}
.tag-sample {{background:#F2F6D6; color:#5A6800; border-color:#D9E49A;}}
.tag-est {{background:#E3EEF8; color:#1F5A86; border-color:#BCD3EA;}}
.tag-na {{background:#F1F1F1; color:#666; border-color:#DDD;}}
.tag-ok {{background:#E9F2E1; color:#3F6420; border-color:#BFD8A9;}}
.na {{color:#8a99aa; font-style:italic;}}
.muted {{color:#5b6f84; font-size:.88rem;}}
.score-pill {{display:inline-block; padding:2px 10px; border-radius:999px; color:#fff; font-weight:700;
      font-size:.82rem;}}
.kv td {{padding:4px 14px 4px 0; vertical-align:top;}}
.kv td:first-child {{color:#5b6f84; white-space:nowrap;}}
a.plain {{color:inherit; text-decoration:none;}}

/* ---------- results header */
.rh-back {{font-size:.9rem; color:#5b6f84 !important; text-decoration:none;}}
.rh-q {{font-size:1.5rem; font-weight:800; margin:.3rem 0 0; line-height:1.2; word-break:break-word; color:var(--navy);}}
.rh-sub {{color:#5b6f84; font-size:.9rem;}}

/* ---------- compact rows that stay side by side on phones (marked with .nowrap) */
div[data-testid="stHorizontalBlock"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .nowrap) {{
    flex-wrap:nowrap !important; gap:.6rem;}}
div[data-testid="stHorizontalBlock"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .nowrap) > div {{
    min-width:0 !important; width:auto !important; flex:1 1 0 !important;}}
div[data-testid="stHorizontalBlock"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] .nowrap) > div:last-child {{
    flex:0 0 min(40%, 190px) !important;}}
.nowrap {{display:none;}}
div[data-testid="stElementContainer"]:has(> div[data-testid="stMarkdown"] .nowrap) {{display:none;}}

/* ---------- product list: white result cards */
.plist {{margin:.2rem 0 .6rem;}}
a.pc {{display:flex; gap:12px; padding:12px; margin-bottom:10px; background:#fff; border:1px solid var(--line);
       border-radius:14px; color:var(--ink) !important; text-decoration:none !important;
       -webkit-tap-highlight-color:transparent; transition:box-shadow .15s;}}
a.pc:hover {{box-shadow:0 4px 14px rgba(6,71,137,.12);}}
a.pc:hover .pc-title {{color:var(--cerulean);}}
a.pc.top {{border:2px solid var(--sage);}}
.pc-img {{flex:none; width:96px; height:96px; border-radius:10px; object-fit:cover; background:var(--alice);}}
.pc-body {{flex:1; min-width:0; display:flex; flex-direction:column; gap:5px;}}
.pc-title {{font-weight:700; line-height:1.3; display:-webkit-box; -webkit-line-clamp:2;
            -webkit-box-orient:vertical; overflow:hidden; color:var(--navy);}}
.pc-meta {{display:flex; flex-wrap:wrap; gap:6px; align-items:center;}}
.mk, .sc, .save, .best-tag {{display:inline-block; padding:1px 8px; border-radius:6px; font-size:.74rem;
       font-weight:700; color:#fff; line-height:1.6;}}
.save {{background:var(--sage);}}
.best-tag {{background:var(--navy);}}
.src-tag {{display:inline-block; padding:0 7px; border-radius:6px; font-size:.7rem; font-weight:700;
           line-height:1.7; color:#5b6f84; border:1px solid #c5d3e2;}}
.src-tag.live {{color:#3F6420; border-color:#BFD8A9; background:#E9F2E1;}}
.pc-price {{font-size:1.5rem; font-weight:800; line-height:1.1; font-variant-numeric:tabular-nums; color:var(--navy);}}
.pc-price small {{font-size:.75rem; font-weight:500; color:#5b6f84; margin-left:4px;}}
a.pc.top .pc-price {{color:var(--sage);}}
.pc-na {{font-size:1rem; font-weight:600; color:#8a99aa; font-style:italic;}}
.pc-sub {{font-size:.78rem; color:#5b6f84; line-height:1.35;}}
.list-count {{font-size:.85rem; color:#5b6f84; padding-top:.55rem;}}
.foot {{font-size:.75rem; color:#7b8da0; padding:6px 0 4px; line-height:1.5;}}

/* ---------- delivered price receipt */
.rcpt {{margin:.4rem 0 .8rem;}}
.rr {{display:flex; justify-content:space-between; gap:12px; padding:9px 0; border-bottom:1px solid var(--line);}}
.rl {{flex:1; min-width:0; font-size:.95rem;}}
.rb {{display:block; color:#7b8da0; font-size:.78rem; line-height:1.35; margin-top:1px;}}
.ra {{text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums;}}
.ra-main {{display:block; font-weight:600;}}
.ra-per {{display:block; color:#7b8da0; font-size:.78rem;}}
.rr.rt {{border-bottom:none; border-top:2px solid var(--navy); margin-top:2px;}}
.rr.rt .rl, .rr.rt .ra-main {{font-weight:800; font-size:1.1rem; color:var(--navy);}}
.rr.rt .ra-main {{color:var(--sage);}}

/* ---------- messages */
.unread-badge {{display:inline-block; min-width:18px; padding:0 6px; border-radius:999px; background:var(--lime);
               color:var(--navy); font-size:.72rem; font-weight:800; text-align:center; line-height:18px;}}
a.msg-link {{font-weight:600;}}
.chat {{display:flex; flex-direction:column; gap:10px; margin:.4rem 0 .8rem;}}
.b {{max-width:88%; padding:10px 12px; border-radius:16px; line-height:1.45; font-size:.95rem; word-break:break-word;}}
.b.me {{align-self:flex-end; background:var(--navy); color:#fff; border-bottom-right-radius:4px;}}
.b.them {{align-self:flex-start; background:#fff; border:1px solid var(--line); border-bottom-left-radius:4px;}}
.b-en {{margin-top:7px; padding-top:7px; border-top:1px solid var(--line);}}
.b-sub {{font-size:.74rem; color:#5b6f84; margin-top:5px;}}
.b.me .b-sub {{color:#cfe0f0;}}
.mean {{margin-top:8px; background:#F2F6D6; color:#4a5600; border-radius:10px; padding:6px 9px; font-size:.85rem;}}
.terms {{margin-top:7px; display:flex; flex-wrap:wrap; gap:5px;}}
.term {{font-size:.72rem; font-weight:700; padding:1px 8px; border-radius:6px; background:#E3EEF8; color:#1F5A86;}}
.chat mark {{background:#E4EE9C; color:inherit; padding:0 2px; border-radius:3px;}}
.typing {{align-self:flex-start; color:#5b6f84; font-style:italic; font-size:.9rem; padding:4px 6px;}}
.chat-head {{margin-bottom:.3rem;}}
.chat-head .who {{font-size:1.2rem; font-weight:800; line-height:1.2; color:var(--navy);}}
.st-key-band .chat-head .who {{color:#fff;}}
.preview {{background:#fff; border:1px solid var(--line); border-radius:12px; padding:10px 12px;
           margin:.3rem 0 .5rem; font-size:.92rem;}}
.preview .bt {{color:#5b6f84; font-size:.82rem; margin-top:5px;}}
.deal-row {{display:flex; justify-content:space-between; gap:10px; padding:7px 0; font-size:.88rem;
            border-bottom:1px solid var(--line);}}
.deal-row .v {{text-align:right; font-weight:600;}}
.deal-row.new .v {{color:var(--sage);}}
.deal-row .src {{display:block; font-weight:400; font-size:.72rem; color:#8a99aa;}}
a.ib, a.oc {{display:block; padding:12px 14px; margin-bottom:8px; background:#fff; border:1px solid var(--line);
       border-radius:12px; color:var(--ink) !important; text-decoration:none !important;}}
.ib-top {{display:flex; justify-content:space-between; gap:8px; align-items:baseline;}}
.ib-name {{font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--navy);}}
a.ib.unread {{border-left:4px solid var(--lime);}}
.ib-time {{font-size:.75rem; color:#8a99aa; white-space:nowrap;}}
.ib-prod {{display:block; font-size:.82rem; color:#5b6f84; margin:2px 0;}}
.ib-last {{display:block; font-size:.88rem; color:#4b5d70; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}}
a.ib.unread .ib-last {{font-weight:600; color:var(--ink);}}

/* ---------- orders */
.tl {{list-style:none; padding:0; margin:.5rem 0 .8rem;}}
.tl li {{position:relative; padding:0 0 14px 24px; font-size:.92rem; line-height:1.3;}}
.tl li::before {{content:""; position:absolute; left:3px; top:3px; width:11px; height:11px; border-radius:50%;
                background:#c5d3e2;}}
.tl li::after {{content:""; position:absolute; left:8px; top:16px; bottom:0; width:1px; background:var(--line);}}
.tl li:last-child::after {{display:none;}}
.tl li.done::before {{background:var(--sage);}}
.tl li.now::before {{background:var(--lime); box-shadow:0 0 0 3px rgba(165,190,0,.3);}}
.tl li.todo {{color:#8a99aa;}}
.tl .t {{display:block; color:#8a99aa; font-size:.74rem;}}

/* ---------- AI translation strip */
details.tr {{font-size:.85rem; margin:.35rem 0 .2rem;}}
details.tr summary {{cursor:pointer; list-style:none; color:#4b5d70;}}
details.tr summary::-webkit-details-marker {{display:none;}}
details.tr summary::after {{content:" ›"; color:#8a99aa;}}
details.tr[open] summary::after {{content:" ⌄";}}
.tr-in {{padding:.4rem 0 .2rem .9rem; border-left:2px solid rgba(128,128,128,.3); color:#4b5d70; line-height:1.6;}}
.tr-in a {{color:var(--cerulean); font-weight:600; text-decoration:none;}}
.tr-in ul {{margin:.1rem 0 .2rem 1rem; padding:0;}}

@media (min-width: 640px) {{
  .st-key-hero, .st-key-band {{padding:1.2rem 0 1.8rem;}}
  .st-key-home_tab [role="radiogroup"] {{justify-content:flex-start;}}
  .st-key-home_tab button {{flex:0 0 auto !important; padding:0 1.1rem !important;}}
  .st-key-hero div[data-testid="stFormSubmitButton"], .st-key-hero .st-key-lp_go {{margin-top:1.75rem;}}
  .pc-img {{width:128px; height:128px;}}
  .pc-price {{font-size:1.7rem;}}
}}
</style>
"""

HOME_CSS = """
<style>
.block-container {max-width: 1080px;}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def inject_home():
    st.markdown(HOME_CSS, unsafe_allow_html=True)


def wide():
    st.markdown("<style>.block-container {max-width:1100px;}</style>", unsafe_allow_html=True)
