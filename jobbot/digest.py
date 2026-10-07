"""Builds a beautiful offline HTML + Markdown digest you can open any time."""
from __future__ import annotations

import html as _html
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def _badge(score: int) -> str:
    if score >= 80:
        return "#0f9d58", "High trust"
    if score >= 65:
        return "#1a73e8", "Looks fine"
    if score >= 55:
        return "#f4b400", "Check carefully"
    return "#db4437", "Risky"


def build_markdown(new_jobs: List, all_run_jobs: List, report: Dict, min_trust: int = 0) -> str:
    ts = datetime.now(timezone.utc).astimezone().strftime("%d %b %Y, %I:%M %p")
    lines = [f"# WFH Job Bot — digest {ts}", ""]
    lines.append(f"**{len(new_jobs)} new job(s)** matching AI-Testing / Teaching from {len(all_run_jobs)} fetched.")
    lines.append("")
    if new_jobs:
        lines.append("| # | Trust | Role | Company | Location | Pay | Source | Apply |")
        lines.append("|---|-------|------|---------|----------|-----|--------|-------|")
        for i, j in enumerate(new_jobs, 1):
            mark = " (below your alert threshold)" if j.trust < min_trust else ""
            lines.append(
                f"| {i} | {j.trust}/100{mark} | {j.title} | {j.company or '-'} | "
                f"{j.location or '-'} | {j.salary or '-'} | {j.source} | [Apply]({j.url}) |")
    lines.append("")
    lines.append("## Source status")
    for k, v in report.get("sources", {}).items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Safety checklist before you apply")
    for tip in SAFETY_TIPS:
        lines.append(f"- {tip}")
    return "\n".join(lines)


SAFETY_TIPS = [
    "A genuine employer NEVER asks for a registration fee, security deposit, training fee or 'kit' money. Any request = scam, stop immediately.",
    "Legitimate interviews happen over a company email ID / official video call — not only on personal WhatsApp.",
    "Google the company name + 'review' and check it on the MCA portal (mca.gov.in) for a real CIN/registration.",
    "Ask for the offer letter on company letterhead with HR name, employee ID process and PF/ESI details.",
    "Never share Aadhaar/PAN/bank OTP/cancelled cheque before a signed offer letter and a verified HR contact.",
    "For WFH: ask exactly how you will be paid (fixed salary vs commission), the payout date, and whether equipment is provided.",
    "Trust your instinct: 'too easy to get, too much money' = scam. Report fraud at cybercrime.gov.in or 1930.",
]


def build_html(new_jobs: List, all_run_jobs: List, report: Dict, min_trust: int = 0) -> str:
    ts = datetime.now(timezone.utc).astimezone().strftime("%d %b %Y, %I:%M %p")
    rows = []
    for i, j in enumerate(new_jobs, 1):
        color, label = _badge(j.trust)
        flags = "".join(f"<span class='flag'>⚠ {_html.escape(f)}</span>" for f in j.red_flags[:3])
        reasons = ", ".join(j.trust_reasons[:4])
        lowflag = ("<span class='flag low'>below your alert threshold</span>"
                   if j.trust < min_trust else "")
        rows.append(f"""
        <tr>
          <td class='num'>{i}</td>
          <td>
            <div class='role'>{_html.escape(j.title)}</div>
            <div class='co'>{_html.escape(j.company or '—')} · {_html.escape(j.location or '—')}</div>
            <div class='meta'>{_html.escape(j.source)} · posted {_html.escape(j.posted or '—')} · {_html.escape(j.salary or 'pay not stated')}</div>
            {f"<div class='why'>Good signs: {_html.escape(reasons)}</div>" if reasons else ""}
            {flags}{lowflag}
          </td>
          <td class='trust'>
            <span class='score' style='background:{color}'>{j.trust}</span>
            <div class='lbl' style='color:{color}'>{label}</div>
          </td>
          <td><a class='apply' href="{_html.escape(j.url)}" target="_blank" rel="noopener">Apply ↗</a></td>
        </tr>""")

    src_rows = "".join(
        f"<li><b>{_html.escape(k)}</b>: {_html.escape(str(v))}</li>" for k, v in report.get("sources", {}).items())
    tips = "".join(f"<li>{_html.escape(t)}</li>" for t in SAFETY_TIPS)
    notify = "".join(f"<li><b>{_html.escape(k)}</b>: {_html.escape(str(v))}</li>"
                     for k, v in (report.get("notify") or {}).items())

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WFH Job Bot digest</title>
<style>
 :root{{--ink:#0f172a;--mut:#5b6b7f;--line:#e3e8ef;--bg:#f6f8fb}}
 *{{box-sizing:border-box}}
 body{{margin:0;font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg)}}
 .wrap{{max-width:980px;margin:0 auto;padding:24px 16px 64px}}
 header{{background:linear-gradient(135deg,#0b3d91,#1273d4);color:#fff;border-radius:16px;padding:22px 24px}}
 header h1{{margin:0 0 6px;font-size:22px}}
 header p{{margin:0;opacity:.9;font-size:14px}}
 .cards{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}}
 .card{{flex:1 1 150px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px}}
 .card b{{display:block;font-size:24px}}
 .card span{{color:var(--mut);font-size:13px}}
 table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}}
 td{{border-bottom:1px solid var(--line);padding:14px;vertical-align:top}}
 tr:last-child td{{border-bottom:none}}
 .num{{color:var(--mut);width:28px}}
 .role{{font-weight:650;font-size:16px}}
 .co{{color:#22364f;font-size:14px;margin-top:2px}}
 .meta{{color:var(--mut);font-size:12.5px;margin-top:3px}}
 .why{{color:#0f7a4a;font-size:12.5px;margin-top:6px}}
 .flag{{display:inline-block;background:#fff4e5;color:#8a4b00;border:1px solid #ffd9a8;border-radius:999px;padding:1px 9px;font-size:12px;margin:6px 6px 0 0}}
 .flag.low{{background:#eef2f7;color:#54637a;border-color:#dbe3ec}}
 .trust{{text-align:center;width:104px}}
 .score{{display:inline-block;color:#fff;font-weight:700;border-radius:999px;padding:4px 12px}}
 .lbl{{font-size:11.5px;margin-top:4px}}
 .apply{{display:inline-block;background:#0b57d0;color:#fff;text-decoration:none;padding:9px 14px;border-radius:10px;font-weight:600;white-space:nowrap}}
 h2{{font-size:17px;margin:28px 0 10px}}
 .panel{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 20px}}
 ul{{margin:8px 0 0;padding-left:20px}} li{{margin:6px 0}}
 .empty{{background:#fff;border:1px dashed var(--line);border-radius:12px;padding:28px;text-align:center;color:var(--mut)}}
 footer{{color:var(--mut);font-size:12.5px;margin-top:26px;text-align:center}}
</style></head><body><div class="wrap">
<header>
  <h1>🏠 WFH Job Bot — {ts}</h1>
  <p>Hunting: AI Testing / QA · Document Verification (KYC) · Stock Market &amp; Equity Research · Online Teaching / Tutoring — work from home, pan-India</p>
</header>
<div class="cards">
  <div class="card"><b>{len(new_jobs)}</b><span>new jobs alerted</span></div>
  <div class="card"><b>{len(all_run_jobs)}</b><span>jobs scanned this run</span></div>
  <div class="card"><b>{report.get('total_seen', 0)}</b><span>jobs remembered (no repeats)</span></div>
  <div class="card"><b>{report.get('onsite_dropped', 0)}</b><span>on-site jobs dropped</span></div>
  <div class="card"><b>{report.get('elapsed', 0):.0f}s</b><span>run time</span></div>
</div>
{'<table>' + ''.join(rows) + '</table>' if rows else '<div class="empty">No new matching jobs this run. The bot keeps checking — you will be pinged the moment something appears.</div>'}
<h2>Source status</h2><div class="panel"><ul>{src_rows}</ul></div>
<h2>Alert delivery</h2><div class="panel"><ul>{notify or '<li>No alert sent this run (nothing new).</li>'}</ul></div>
<h2>Safety checklist — read before you apply</h2><div class="panel"><ul>{tips}</ul></div>
<footer>Generated by your own WFH Job Bot · runs free · never pays for job alerts</footer>
</div></body></html>"""


def write_files(s, html: str, md: str) -> None:
    for rel, content in ((s.digest_html, html), (s.digest_md, md)):
        p = Path(s.path(rel))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
