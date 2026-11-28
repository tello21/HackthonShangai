"""All CSS of the app, mobile-first (375px first, then wider screens).

Design reference: the team's "Scoutr — Search. Compare. Trust. Buy." mock-up.
  Ink        #162638  text and headings
  Muted      #627384  secondary text
  Blue       #17639c  links, brand mark, highlights
  Lime       #d9f077  the main call to action, "your quantity", marker strokes under key numbers
  Deep blue  #103d5d  closing band
  Background #fbfbf7, soft sections #f3f7f7, lines #dde4e6
Fonts: Space Grotesk (headings, prices, scores) and Inter (text), Google Fonts.
"""

import streamlit as st

INK = "#162638"
MUTED = "#627384"
BLUE = "#17639c"
LIME = "#d9f077"
DEEP = "#103d5d"
BG = "#fbfbf7"
SOFT = "#f3f7f7"
LINE = "#dde4e6"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root {{--navy:{INK}; --ink:{INK}; --muted:{MUTED}; --cerulean:{BLUE}; --blue:{BLUE}; --hl:{LIME}; --deep:{DEEP};
        --bg:{BG}; --alice:{SOFT}; --soft:{SOFT}; --line:{LINE};
        --font:Inter, ui-sans-serif, system-ui, sans-serif; --display:'Space Grotesk', Inter, sans-serif;
        --shadow:0 12px 40px #19394b0b;}}
/* Inter everywhere except Streamlit's icon font (expander arrows, etc.) */
.stApp, .stApp p, .stApp div, .stApp a, .stApp label, .stApp button, .stApp input, .stApp textarea,
.stApp li, .stApp td, .stApp th, .stApp summary, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stApp span:not([data-testid="stIconMaterial"]) {{font-family:var(--font);}}
.stApp h1, .stApp h2, .stApp h3, .disp, .brand, .pc-price, .trust-num, .tier-p, .kf-v, .ps-title, .sec-h,
.rh-q, .hero-h1, .h2, .step-t, .endcta-h, .summary-price {{font-family:var(--display) !important;}}
[data-testid="stToolbar"], [data-testid="stDecoration"], footer {{display:none !important;}}
/* Streamlit's invisible 60px header sits over our top bar: let clicks through to the logo and links,
   but keep its own buttons (sidebar/filters toggle) clickable */
header[data-testid="stHeader"] {{background:transparent; pointer-events:none;}}
header[data-testid="stHeader"] button, header[data-testid="stHeader"] a,
header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"] {{pointer-events:auto;}}
a.brand {{padding:6px 10px 6px 0; position:relative; z-index:1;}}
.stApp {{background:var(--bg); color:var(--ink);}}
.block-container {{padding:0 1.1rem 0; max-width:1190px;}}
a {{color:var(--blue);}}
h1, h2, h3, h4 {{color:var(--ink);}}
.stApp button[kind="primary"], .stApp button[kind="primaryFormSubmit"] {{background:var(--hl); border-color:var(--hl);
    color:#21372a; font-weight:700; border-radius:9px;}}
.stApp button[kind="primary"]:hover, .stApp button[kind="primaryFormSubmit"]:hover {{background:#cce866;
    border-color:#cce866; color:#21372a;}}
.stApp button[kind="primary"] p, .stApp button[kind="primaryFormSubmit"] p {{color:#21372a; font-weight:700;}}
.stApp button[kind="secondary"] {{border-radius:9px; border-color:#bfcfd5; color:#245974; font-weight:600;}}

/* ---------- top bar (light, full width, line below) */
.st-key-band, .st-key-hero {{background:#fff; box-shadow:0 0 0 100vmax #fff, 0 1px 0 100vmax var(--line);
    clip-path:inset(-100vmax -100vmax -1px -100vmax); margin-bottom:.4rem; padding:0;}}
.topbar {{display:flex; justify-content:space-between; align-items:center; gap:18px; min-height:70px;}}
.brand {{display:flex; align-items:center; gap:10px; color:var(--ink) !important; text-decoration:none !important;
         font-weight:700; font-size:1.35rem; letter-spacing:-.05em;}}
.mark {{width:33px; height:33px; border-radius:10px; background:#145f97; display:grid; place-items:center; flex:none;}}
.mark svg {{width:21px;}}
.top-links {{display:flex; align-items:center; gap:22px; font-size:13px; font-weight:600; flex-wrap:wrap;
             justify-content:flex-end;}}
.top-links a {{color:#435565 !important; text-decoration:none !important;}}
.top-links a:hover, .top-links a.on {{color:var(--blue) !important;}}
.top-links .sm {{display:none;}}
.locale {{border:1px solid var(--line); border-radius:10px; background:#fff; padding:8px 12px; font-size:12px;
          color:var(--ink); white-space:nowrap;}}
a.avatar-link {{display:inline-flex; align-items:center; gap:6px;}}
.avatar {{display:inline-flex; width:26px; height:26px; border-radius:50%; background:var(--blue); color:#fff;
          font-size:.72rem; font-weight:700; align-items:center; justify-content:center; flex:none;}}
.avatar.big {{width:56px; height:56px; font-size:1.3rem; background:var(--hl); color:#21372a;}}
.profile-head {{display:flex; align-items:center; gap:14px; margin:1.6rem 0 .4rem;}}
.profile-head .pn {{font-family:var(--display); font-size:1.8rem; font-weight:600; color:var(--ink); line-height:1.2;
                    letter-spacing:-.03em;}}
.profile-head .pc2 {{color:var(--muted); font-size:.9rem;}}
.section-h {{font-family:var(--display); font-size:1.35rem; font-weight:600; color:var(--ink); margin:1.4rem 0 .5rem;
             letter-spacing:-.03em;}}
.chip {{border:1px solid var(--line); background:#fff; border-radius:100px; padding:6px 12px; font-size:12px;
        color:#4c6373; font-weight:600; white-space:nowrap;}}

/* ---------- page heading used by inner pages (Results, Compare, Checkout...) */
.pagehero {{text-align:center; padding:2.6rem 0 .6rem;}}
.sectiontag {{font-size:11px; text-transform:uppercase; color:#2a6c80; letter-spacing:.17em; font-weight:700;
              margin-bottom:12px;}}
.pagehero .ph1 {{font-family:var(--display); font-size:clamp(32px, 4vw, 54px); line-height:1.08; font-weight:600;
                 letter-spacing:-.055em; color:var(--ink); margin:0 0 12px; word-break:break-word;}}
.pagehero .psub {{font-size:15px; color:var(--muted); max-width:740px; margin:0 auto;}}
.progress {{display:flex; gap:10px; align-items:center; justify-content:center; margin:14px 0 22px; font-size:12px;
            color:#8798a4; flex-wrap:wrap;}}
.progress span {{border-radius:20px; padding:5px 11px; border:1px solid var(--line); background:#fff;}}
.progress span.on {{color:#236448; background:#e8f5da; border-color:#c9dfb4;}}

/* ---------- home: hero */
.hero {{text-align:center; padding:4.2rem 0 1.6rem;}}
.hero-h1 {{font-size:clamp(40px, 5.1vw, 76px); line-height:1.06; font-weight:600; letter-spacing:-.064em;
           color:var(--ink); margin:0 auto 20px; max-width:930px;}}
.hero-h1 .hl {{color:var(--blue);}}
.hero-sub {{font-size:18px; max-width:690px; margin:0 auto 34px !important; line-height:1.7; color:var(--muted);
            text-align:center;}}
.st-key-searchpanel {{background:#fff; border:1px solid #d8e0e1; box-shadow:0 12px 55px #1c425214; border-radius:17px;
                      padding:22px 22px 24px; margin-bottom:8px;}}
.st-key-searchpanel div[data-testid="stForm"] {{border:none; padding:0; margin:0;}}
.st-key-searchpanel label {{min-height:0; margin-bottom:6px;}}
.st-key-searchpanel label p {{font-weight:600 !important; font-size:11.5px !important; color:#586d7e !important;}}
.st-key-searchpanel div[data-baseweb="input"], .st-key-searchpanel div[data-baseweb="select"] > div {{
    min-height:50px; border-radius:9px; background:#fff;}}
.st-key-searchpanel input {{font-size:15px; min-height:48px;}}
/* the chosen country / currency sat low in the taller box: centre it vertically */
.st-key-searchpanel div[data-baseweb="select"] > div {{align-items:center;}}
.st-key-searchpanel div[data-baseweb="select"] > div > div:first-child {{padding-top:0 !important;
    padding-bottom:0 !important; display:flex; align-items:center; align-self:stretch;}}
.st-key-searchpanel div[data-baseweb="select"] > div > div:first-child > div {{line-height:1.2;}}
.st-key-searchpanel div[data-testid="stFormSubmitButton"] button, .st-key-searchpanel button[kind="primaryFormSubmit"] {{
    height:48px; min-height:48px; padding:0 22px; white-space:nowrap; border-radius:9px;}}
/* as in the mock-up: below 1000px the query and the button take a full row each */
@media (max-width: 1000px) {{
  .st-key-searchpanel div[data-testid="stHorizontalBlock"] {{flex-wrap:wrap !important;}}
  .st-key-searchpanel div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {{
      flex:1 1 calc(33% - 1rem) !important; min-width:120px !important;}}
  .st-key-searchpanel div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:first-child,
  .st-key-searchpanel div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:last-child {{
      flex:1 1 100% !important;}}
}}
.markets {{display:flex; gap:12px; align-items:center; justify-content:center; margin-top:26px; color:#7b8794;
           font-size:12px; flex-wrap:wrap;}}
.market {{border:1px solid var(--line); border-radius:7px; padding:3px 11px; background:#fff; color:#627382;}}
.micro {{font-size:12px; color:#758593; margin-top:14px; text-align:center;}}

/* ---------- home: sections */
.fullbleed, .st-key-trustsec {{background:var(--soft); box-shadow:0 0 0 100vmax var(--soft);
    clip-path:inset(0 -100vmax); border-top:1px solid #e7eced;}}
.sec {{padding:64px 0;}}
.st-key-trustsec {{padding:64px 0 56px;}}
.sectionhead {{max-width:750px; margin-bottom:36px;}}
.h2 {{font-size:clamp(30px, 3vw, 46px); line-height:1.17; font-weight:600; letter-spacing:-.04em; color:var(--ink);
      margin:0 0 14px;}}
.lead {{font-size:16px; color:var(--muted); line-height:1.6;}}
.steps {{display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:18px;}}
.step {{padding:28px; border:1px solid var(--line); border-radius:13px; background:#fff; min-height:220px;}}
.stepno {{display:inline-grid; place-items:center; width:38px; height:38px; background:#e9f4d3; border-radius:11px;
          color:#365936; font-family:var(--display); font-size:18px; font-weight:700; margin-bottom:18px;}}
.step-t {{font-size:20px; line-height:1.28; font-weight:600; letter-spacing:-.03em; color:var(--ink); margin-bottom:10px;}}
.step p {{font-size:14px; margin:0; color:var(--muted); line-height:1.6;}}
.principles {{display:grid; gap:16px; margin-top:24px;}}
.principle {{display:flex; align-items:start; gap:15px; border-bottom:1px solid var(--line); padding-bottom:16px;}}
.principle .num {{color:var(--blue); font-weight:700; font-size:12px; margin-top:3px;}}
.principle .pt {{font-weight:600; font-size:15px; color:var(--ink); margin-bottom:3px;}}
.principle p {{font-size:13px; margin:0; color:var(--muted); line-height:1.6;}}
.st-key-scorebox {{background:#fff; border:1px solid var(--line); border-radius:17px; padding:24px; box-shadow:var(--shadow);}}
.scorehead {{display:flex; align-items:start; justify-content:space-between; gap:20px; margin-bottom:4px;}}
.scorehead .disp {{font-size:21px; font-weight:600; letter-spacing:-.03em; color:var(--ink); line-height:1.25;}}
.st-key-mk_pick button {{padding:0 .6rem !important; min-height:2.2rem;}}
.st-key-mk_pick button p {{font-size:13px !important;}}
.samplechip {{background:#f4f6f7; border:1px solid #e4e9eb; color:#687e88; font-weight:600; border-radius:8px;
              padding:6px 10px; font-size:11px; white-space:nowrap;}}
.st-key-mk_pick button {{border-radius:100px !important;}}
.st-key-mk_pick button[aria-checked="true"] {{background:#eaf5dc !important; border-color:#b9d9aa !important;}}
.st-key-mk_pick button[aria-checked="true"] p {{color:#2f6447 !important;}}
.mk-intro {{font-size:13px; color:var(--muted); margin:2px 0 6px; line-height:1.55;}}
.mrow {{border-top:1px solid var(--line); padding:14px 0 12px;}}
.mrow-top {{display:grid; grid-template-columns:1fr 2fr 42px; align-items:center; gap:12px; font-size:13px;
            color:#41556a; font-weight:600;}}
.track {{height:7px; border-radius:15px; background:#e9edee; overflow:hidden;}}
.fill {{height:100%; background:#9bbcaf; border-radius:15px;}}
.mrow-top b {{text-align:right; color:var(--ink);}}
.mrow-body {{font-size:12.5px; color:#546879; line-height:1.55; margin-top:7px;}}
.mrow-body b {{color:#294657; font-weight:600;}}
.avail {{display:inline-block; font-size:10.5px; font-weight:700; border-radius:100px; padding:1px 8px; margin-left:6px;
         vertical-align:1px;}}
.avail.yes {{background:#e8f5da; color:#2f6447;}}
.avail.some {{background:#f6f4ed; color:#8a6b2b;}}
.avail.no {{background:#f3f5f6; color:#7c8b98;}}
.note {{font-size:12px; color:#7c8b98; margin-top:12px; line-height:1.55;}}
.ex {{display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;}}
.ex a {{display:inline-flex; gap:6px; align-items:center; font-size:12px; border:1px solid var(--line); border-radius:8px;
        padding:4px 8px; background:#fff; color:var(--ink) !important; text-decoration:none !important;}}
.faqgrid {{display:grid; grid-template-columns:.8fr 1.2fr; gap:70px; padding:64px 0;}}
details.fq {{border-top:1px solid #dce4e7;}}
details.fq:last-child {{border-bottom:1px solid #dce4e7;}}
details.fq summary {{cursor:pointer; list-style:none; padding:20px 30px 20px 0; font-weight:600; font-size:15px;
                     position:relative; color:var(--ink);}}
details.fq summary::-webkit-details-marker {{display:none;}}
details.fq summary::after {{content:'+'; font-size:22px; font-weight:400; position:absolute; right:4px; top:14px; color:#507185;}}
details.fq[open] summary::after {{content:'−';}}
details.fq p {{padding:0 20px 20px 0; margin:0; font-size:14px; line-height:1.8; color:var(--muted);}}
.endcta {{padding:60px 25px; background:var(--deep); text-align:center; color:#fff; border-radius:18px; margin:10px 0 50px;}}
.endcta-h {{font-size:clamp(28px, 3vw, 42px); font-weight:600; letter-spacing:-.04em; margin-bottom:10px; color:#fff;}}
.endcta p {{color:#c8d8e3; margin-bottom:22px;}}
a.cta {{display:inline-flex; align-items:center; background:var(--hl); color:#21372a !important; font-weight:700;
        border-radius:9px; padding:0 23px; height:48px; text-decoration:none !important;}}
@media (max-width: 950px) {{ .faqgrid {{gap:30px;}} }}
@media (max-width: 700px) {{
  .top-links {{gap:12px; font-size:13px;}} .top-links .hide-sm, .top-links .locale, .top-links .lg {{display:none;}}
  .top-links .sm {{display:inline;}} .topbar {{gap:10px; min-height:60px;}} .brand .mark {{width:30px; height:30px;}}
  .brand {{font-size:1.15rem;}}
  .hero {{padding:3rem 0 1.2rem;}} .hero-sub {{font-size:15px;}}
  .steps, .faqgrid {{grid-template-columns:1fr;}} .step {{min-height:auto;}}
  .sec, .faqgrid {{padding:44px 0;}} .st-key-trustsec {{padding:44px 0;}}
  .st-key-scorebox {{padding:18px;}}
}}

/* ---------- results: compact heading, 4 cards per row */
.pagehero.compact {{padding:1.3rem 0 0;}}
.pagehero.compact .sectiontag {{margin-bottom:6px;}}
.pagehero.compact .ph1 {{font-size:clamp(28px, 3vw, 40px); margin-bottom:4px;}}
.pagehero.compact .psub {{font-size:14px;}}
.pagehero.compact + .progress {{margin:10px 0 10px;}}
.st-key-rtools {{display:flex; flex-direction:column; align-items:center; gap:.2rem; margin-bottom:.2rem;}}
.st-key-rtools [data-testid="stMarkdownContainer"], .st-key-rtools details.tr {{text-align:center;}}
.grid {{display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:16px; margin:.4rem 0 1rem;}}
a.gc {{display:flex; flex-direction:column; background:#fff; border:1px solid var(--line); border-radius:13px;
       overflow:hidden; color:var(--ink) !important; text-decoration:none !important; transition:box-shadow .15s, transform .15s;}}
a.gc:hover {{box-shadow:0 14px 40px #19394b1a; transform:translateY(-2px);}}
.gc-media {{position:relative; display:block; aspect-ratio:4/3; background:#fff; border-bottom:1px solid var(--line);}}
.gc-media img {{width:100%; height:100%; object-fit:contain; padding:10px; display:block;}}
.gc-flags {{position:absolute; top:8px; left:8px; display:flex; flex-direction:column; gap:4px; align-items:flex-start;}}
.gc-flags .demo-tag {{background:#fff;}}
.gc-flags .warn-tag {{font-size:.66rem;}}
.gc-body {{display:flex; flex-direction:column; gap:10px; padding:12px 14px 14px; flex:1;}}
.gc-title {{font-family:var(--display); font-size:14.5px; font-weight:600; line-height:1.3; letter-spacing:-.01em;
            display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; min-height:2.6em;}}
a.gc:hover .gc-title {{color:var(--blue);}}
.gc-row {{display:flex; flex-direction:column; gap:2px; border-top:1px solid #e5eaed; padding-top:9px;}}
.gc-l {{font-size:10px; text-transform:uppercase; letter-spacing:.12em; font-weight:700; color:#7c8b98;}}
.gc-price {{font-family:var(--display); font-size:24px; font-weight:600; letter-spacing:-.04em; line-height:1.1;
            font-variant-numeric:tabular-nums;}}
.gc-price.na-price {{font-size:15px; color:#9aa8b5; font-style:italic; letter-spacing:0;}}
.gc-unit {{font-size:11.5px; color:var(--muted); line-height:1.35;}}
.gc-row .score-pill {{align-self:flex-start; font-size:.82rem; padding:3px 11px;}}
.list-count {{text-align:right;}}
@media (max-width: 1050px) {{ .grid {{grid-template-columns:repeat(3, minmax(0, 1fr));}} }}
@media (max-width: 760px) {{ .grid {{grid-template-columns:repeat(2, minmax(0, 1fr)); gap:10px;}} }}
@media (max-width: 420px) {{ .gc-price {{font-size:20px;}} .gc-row .score-pill {{font-size:.72rem; padding:2px 8px;}}
                            .list-count {{text-align:left;}} }}

/* ---------- inner panels (white cards) */
.st-key-panel {{background:#fff; border:1px solid var(--line); border-radius:14px; padding:22px;
    box-shadow:var(--shadow);}}
/* ---------- white cards on Alice Blue */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"]) {{background:#fff;}}
.tag {{display:inline-block; padding:2px 10px; border-radius:999px; font-size:.75rem; font-weight:600;
      margin-right:6px; border:1px solid var(--line);}}
.tag-sample {{background:#FFFBB8; color:#5C5400; border-color:#EDE36A;}}
.tag-est {{background:#E3EEF8; color:#1F5A86; border-color:#BCD3EA;}}
.tag-na {{background:#F1F1F1; color:#666; border-color:#DDD;}}
.tag-ok {{background:#E9F2E1; color:#3F6420; border-color:#BFD8A9;}}
.na {{color:#8a99aa; font-style:italic;}}
.est-note {{font-size:.78rem; color:#7b8da0; line-height:1.45;}}
.muted {{color:#5b6f84; font-size:.88rem;}}
.score-pill {{display:inline-block; padding:2px 10px; border-radius:999px; color:#fff; font-weight:700;
      font-size:.82rem;}}
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
a.pc.top {{border:2px solid var(--navy);}}
.pc-img {{flex:none; width:96px; height:96px; border-radius:10px; object-fit:cover; background:#fff; border:1px solid var(--line);}}
.pc-body {{flex:1; min-width:0; display:flex; flex-direction:column; gap:5px;}}
.pc-title {{font-weight:700; line-height:1.3; display:-webkit-box; -webkit-line-clamp:2;
            -webkit-box-orient:vertical; overflow:hidden; color:var(--navy);}}
.pc-meta {{display:flex; flex-wrap:wrap; gap:6px; align-items:center;}}
.mk, .sc, .save, .best-tag {{display:inline-block; padding:1px 8px; border-radius:6px; font-size:.74rem;
       font-weight:700; color:#fff; line-height:1.6;}}
.save {{background:var(--hl); color:var(--navy);}}
.best-tag {{background:var(--navy);}}
.pc-price {{font-size:1.5rem; font-weight:800; line-height:1.1; font-variant-numeric:tabular-nums; color:var(--navy);}}
.pc-price small {{font-size:.75rem; font-weight:500; color:#5b6f84; margin-left:4px;}}
a.pc.top .pc-price {{display:inline; align-self:flex-start; background:linear-gradient(transparent 52%, var(--hl) 52%);}}
.pc-na {{font-size:1rem; font-weight:600; color:#8a99aa; font-style:italic;}}
.pc-sub {{font-size:.78rem; color:#5b6f84; line-height:1.35;}}
.list-count {{font-size:.85rem; color:#5b6f84; padding-top:.55rem;}}
.foot {{font-size:.75rem; color:#7b8da0; padding:6px 0 4px; line-height:1.5;}}

.pc-why {{font-size:.76rem; color:#4b5d70; line-height:1.35;}}
.warn {{color:#B3261E; font-weight:700;}}
.demo-tag {{display:inline-block; padding:0 7px; border-radius:6px; font-size:.68rem; font-weight:700;
            line-height:1.7; color:#5b6f84; border:1px dashed #9AA8B6; text-transform:lowercase;}}
.warn-tag {{display:inline-block; padding:1px 9px; border-radius:6px; font-size:.74rem; font-weight:700;
            line-height:1.6; color:#fff; background:#B3261E;}}

/* ---------- product sheet */
.sec-h {{display:flex; align-items:center; gap:10px; font-size:1.3rem; font-weight:800; color:var(--navy);
         margin:1.6rem 0 .7rem; letter-spacing:-.01em;}}
.sec-n {{display:inline-flex; width:28px; height:28px; border-radius:50%; background:var(--hl); color:var(--navy);
         font-size:.9rem; font-weight:800; align-items:center; justify-content:center; flex:none;}}
.sub-h {{font-weight:800; color:var(--navy); margin:1rem 0 .5rem; font-size:1rem;}}
.sub-h span {{font-weight:500; color:#7b8da0; font-size:.8rem; margin-left:6px;}}
.ps {{display:flex; flex-direction:column; gap:14px; background:#fff; border:1px solid var(--line);
      border-radius:18px; padding:14px;}}
.ps-img {{width:100%; aspect-ratio:1/1; max-height:200px; object-fit:contain; border-radius:14px; background:#fff; border:1px solid var(--line);}}
.ps-info {{flex:1; min-width:0; display:flex; flex-direction:column; gap:8px;}}
.ps-tags {{display:flex; flex-wrap:wrap; gap:6px; align-items:center;}}
.ps-tags .tag {{margin-right:0;}}
.ps-title {{font-size:1.45rem; font-weight:800; line-height:1.2; color:var(--navy); letter-spacing:-.01em;}}
.ps-orig {{font-size:.85rem; color:#7b8da0;}}
.kfs {{display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; margin-top:4px;}}
.kf {{background:var(--alice); border-radius:12px; padding:10px 10px 8px;}}
.kf-v {{font-size:1.25rem; font-weight:800; color:var(--navy); line-height:1.1; font-variant-numeric:tabular-nums;}}
.kf-v small {{font-size:.75rem; font-weight:600; color:#5b6f84;}}
.kf-v .na {{font-size:.8rem; font-weight:500;}}
.kf-l {{font-size:.72rem; color:#5b6f84; margin-top:3px; text-transform:uppercase; letter-spacing:.04em; font-weight:600;}}
.facts {{display:flex; flex-wrap:wrap; gap:8px; margin:.6rem 0 1.2rem;}}
.facts .fact {{flex:1 1 200px;}}
.facts .fact.wide {{flex-basis:100%;}}
.fact {{background:#fff; border:1px solid var(--line); border-radius:12px; padding:10px 12px; min-width:0;}}
.fact.wide {{grid-column:1 / -1;}}
.fact-l {{font-size:.7rem; color:#7b8da0; text-transform:uppercase; letter-spacing:.05em; font-weight:700;}}
.fact-v {{font-size:.95rem; font-weight:600; color:var(--ink); margin-top:2px; line-height:1.35; word-break:break-word;}}
.fact.na-tile {{background:transparent; border-style:dashed;}}
.fact.na-tile .fact-v {{color:#9AA8B6; font-weight:500; font-style:italic;}}
.chip-b {{display:inline-block; margin:2px 6px 2px 0; padding:2px 10px; border-radius:999px; font-size:.8rem;
          background:#E3EEF8; color:#1F5A86; font-weight:600;}}
.tiers {{display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:8px; margin:.2rem 0 .3rem;}}
.tier {{position:relative; background:#fff; border:1px solid var(--line); border-radius:14px; padding:12px;}}
.tier.on {{border:2px solid var(--navy); padding:11px;}}
.tier-you {{position:absolute; top:-10px; right:10px; background:var(--hl); color:var(--navy); font-size:.68rem;
            font-weight:800; padding:1px 8px; border-radius:999px;}}
.tier-q {{font-size:.78rem; color:#5b6f84; font-weight:600;}}
.tier-p {{font-size:1.35rem; font-weight:800; color:var(--navy); line-height:1.2; font-variant-numeric:tabular-nums;}}
.tier-p small {{font-size:.72rem; font-weight:500; color:#7b8da0; margin-left:2px;}}
.tier-c {{display:flex; justify-content:space-between; gap:6px; font-size:.8rem; color:#5b6f84;}}
.tier-off {{font-weight:800; color:var(--navy); background:linear-gradient(transparent 50%, var(--hl) 50%);}}
.sup-name {{font-size:1.1rem; font-weight:800; color:var(--navy); margin-top:.8rem; line-height:1.25;}}
.sup-cn, .sup-city {{font-size:.85rem; color:#5b6f84;}}
@media (min-width: 640px) {{
  .ps {{flex-direction:row; padding:18px; gap:20px;}}
  .ps-img {{width:220px; height:220px; flex:none;}}
  .ps-title {{font-size:1.7rem;}}
}}

/* ---------- trust score: band pill + one bar per metric */
.score-pill.big {{font-size:1rem; padding:4px 14px;}}
.trust-head {{display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin-bottom:.3rem;}}
.trust-num {{font-size:2.4rem; font-weight:900; line-height:1; color:var(--navy);}}
.trust-num small {{font-size:1rem; color:#7b8da0; font-weight:600;}}
.tms {{margin:.6rem 0 .4rem;}}
.tm {{margin:0 0 10px;}}
.tm-top {{display:flex; justify-content:space-between; font-size:.88rem; font-weight:600; color:var(--ink);}}
.tm-top small {{color:#7b8da0; font-weight:500;}}
.tm-bar {{height:8px; background:#E3EBF3; border-radius:4px; overflow:hidden; margin:3px 0 2px;}}
.tm-fill {{height:100%; background:var(--cerulean); border-radius:4px;}}
.tm-why {{font-size:.76rem; color:#7b8da0;}}
.tm.na .tm-top, .tm.na .tm-why {{color:#9AA8B6;}}
.tm.na .tm-bar {{background:repeating-linear-gradient(45deg, #EEF2F6, #EEF2F6 4px, #E3EBF3 4px, #E3EBF3 8px);}}
.penalty {{background:#FDECEA; color:#8A1F17; border-radius:8px; padding:6px 10px; font-size:.85rem; margin:4px 0;}}

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
.rr.rt .ra-main {{background:linear-gradient(transparent 50%, var(--hl) 50%);}}

/* ---------- messages */
.unread-badge {{display:inline-block; min-width:18px; padding:0 6px; border-radius:999px; background:var(--hl);
               color:var(--navy); font-size:.72rem; font-weight:800; text-align:center; line-height:18px;}}
a.msg-link {{font-weight:600;}}
.chat {{display:flex; flex-direction:column; gap:10px; margin:.4rem 0 .8rem;}}
.b {{max-width:88%; padding:10px 12px; border-radius:16px; line-height:1.45; font-size:.95rem; word-break:break-word;}}
.b.me {{align-self:flex-end; background:var(--navy); color:#fff; border-bottom-right-radius:4px;}}
.b.them {{align-self:flex-start; background:#fff; border:1px solid var(--line); border-bottom-left-radius:4px;}}
.b-en {{margin-top:7px; padding-top:7px; border-top:1px solid var(--line);}}
.b-sub {{font-size:.74rem; color:#5b6f84; margin-top:5px;}}
.b.me .b-sub {{color:#cfe0f0;}}
.mean {{margin-top:8px; background:#FFFBB8; color:#4D4600; border-radius:10px; padding:6px 9px; font-size:.85rem;}}
.terms {{margin-top:7px; display:flex; flex-wrap:wrap; gap:5px;}}
.term {{font-size:.72rem; font-weight:700; padding:1px 8px; border-radius:6px; background:#E3EEF8; color:#1F5A86;}}
.chat mark {{background:var(--hl); color:inherit; padding:0 2px; border-radius:3px;}}
.typing {{align-self:flex-start; color:#5b6f84; font-style:italic; font-size:.9rem; padding:4px 6px;}}
.chat-head {{margin-bottom:.3rem;}}
.chat-head .who {{font-size:1.2rem; font-weight:800; line-height:1.2; color:var(--navy);}}
.preview {{background:#fff; border:1px solid var(--line); border-radius:12px; padding:10px 12px;
           margin:.3rem 0 .5rem; font-size:.92rem;}}
.preview .bt {{color:#5b6f84; font-size:.82rem; margin-top:5px;}}
.deal-row {{display:flex; justify-content:space-between; gap:10px; padding:7px 0; font-size:.88rem;
            border-bottom:1px solid var(--line);}}
.deal-row .v {{text-align:right; font-weight:600;}}
.deal-row.new .v {{background:linear-gradient(transparent 50%, var(--hl) 50%);}}
.deal-row .src {{display:block; font-weight:400; font-size:.72rem; color:#8a99aa;}}
a.ib, a.oc {{display:block; padding:12px 14px; margin-bottom:8px; background:#fff; border:1px solid var(--line);
       border-radius:12px; color:var(--ink) !important; text-decoration:none !important;}}
.ib-top {{display:flex; justify-content:space-between; gap:8px; align-items:baseline;}}
.ib-name {{font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--navy);}}
a.ib.unread {{border-left:4px solid var(--hl);}}
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
.tl li.done::before {{background:var(--navy);}}
.tl li.now::before {{background:var(--hl); box-shadow:0 0 0 2px var(--navy);}}
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
  .pc-price {{font-size:1.7rem;}}
}}
</style>
"""

HOME_CSS = """
<style>
.block-container {max-width: 1190px;}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def inject_home():
    st.markdown(HOME_CSS, unsafe_allow_html=True)


def wide():
    st.markdown("<style>.block-container {max-width:1100px;}</style>", unsafe_allow_html=True)
