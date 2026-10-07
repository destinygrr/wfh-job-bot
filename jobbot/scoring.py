"""Job model + trust scoring (scam detection) + relevance matching."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


# --------------------------------------------------------------------------- #
# SCAM / LOW-QUALITY PATTERNS  (India-specific job-scam wording)
# --------------------------------------------------------------------------- #
SCAM_PATTERNS: List[tuple[str, str]] = [
    (r"\bregistration\s*(fee|charge|amount)\b", "asks for registration fee"),
    (r"\bsecurity\s*deposit\b", "asks for security deposit"),
    (r"\bpay\s*(rs\.?|inr|₹)?\s*\d+\s*(to|for)\s*(join|start|training|kit)", "pay to join"),
    (r"\b(refundable|re-?fundable)\s*(amount|deposit|fee)\b", "refundable fee trick"),
    (r"\binvest(ment)?\s*(required|mandatory)|\bcapital\s*required\b", "asks for investment"),
    (r"\bcommission\s*only\b|\bonly\s*commission\b|\b100%\s*commission\b", "commission-only pay"),
    (r"\bnetwork\s*marketing\b|\bmlm\b|\bchain\s*marketing\b|\bpyramid\b", "MLM / network marketing"),
    (r"\bdata\s*entry\s*(work)?\s*(with|at)\s*home\s*payment\b", "classic data-entry scam"),
    (r"\bwhats?app\s*(us|me|on)?\s*\+?\d{10,}", "hires only on WhatsApp"),
    (r"\bsend\s*(your)?\s*(aadhaar|pan|bank\s*details)\b", "asks ID/bank up-front"),
    (r"\bjoining\s*(fee|charges|kit)\b", "joining fee/kit"),
    (r"\btyping\s*job.{0,30}(deposit|fee|charges)\b", "typing-job fee scam"),
    (r"\bearn\s*(up\s*to\s*)?(rs\.?|₹)\s*\d{4,}\s*(daily|per\s*day)\b", "unrealistic daily earnings"),
    (r"\bno\s*(experience|interview)\s*(needed|required).{0,30}(earn|salary)\b", "too-good-to-be-true"),
    (r"\bpart[\s-]*time\s*earning\s*(app|opportunity)\b", "earning app scheme"),
    (r"\b(ltd|pvt)\s*co\.?\s*(is\s*)?hiring\s*(freshers)?.{0,20}home\b", "vague company hiring blurb"),
]

# Well-known, verifiable employers (a +10 boost). Not a guarantee - still verify,
# but these are registered companies with public HR/office presence.
TRUSTED_COMPANIES = [
    "accenture", "tcs", "tata consultancy", "infosys", "wipro", "tech mahindra", "hcl",
    "cognizant", "capgemini", "ibm", "oracle", "microsoft", "google", "amazon", "adobe",
    "deloitte", "ey", "kpmg", "pwc", "genpact", "wns", "sutherland", "concentrix",
    "teleperformance", "taskus", "foundever", "sitel", "firstsource", "startek",
    "telus", "appen", "chegg", "pearson", "planetspark", "vedantu", "unacademy",
    "cuemath", "byju", "flipkart", "myntra", "swiggy", "zomato", "paytm", "phonepe",
    "razorpay", "hdfc", "icici", "axis bank", "kotak", "bajaj", "sbi", "flipkart",
    "lionbridge", "sigma ai", "iMerit", "innodata", "objectways", "evalart",
    "physicswallah", "pw ", "toppr", "whitehat", "emeritus", "upgrad", "scaler",
    "salesforce", "sap", "siemens", "bosch", "qualcomm", "sandisk", "western digital",
    "lilly", "novartis", "glaxosmithkline", "sanofi", "accenture in india",
]

# Positive trust signals
GOOD_SIGNALS = [
    (r"\b(private limited|pvt\.?\s*ltd|limited|inc\.?|corporation|technologies|solutions|labs|systems)\b",
     "named registered company", 8),
    (r"\b(health|medical|life|term)\s*insurance\b|\bpf\b|\bprovident fund\b|\bgratuity\b",
     "offers PF / insurance / benefits", 8),
    (r"\b(fixed\s*salary|no\s*target|fixed\s*pay)\b", "fixed salary (no target pressure)", 6),
    (r"\b(5|five)\s*day(s)?\s*week\b|\bmon(day)?\s*(to|-)\s*fri(day)?\b", "5-day work week", 5),
    (r"\bwork\s*from\s*home\b|\bremote\b|\bwfh\b", "confirmed work-from-home", 10),
    (r"\b(experienced|min(imum)?\.?\s*\d+\s*(years|yrs))\b", "values experience (not fresher-only)", 6),
    (r"\b(after\s*training|paid\s*training)\b", "mentions training", 3),
    (r"\b(salary|ctc)\s*(range)?\s*[:\-]?\s*(₹|rs\.?|inr)?\s*\d",
     "salary stated in posting", 7),
]

BAD_LOW_SIGNALS = [
    (r"\b(freshers?\s*only|only\s*freshers?)\b", "freshers-only", -25),
    (r"\bintern(ship)?\b", "internship", -20),
    (r"\bstipend\b", "stipend (not salary)", -12),
    (r"\bunpaid\b", "unpaid", -35),
    (r"\b\d{2,}\s*(k|thousand)\s*(per|/)\s*month.{0,15}(target|incentive)\b",
     "heavy target-based pay", -12),
    (r"\bcommission\b(?!.*\bfixed\b)", "commission mentioned", -10),
    (r"\b(daily|weekly)\s*payout\b", "daily payout (scam-ish)", -15),
    (r"\b(immediate\s*joiners?\s*only|immediate\s*joining)\b", "urgent/immediate only", -3),
    (r"\btarget\s*based\b|\battractive\s*incentives?\b", "target/incentive heavy", -8),
]

WORK_MODE_OFFICE = re.compile(r"\b(work\s*from\s*office|wfo|on[\s-]*site|in[\s-]*office|walk[\s-]*in)\b", re.I)
WORK_MODE_HOME = re.compile(r"\b(work\s*from\s*home|wfh|remote|work\s*at\s*home|anywhere)\b", re.I)

SALARY_RE = re.compile(
    r"(?:₹|rs\.?\s*|inr\s*)?((?:\d{1,3}(?:,\d{2,3})+)|(?:\d+(?:\.\d+)?))\s*"
    r"(lpa|lakhs?|lac|k\b|thousand|per\s*month|/month|pm\b)?",
    re.I,
)


def parse_salary_lpa(text: str) -> float | None:
    """Best-effort salary extraction -> lakhs per annum."""
    if not text:
        return None
    t = str(text)
    best = None
    for m in SALARY_RE.finditer(t):
        num = float(m.group(1).replace(",", ""))
        unit = (m.group(2) or "").lower().strip()
        if unit.startswith("lpa") or unit.startswith("lakh") or unit.startswith("lac"):
            val = num
        elif unit in ("k", "thousand"):
            val = num * 1000 * 12 / 100_000
        elif "month" in unit or unit == "pm":
            val = num * 12 / 100_000
        elif num >= 100_000:          # raw annual figure
            val = num / 100_000
        elif num >= 8_000:            # monthly figure
            val = num * 12 / 100_000
        else:
            continue
        if 0.2 <= val <= 100:
            best = val if best is None else max(best, val)
    return round(best, 2) if best else None


# --------------------------------------------------------------------------- #
# RELEVANCE: does this job actually match one of your target roles?
# Strict on purpose - a job alert is only useful if it is the right kind of job.
# --------------------------------------------------------------------------- #
_ACRONYMS = {"ai", "qa", "ml", "it", "ux", "hr", "cs", "seo"}


def _words(text: str) -> set:
    return set(re.split(r"[^a-z0-9+#]+", (text or "").lower()))


def keyword_hit(keyword: str, title_blob: str, full_blob: str) -> bool:
    kw = (keyword or "").lower().strip()
    if not kw:
        return False
    if kw in title_blob:                       # exact phrase in title/tags/company
        return True
    toks = [t for t in re.split(r"[^a-z0-9+#]+", kw)
            if len(t) >= 3 or t in _ACRONYMS]
    if toks and all(t in _words(title_blob) for t in toks):
        return True
    return kw in full_blob                     # phrase somewhere in the description


def match_profile(s, job) -> str | None:
    """Return the profile name this job belongs to, or None if not relevant."""
    title_blob = " ".join([job.title, job.tags, job.company]).lower()
    full_blob = " ".join([title_blob, job.snippet, job.salary, job.location]).lower()
    for p in s.profiles:
        for kw in p.keywords:
            if keyword_hit(kw, title_blob, full_blob):
                return p.name
    return None


@dataclass
class Job:
    source: str
    job_id: str
    title: str
    company: str = ""
    location: str = ""
    url: str = ""
    posted: str = ""
    salary: str = ""
    tags: str = ""
    snippet: str = ""
    is_remote_hint: bool = False        # source itself is a WFH/remote source
    relevant: bool = True               # matches one of your target roles
    profile: str = ""
    trust: int = 60
    trust_reasons: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.job_id}"

    @property
    def blob(self) -> str:
        return " ".join([self.title, self.company, self.location, self.tags, self.snippet, self.salary])

    # ------------------------------------------------------------------ #
    def evaluate(self, s, profile_name: str = "") -> "Job":
        """Fill profile / trust / red flags and return self."""
        blob = self.blob
        low = blob.lower()

        matched_role = match_profile(s, self)
        self.relevant = matched_role is not None
        self.profile = profile_name or matched_role or s.keyword_to_profile(blob)
        score, reasons, flags = 70, [], []
        if matched_role:
            score += 5
            reasons.append(f"matches target role ({matched_role})")

        # WFH check
        wfh = self.is_remote_hint or bool(WORK_MODE_HOME.search(blob)) or s.remote_only is False
        if WORK_MODE_OFFICE.search(blob) and not WORK_MODE_HOME.search(blob):
            wfh = False
        if wfh:
            score += 8
        else:
            score -= 25
            flags.append("not clearly work-from-home")

        for pat, why in SCAM_PATTERNS:
            if re.search(pat, low, re.I):
                penalty = -18 if "fee" in why or "deposit" in why else -12
                score += penalty
                flags.append(why)

        comp_low = (self.company or "").lower()
        if any(c in comp_low for c in TRUSTED_COMPANIES):
            score += 10
            reasons.append("well-known registered company")

        for pat, why, pts in GOOD_SIGNALS:
            if re.search(pat, blob, re.I):
                score += pts
                reasons.append(why)

        for pat, why, pts in BAD_LOW_SIGNALS:
            if re.search(pat, low, re.I):
                score += pts
                reasons.append(f"{why} ({pts})")

        if s.filters.get("exclude_fresher_only", True) and re.search(r"freshers?\s*only", low):
            flags.append("Freshers-only (you have experience)")
        if s.filters.get("exclude_internships", True) and re.search(r"\bintern(ship)?\b", low):
            flags.append("Internship")

        lpa = parse_salary_lpa(self.salary or blob)
        if lpa:
            self.salary = self.salary or f"~₹{lpa:g} LPA"
            if lpa >= 4:
                score += 6
                reasons.append(f"salary ≈₹{lpa:g} LPA")
            if lpa < 1.5:
                score -= 8
                reasons.append("very low pay")

        self.trust = max(0, min(100, score))
        self.trust_reasons, self.red_flags = reasons, flags
        return self

    def sort_key(self):
        return (-self.trust, self.source)
