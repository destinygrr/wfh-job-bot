"""Job sources: LinkedIn, Apna, Naukri (+Jooble fallback), Remotive, Jobicy.

Every fetcher returns a list of Job objects and never raises: on failure it
returns ([], "error message") so one blocked site can't stop the whole run.
"""
from __future__ import annotations

import html
import json
import re
import time
from typing import List, Tuple
from urllib.parse import quote_plus, urlencode

import requests

from .scoring import Job

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
}

TIMEOUT = 25


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


# =========================================================================== #
# 1. LINKEDIN  - public "guest" job search API (no login, no key)
# =========================================================================== #
def fetch_linkedin(s, max_jobs: int = 200, pages: int = 2) -> Tuple[List[Job], str]:
    jobs: List[Job] = []
    sess = _session()
    # round-robin the keywords so all four job types are searched equally
    kws = s.spread_keywords(32)
    if len(kws) > 20:
        pages = 1                      # many keywords -> one page each, stays polite
    base = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    try:
        for kw in kws:
            for page in range(pages):
                params = {
                    "keywords": kw,
                    "location": s.location,
                    "start": page * 10,
                }
                if s.remote_only:
                    params["f_WT"] = "2"          # 2 = Remote
                url = f"{base}?{urlencode(params)}"
                r = sess.get(url, timeout=TIMEOUT)
                if r.status_code != 200 or "No matching" in r.text:
                    break
                jobs.extend(_parse_linkedin(r.text, remote_hint=s.remote_only))
                if len(jobs) >= max_jobs:
                    return jobs[:max_jobs], f"{len(jobs)} jobs"
                time.sleep(0.6)
        return jobs[:max_jobs], f"{len(jobs)} jobs"
    except Exception as exc:                      # noqa: BLE001
        return jobs, f"error: {type(exc).__name__}"


def _parse_linkedin(page: str, remote_hint: bool = False) -> List[Job]:
    out: List[Job] = []
    blocks = re.split(r'data-entity-urn="urn:li:jobPosting:', page)[1:]
    for b in blocks:
        m = re.match(r"(\d+)", b)
        if not m:
            continue
        jid = m.group(1)

        def grab(pattern: str) -> str:
            mm = re.search(pattern, b, re.S)
            return _clean(mm.group(1)) if mm else ""

        title = grab(r'class="base-search-card__title">\s*(.*?)\s*</h3>')
        company = grab(r'class="hidden-nested-link"[^>]*>\s*(.*?)\s*</a>')
        if not company:
            company = grab(r'class="base-search-card__subtitle">\s*(.*?)\s*</h4>')
        loc = grab(r'job-search-card__location">\s*(.*?)\s*</span>')
        posted = grab(r'datetime="([\d-]+)"')
        link = grab(r'href="(https://[a-z]{0,3}\.?linkedin\.com/jobs/view/[^"?]+)')
        if not link:
            link = f"https://www.linkedin.com/jobs/view/{jid}"
        label = grab(r'class="job-posting-benefits__text">\s*(.*?)\s*</span>')
        out.append(Job(
            source="LinkedIn", job_id=jid, title=title, company=company,
            location=loc, url=link.split("?")[0], posted=posted,
            tags=label, is_remote_hint=remote_hint,
        ))
    return [j for j in out if j.title]


# =========================================================================== #
# 2. APNA  - job data is embedded in the public page (no login)
# =========================================================================== #
def fetch_apna(s, max_jobs: int = 240) -> Tuple[List[Job], str]:
    jobs: List[Job] = []
    sess = _session()
    slugs = list(dict.fromkeys(s.all_apna_categories or ["work-from-home-jobs"]))
    try:
        for slug in slugs:
            url = f"https://apna.co/jobs/{slug}"
            r = sess.get(url, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code != 200:
                continue
            jobs.extend(_parse_apna(r.text, slug))
            if len(jobs) >= max_jobs:
                break
            time.sleep(0.5)
        return jobs[:max_jobs], f"{len(jobs)} jobs"
    except Exception as exc:                      # noqa: BLE001
        return jobs, f"error: {type(exc).__name__}"


def _parse_apna(page: str, slug: str) -> List[Job]:
    t = page.replace('\\\\"', '"').replace('\\"', '"')
    t = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), t)
    out: List[Job] = []
    pat = re.compile(
        r'"jobID":(\d+),"jobTitle":"(.*?)","jobOrganisationDetails":\{[^{}]*?'
        r'"organisationName":"(.*?)"\},"jobPublicURL":"(.*?)"', re.S)
    for m in pat.finditer(t):
        jid, title, company, path = m.group(1), _clean(m.group(2)), _clean(m.group(3)), m.group(4)
        # look ahead a little for salary / address / tags
        window = t[m.end(): m.end() + 900]
        salary = ""
        sal = re.search(r'"salaryMax":(\d+),"salaryMin":(\d+)', window) or \
              re.search(r'"salaryMin":(\d+),"salaryMax":(\d+)', window)
        if sal:
            a, b = int(sal.group(1)), int(sal.group(2))
            lo, hi = min(a, b), max(a, b)
            if lo:
                salary = f"₹{lo//1000}k-{hi//1000}k/yr" if hi else f"₹{lo//1000}k/yr"
        addr = re.search(r'"jobCardAddress":"(.*?)"', window)
        tags = " | ".join(list(dict.fromkeys(re.findall(r'"tagLabel":"(.*?)"', window)))[:6])
        out.append(Job(
            source="Apna", job_id=jid, title=title, company=company,
            location=_clean(addr.group(1)) if addr else slug.replace("-", " "),
            url=f"https://apna.co{path}", salary=salary, tags=tags,
            is_remote_hint="work-from-home" in slug or "work from home" in tags.lower(),
        ))
    return [j for j in out if j.title]


# =========================================================================== #
# 3. NAUKRI  - try its search API; on block, fall back to Jooble (needs key)
# =========================================================================== #
def fetch_naukri(s, max_jobs: int = 60) -> Tuple[List[Job], str]:
    jobs: List[Job] = []
    sess = _session()
    sess.headers.update({
        "appid": "109", "systemid": "Naukri", "gid": "LOCATION,IN",
        "Accept": "application/json", "Referer": "https://www.naukri.com/",
    })
    try:
        for kw in s.spread_keywords(8):
            params = {
                "noOfResults": 20, "urlType": "search_by_keyword", "searchType": "adv",
                "keyword": kw, "k": kw, "src": "directSearch",
                "seoKey": kw.lower().replace(" ", "-") + "-jobs",
            }
            url = "https://www.naukri.com/jobapi/v3/search?" + urlencode(params)
            r = sess.get(url, timeout=TIMEOUT)
            if r.status_code == 406 or "recaptcha" in r.text.lower():
                return jobs, ("blocked by Naukri (captcha) - this is normal from cloud/office "
                              "IPs; it works when run from your home Wi-Fi")
            data = r.json()
            for item in data.get("jobDetails", []):
                jid = str(item.get("jobId", ""))
                jd_url = item.get("jdURL", "") or f"/job-listings-{item.get('title','')}-{jid}"
                loc = ", ".join(
                    p.get("label", "") for p in (item.get("placeholders") or [])
                    if p.get("type") == "location") or s.location
                tags = " ".join(item.get("tagsAndSkills", "").split(",")[:6])
                jobs.append(Job(
                    source="Naukri", job_id=jid, title=_clean(item.get("title")),
                    company=_clean(item.get("companyName")), location=loc,
                    url="https://www.naukri.com" + jd_url if jd_url.startswith("/") else jd_url,
                    posted=_clean(item.get("footerPlaceholderLabel") or item.get("createdDate")),
                    salary=_clean(item.get("salary") or ""), tags=tags,
                    snippet=_clean(item.get("jobDescription")),
                ))
            if len(jobs) >= max_jobs:
                break
            time.sleep(1.0)
        return jobs[:max_jobs], f"{len(jobs)} jobs"
    except Exception as exc:                      # noqa: BLE001
        return jobs, f"error: {type(exc).__name__}"


def fetch_jooble(s, max_jobs: int = 60) -> Tuple[List[Job], str]:
    """Jooble = Naukri-like Indian coverage (Monster/TimesJobs feed). Needs a FREE key."""
    if not s.jooble_key:
        return [], "skipped (no JOOBLE_API_KEY set)"
    jobs: List[Job] = []
    try:
        for kw in s.spread_keywords(8):
            r = requests.post(
                f"https://jooble.org/api/{s.jooble_key}",
                json={"keywords": kw, "location": s.location, "page": "1"},
                headers={"Content-Type": "application/json"}, timeout=TIMEOUT)
            for item in (r.json().get("jobs") or [])[:20]:
                jid = str(abs(hash(item.get("link", item.get("title", "")))))
                jobs.append(Job(
                    source="Jooble", job_id=jid, title=_clean(item.get("title")),
                    company=_clean(item.get("company")), location=_clean(item.get("location")),
                    url=item.get("link", ""), posted=_clean(item.get("updated")),
                    salary=_clean(item.get("salary")), snippet=_clean(item.get("snippet")),
                ))
            if len(jobs) >= max_jobs:
                break
            time.sleep(0.5)
        return jobs[:max_jobs], f"{len(jobs)} jobs"
    except Exception as exc:                      # noqa: BLE001
        return jobs, f"error: {type(exc).__name__}"


# =========================================================================== #
# 4. BONUS free APIs (no key, no signup) - extra remote roles incl. AI training
# =========================================================================== #
def fetch_remotive(s, max_jobs: int = 40) -> Tuple[List[Job], str]:
    jobs: List[Job] = []
    try:
        for kw in s.spread_keywords(8):
            r = requests.get("https://remotive.com/api/remote-jobs",
                             params={"search": kw, "limit": 20}, timeout=TIMEOUT)
            for item in r.json().get("jobs", []):
                loc = _clean(item.get("candidate_required_location"))
                if "india" not in loc.lower() and "worldwide" not in loc.lower() \
                        and "anywhere" not in loc.lower():
                    continue
                jobs.append(Job(
                    source="Remotive", job_id=str(item.get("id")), title=_clean(item.get("title")),
                    company=_clean(item.get("company_name")), location=loc or "Worldwide",
                    url=item.get("url", ""), posted=_clean(item.get("publication_date"))[:10],
                    salary=_clean(item.get("salary")), tags=_clean(item.get("job_type")),
                    snippet=_clean(item.get("description"))[:600], is_remote_hint=True,
                ))
            if len(jobs) >= max_jobs:
                break
            time.sleep(0.4)
        return jobs[:max_jobs], f"{len(jobs)} jobs"
    except Exception as exc:                      # noqa: BLE001
        return jobs, f"error: {type(exc).__name__}"


def fetch_jobicy(s, max_jobs: int = 40) -> Tuple[List[Job], str]:
    jobs: List[Job] = []
    try:
        seen = set()
        for kw in s.spread_keywords(8):
            r = requests.get("https://jobicy.com/api/v2/remote-jobs",
                             params={"count": 20, "tag": (kw.split() or ["remote"])[0]}, timeout=TIMEOUT)
            for item in r.json().get("jobs", []):
                jid = str(item.get("id"))
                if jid in seen:
                    continue
                geo = _clean(item.get("jobGeo"))
                if geo and not any(g in geo.lower() for g in ("anywhere", "india", "apac", "asia")):
                    continue
                seen.add(jid)
                jobs.append(Job(
                    source="Jobicy", job_id=jid, title=_clean(item.get("jobTitle")),
                    company=_clean(item.get("companyName")), location=geo or "Anywhere",
                    url=item.get("url", ""), posted=_clean(item.get("pubDate"))[:10],
                    salary=_clean(
                        f"{item.get('salaryMin') or ''}-{item.get('salaryMax') or ''} "
                        f"{item.get('salaryCurrency') or ''} {item.get('salaryPeriod') or ''}".strip("- ")),
                    tags=_clean(" ".join(item.get("jobType") or [])),
                    snippet=_clean(item.get("jobExcerpt"))[:400],
                    is_remote_hint=True,
                ))
            if len(jobs) >= max_jobs:
                break
            time.sleep(0.4)
        return jobs[:max_jobs], f"{len(jobs)} jobs"
    except Exception as exc:                      # noqa: BLE001
        return jobs, f"error: {type(exc).__name__}"


FETCHERS = {
    "linkedin": fetch_linkedin,
    "apna": fetch_apna,
    "naukri": fetch_naukri,
    "jooble": fetch_jooble,
    "remotive": fetch_remotive,
    "jobicy": fetch_jobicy,
}
