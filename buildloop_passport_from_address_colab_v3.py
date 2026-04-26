#!/usr/bin/env python3
"""
BuildLoop address-only passport pipeline (Colab version, resolver v3)

What this version improves
--------------------------
- Accepts multiple test addresses in one run
- Uses Estonia-friendly query variants for In-ADS
- Groups resolver hits by EHR code instead of treating each hit independently
- Handles corner buildings / multiple official addresses for one building
- Boosts confidence when multiple query variants resolve to the same EHR code
- Preserves address aliases in the passport output
- Writes per-address artifacts and a batch summary

How to use in Colab
-------------------
1. Edit TEST_ADDRESSES below.
2. Run:
       !python buildloop_passport_from_address_colab_v3.py

Artifacts
---------
For each address:
- address_resolution.json
- resolver_attempts.json
- resolver_inads_raw_*.json
- source_fetch.json
- source_document.pdf
- source_document.txt
- passport_mvp.json
- observations.json
- source_manifest.json
- pipeline_result.json
- run_summary.md

Batch-level:
- batch_summary.json
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import urllib3


# =========================
# EDIT THIS IN COLAB
# =========================
TEST_ADDRESSES = [
    "Lai 1, Nunne tn 4, 10133 Tallinn, Estonia",
    # add more Tallinn test addresses here
]

# The fetcher tries verified TLS first and falls back if needed.
TEST_SSL_VERIFY = True

OUTPUT_ROOT = Path(os.environ.get("OUTPUT_ROOT", "./artifacts")).resolve()
EHR_BASE_URL = os.environ.get("EHR_BASE_URL", "https://livekluster.ehr.ee/api/document/v1").rstrip("/")
INADS_BASE_URL = os.environ.get("INADS_BASE_URL", "https://inaadress.maaamet.ee/inaadress").rstrip("/")
INADS_FEATURES = os.environ.get("INADS_FEATURES", "EHAK,VAIKEKOHT,TANAV,KATASTRIYKSUS,EHITISHOONE")
CHECKLIST_JSON_ENV = os.environ.get("CHECKLIST_JSON", "").strip()

AUTO_RESOLVE_THRESHOLD = float(os.environ.get("AUTO_RESOLVE_THRESHOLD", "0.85"))
AMBIGUOUS_THRESHOLD = float(os.environ.get("AMBIGUOUS_THRESHOLD", "0.50"))

DEFAULT_CHECKLIST = {
    "identity": ["ehr_code", "normalized_address", "country"],
    "building_profile": [
        "building_type", "building_status", "use_categories", "floors",
        "footprint_area_m2", "net_area_m2", "height_m", "volume_m3"
    ],
    "structural_systems": [
        "foundation_type", "load_bearing_material", "wall_type",
        "roof_structure_material", "roof_covering_material"
    ],
    "technical_systems": [
        "electricity", "water", "sewer", "heat_source", "ventilation", "gas"
    ],
    "building_parts": ["part_identifier", "part_type", "part_use", "part_area_m2"],
    "quality": ["schema_completeness_score", "confidence_score", "provenance_by_section"],
}

MUNICIPALITY_TO_COUNTY = {
    "tallinn": "Harju maakond",
    "tartu": "Tartu maakond",
    "pärnu": "Pärnu maakond",
    "parnu": "Pärnu maakond",
    "narva": "Ida-Viru maakond",
    "kohtla järve": "Ida-Viru maakond",
    "kohtla jarve": "Ida-Viru maakond",
}


@dataclass
class Observation:
    field_path: str
    value: Any
    section: str
    source_type: str
    source_name: str
    page: Optional[int]
    confidence: str
    evidence_text: str


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def json_dump(obj: Any, path: Path) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_multiline_value(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s*\n\s*", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip() or None


def parse_decimal(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    v = value.replace("\u00a0", " ").replace(" ", "").replace(",", ".")
    try:
        return float(v)
    except Exception:
        return None


def load_checklist() -> Dict[str, List[str]]:
    if CHECKLIST_JSON_ENV:
        p = Path(CHECKLIST_JSON_ENV)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    local = Path("relevance_checklist.json")
    if local.exists():
        return json.loads(local.read_text(encoding="utf-8"))
    return DEFAULT_CHECKLIST


def make_session(ssl_verify: bool) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "BuildLoop-Passport-From-Address-Colab/3.0",
        "Accept": "*/*",
    })
    s.verify = ssl_verify
    if not ssl_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return s


def ensure_package(module_name: str, pip_name: Optional[str] = None) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        pass
    pip_target = pip_name or module_name
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", pip_target],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        importlib.invalidate_caches()
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


# ----------------------------
# Address normalization / variants
# ----------------------------

def normalize_address_for_match(address: str) -> str:
    address = address.lower()
    address = (
        address.replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("õ", "o")
    )
    address = re.sub(r"[^a-z0-9]+", " ", address)
    return re.sub(r"\s+", " ", address).strip()


def titleish(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str, max_len: int = 60) -> str:
    s = normalize_address_for_match(text).replace(" ", "_")
    return s[:max_len] or "item"


def split_address_aliases(normalized_address: Optional[str]) -> List[str]:
    if not normalized_address:
        return []
    # Corner buildings often use // as official separator.
    parts = [p.strip() for p in re.split(r"\s*//\s*", normalized_address) if p.strip()]
    if parts:
        return parts
    return [normalized_address.strip()]


def parse_address_components(raw_address: str) -> Dict[str, Any]:
    original = raw_address.strip()
    parts = [p.strip() for p in original.split(",") if p.strip()]

    country = None
    if parts and parts[-1].lower() in {"estonia", "eesti"}:
        country = parts.pop(-1)

    postcode = None
    municipality = None

    remaining: List[str] = []
    for part in parts:
        m = re.match(r"^(\d{5})\s+(.+)$", part)
        if m and postcode is None:
            postcode = m.group(1)
            municipality = m.group(2).strip()
        else:
            remaining.append(part)
    parts = remaining

    if municipality is None and parts:
        maybe_city = parts[-1]
        if not re.search(r"\d", maybe_city):
            municipality = maybe_city
            parts = parts[:-1]

    street_fragments = []
    for part in parts:
        if re.search(r"\d", part):
            street_fragments.append(part.strip())

    county = None
    if municipality:
        county = MUNICIPALITY_TO_COUNTY.get(municipality.lower())

    return {
        "raw_input": original,
        "country": country or "Estonia",
        "postcode": postcode,
        "municipality": municipality,
        "county": county,
        "street_fragments": street_fragments,
    }


def build_query_variants(components: Dict[str, Any]) -> List[str]:
    variants: List[str] = []

    municipality = components.get("municipality")
    county = components.get("county")
    postcode = components.get("postcode")
    street_fragments = components.get("street_fragments") or []

    for frag in street_fragments:
        frag = titleish(frag)
        variants.append(frag)
        if municipality:
            variants.append(f"{frag} {municipality}")
            variants.append(f"{frag}, {municipality}")
        if postcode and municipality:
            variants.append(f"{frag} {postcode} {municipality}")
            variants.append(f"{frag}, {postcode} {municipality}")
        if county:
            variants.append(f"{frag} {county}")
            if municipality:
                variants.append(f"{frag} {municipality} {county}")

    raw = components["raw_input"]
    raw_no_country = re.sub(r",?\s*(Estonia|Eesti)\s*$", "", raw, flags=re.I).strip()
    variants.append(raw_no_country)

    if municipality and postcode:
        variants.append(f"{postcode} {municipality}")
    if municipality:
        variants.append(municipality)

    seen = set()
    out = []
    for v in variants:
        v = re.sub(r"\s+", " ", v).strip(" ,")
        if not v:
            continue
        key = v.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


# ----------------------------
# Address resolution
# ----------------------------

def collect_candidate_objects(node: Any, bag: List[Dict[str, Any]]) -> None:
    if isinstance(node, dict):
        lower_keys = {str(k).lower() for k in node.keys()}
        addressish = any(k in lower_keys for k in {
            "taisaadress", "pikkaadress", "aadress", "address", "lahiaadress", "ads_lahiaadress"
        })
        ehrish = any(k in lower_keys for k in {"ehr", "ehr_kood", "ehrcode", "ehr_code"})
        if addressish or ehrish:
            bag.append(node)
        for v in node.values():
            collect_candidate_objects(v, bag)
    elif isinstance(node, list):
        for item in node:
            collect_candidate_objects(item, bag)


def extract_all_ehr_codes(node: Any, bag: List[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            lk = str(k).lower()
            if lk in {"ehr_kood", "ehrcode", "ehr_code"} and isinstance(v, (str, int)):
                bag.append(str(v))
            else:
                extract_all_ehr_codes(v, bag)
    elif isinstance(node, list):
        for item in node:
            extract_all_ehr_codes(item, bag)


def extract_candidate_address(candidate_obj: Dict[str, Any]) -> Optional[str]:
    possible_keys = [
        "taisaadress", "pikkaadress", "aadress", "address", "lahiaadress",
        "nimi", "nimetus", "ads_lahiaadress"
    ]
    for key in possible_keys:
        value = candidate_obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for v in candidate_obj.values():
        if isinstance(v, dict):
            for key in possible_keys:
                value = v.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return None


def extract_object_type(candidate_obj: Dict[str, Any]) -> Optional[str]:
    for key in ("liikVal", "liik", "type", "objektiliik", "features"):
        value = candidate_obj.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return ",".join(str(x) for x in value)
    return None


def is_primary_candidate(candidate_obj: Dict[str, Any]) -> bool:
    for key in ("primary", "esmane"):
        value = candidate_obj.get(key)
        if value is True:
            return True
        if isinstance(value, str) and value.lower() in {"true", "1", "yes"}:
            return True
    return False


def score_candidate(address_input: str, query_variant: str, candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
    reasons: List[str] = []
    score = 0.0

    normalized_input = normalize_address_for_match(address_input)
    normalized_query = normalize_address_for_match(query_variant)
    normalized_candidate = normalize_address_for_match(candidate.get("normalized_address") or "")

    # overlap against original raw input
    input_tokens = set(normalized_input.split())
    cand_tokens = set(normalized_candidate.split())
    overlap = input_tokens & cand_tokens
    if overlap:
        overlap_ratio = len(overlap) / max(1, len(input_tokens))
        score += 0.35 * overlap_ratio
        reasons.append(f"input_token_overlap={overlap_ratio:.2f}")

    # overlap against specific query variant
    query_tokens = set(normalized_query.split())
    overlap_q = query_tokens & cand_tokens
    if overlap_q:
        overlap_ratio_q = len(overlap_q) / max(1, len(query_tokens))
        score += 0.20 * overlap_ratio_q
        reasons.append(f"query_token_overlap={overlap_ratio_q:.2f}")

    # house number
    input_nums = re.findall(r"\d+[a-z]?", normalized_input)
    cand_nums = re.findall(r"\d+[a-z]?", normalized_candidate)
    if input_nums and cand_nums and any(n in cand_nums for n in input_nums):
        score += 0.20
        reasons.append("house_number_match")

    # locality hints
    for token in ("tallinn", "kesklinn", "kesklinna", "harju", "maakond"):
        if token in normalized_input and token in normalized_candidate:
            score += 0.02
            reasons.append(f"locality_match:{token}")

    # building object type boost
    obj_type = normalize_address_for_match(candidate.get("object_type") or "")
    if "ehitis" in obj_type or "hoone" in obj_type:
        score += 0.08
        reasons.append("building_type_match")

    # primary candidate boost
    if candidate.get("primary"):
        score += 0.05
        reasons.append("primary_candidate")

    # direct numeric ehr code
    ehr_code = str(candidate.get("ehr_code") or "")
    if ehr_code.isdigit():
        score += 0.10
        reasons.append("numeric_ehr_code_present")

    return min(score, 0.99), reasons


def aggregate_candidates(address_input: str, raw_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_ehr: Dict[str, Dict[str, Any]] = {}

    for c in raw_candidates:
        ehr_code = c["ehr_code"]
        group = by_ehr.setdefault(ehr_code, {
            "ehr_code": ehr_code,
            "normalized_address": None,
            "address_aliases": set(),
            "source": "inads",
            "confidence": 0.0,
            "match_reasons": set(),
            "matched_query_variants": set(),
            "object_types": set(),
            "primary": False,
            "raw_candidates": [],
            "variant_hit_count": 0,
        })

        group["raw_candidates"].append(c["raw_candidate"])
        group["matched_query_variants"].add(c["query_variant"])
        group["variant_hit_count"] = len(group["matched_query_variants"])
        group["primary"] = group["primary"] or bool(c.get("primary"))

        if c.get("object_type"):
            group["object_types"].add(str(c["object_type"]))

        if c.get("normalized_address"):
            aliases = split_address_aliases(c["normalized_address"])
            for alias in aliases:
                group["address_aliases"].add(alias)
            # prefer the longest full normalized address
            current = group["normalized_address"] or ""
            if len(c["normalized_address"]) > len(current):
                group["normalized_address"] = c["normalized_address"]

        if c.get("confidence", 0.0) > group["confidence"]:
            group["confidence"] = c["confidence"]

        for r in c.get("match_reasons", []):
            group["match_reasons"].add(r)

    final_candidates: List[Dict[str, Any]] = []
    for group in by_ehr.values():
        # cross-variant agreement boost
        boost = 0.0
        if group["variant_hit_count"] > 1:
            boost += min(0.12, 0.04 * (group["variant_hit_count"] - 1))
        if len(group["address_aliases"]) > 1:
            boost += 0.05  # corner-building / multi-address signal
        if group["primary"]:
            boost += 0.02

        confidence = min(0.99, group["confidence"] + boost)

        final_candidates.append({
            "ehr_code": group["ehr_code"],
            "normalized_address": group["normalized_address"],
            "address_aliases": sorted(group["address_aliases"]),
            "source": group["source"],
            "confidence": round(confidence, 3),
            "match_reasons": sorted(group["match_reasons"]),
            "matched_query_variants": sorted(group["matched_query_variants"]),
            "variant_hit_count": group["variant_hit_count"],
            "object_types": sorted(group["object_types"]),
            "primary": group["primary"],
            "raw_candidate_count": len(group["raw_candidates"]),
            "raw_candidates": group["raw_candidates"][:5],  # keep sample only
        })

    final_candidates.sort(key=lambda x: x["confidence"], reverse=True)
    return final_candidates


def resolve_address_to_ehr(address_input: str, out_dir: Path) -> Dict[str, Any]:
    result = {
        "status": "unresolved",
        "ehr_code": None,
        "normalized_address": None,
        "address_aliases": [],
        "confidence": 0.0,
        "candidates": [],
        "reason": None,
        "source": "inads_gazetteer",
        "query_variants": [],
    }

    components = parse_address_components(address_input)
    query_variants = build_query_variants(components)
    result["query_variants"] = query_variants

    session = make_session(ssl_verify=True)
    attempt_logs: List[Dict[str, Any]] = []
    all_raw_candidates: List[Dict[str, Any]] = []

    for idx, query in enumerate(query_variants, start=1):
        query_url = (
            f"{INADS_BASE_URL}/gazetteer"
            f"?results=10&features={INADS_FEATURES}&address={requests.utils.quote(query, safe='')}"
            f"&seosreg=1&ehr1=1&ehr2=1"
        )

        attempt_log: Dict[str, Any] = {
            "attempt_no": idx,
            "query": query,
            "query_url": query_url,
            "http_status": None,
            "candidate_count": 0,
            "reason": None,
        }

        raw_body_path = out_dir / f"resolver_inads_raw_{idx:02d}.json"
        try:
            resp = session.get(query_url, timeout=60)
            attempt_log["http_status"] = resp.status_code
            raw_body_path.write_text(resp.text, encoding="utf-8", errors="ignore")
        except Exception as e:
            attempt_log["reason"] = f"network_error: {type(e).__name__}: {e}"
            attempt_logs.append(attempt_log)
            continue

        if resp.status_code != 200:
            attempt_log["reason"] = f"http_{resp.status_code}"
            attempt_logs.append(attempt_log)
            continue

        try:
            data = resp.json()
        except Exception:
            attempt_log["reason"] = "non_json_body"
            attempt_logs.append(attempt_log)
            continue

        candidate_objects: List[Dict[str, Any]] = []
        collect_candidate_objects(data, candidate_objects)

        extracted_for_attempt = 0
        for obj in candidate_objects:
            ehr_codes: List[str] = []
            extract_all_ehr_codes(obj, ehr_codes)
            ehr_codes = [c for c in ehr_codes if c.isdigit()]
            if not ehr_codes:
                continue

            normalized_address = extract_candidate_address(obj)
            object_type = extract_object_type(obj)
            primary = is_primary_candidate(obj)

            for ehr_code in set(ehr_codes):
                candidate = {
                    "ehr_code": ehr_code,
                    "normalized_address": normalized_address,
                    "query_variant": query,
                    "object_type": object_type,
                    "primary": primary,
                    "raw_candidate": obj,
                }
                score, reasons = score_candidate(address_input, query, candidate)
                candidate["confidence"] = round(score, 3)
                candidate["match_reasons"] = reasons
                all_raw_candidates.append(candidate)
                extracted_for_attempt += 1

        attempt_log["candidate_count"] = extracted_for_attempt
        if extracted_for_attempt == 0:
            attempt_log["reason"] = "no_extractable_ehr_code_found"
        attempt_logs.append(attempt_log)

    json_dump(attempt_logs, out_dir / "resolver_attempts.json")

    if not all_raw_candidates:
        result["reason"] = "no_extractable_ehr_code_found"
        result["candidates"] = []
        return result

    final_candidates = aggregate_candidates(address_input, all_raw_candidates)
    result["candidates"] = final_candidates

    top = final_candidates[0]
    if top["confidence"] >= AUTO_RESOLVE_THRESHOLD:
        result["status"] = "resolved"
        result["ehr_code"] = top["ehr_code"]
        result["normalized_address"] = top["normalized_address"]
        result["address_aliases"] = top.get("address_aliases", [])
        result["confidence"] = top["confidence"]
        return result

    if top["confidence"] >= AMBIGUOUS_THRESHOLD:
        result["status"] = "ambiguous"
        result["confidence"] = top["confidence"]
        result["reason"] = "multiple_or_weak_candidates"
        return result

    result["confidence"] = top["confidence"]
    result["reason"] = "no_reliable_candidate"
    return result


# ----------------------------
# Source fetch
# ----------------------------

def fetch_pdf(ehr_code: str) -> Tuple[Dict[str, Any], Optional[bytes]]:
    url = f"{EHR_BASE_URL}/pdf/document/file/{ehr_code}"

    session = make_session(ssl_verify=TEST_SSL_VERIFY)
    try:
        resp = session.get(url, headers={"Accept": "application/pdf"}, timeout=90)
        if resp.status_code == 200:
            return {
                "status": "ok",
                "url": url,
                "http_code": resp.status_code,
                "content_type": resp.headers.get("Content-Type", ""),
                "bytes": len(resp.content),
                "ssl_verify": TEST_SSL_VERIFY,
            }, resp.content
        return {
            "status": "failed",
            "url": url,
            "http_code": resp.status_code,
            "response_preview": resp.text[:1000],
            "ssl_verify": TEST_SSL_VERIFY,
        }, None
    except requests.exceptions.SSLError as e:
        ssl_error = str(e)
    except Exception as e:
        return {
            "status": "failed",
            "url": url,
            "error": f"{type(e).__name__}: {e}",
            "ssl_verify": TEST_SSL_VERIFY,
        }, None

    # Retry once without verification
    session = make_session(ssl_verify=False)
    try:
        resp = session.get(url, headers={"Accept": "application/pdf"}, timeout=90)
        if resp.status_code == 200:
            return {
                "status": "ok",
                "url": url,
                "http_code": resp.status_code,
                "content_type": resp.headers.get("Content-Type", ""),
                "bytes": len(resp.content),
                "ssl_verify": False,
                "warning": f"retried_without_tls_verification_after_ssl_error: {ssl_error}",
            }, resp.content
        return {
            "status": "failed",
            "url": url,
            "http_code": resp.status_code,
            "response_preview": resp.text[:1000],
            "ssl_verify": False,
            "warning": f"retried_without_tls_verification_after_ssl_error: {ssl_error}",
        }, None
    except Exception as e:
        return {
            "status": "failed",
            "url": url,
            "error": f"{type(e).__name__}: {e}",
            "ssl_verify": False,
            "warning": f"initial_ssl_error: {ssl_error}",
        }, None


# ----------------------------
# PDF parsing
# ----------------------------

def extract_text_from_pdf(pdf_path: Path) -> str:
    if ensure_package("pypdf"):
        try:
            from pypdf import PdfReader  # type: ignore
            reader = PdfReader(str(pdf_path))
            text = "\n---PAGE---\n".join((page.extract_text() or "") for page in reader.pages)
            if text.strip():
                return text
        except Exception:
            pass

    if shutil.which("pdftotext"):
        txt_path = pdf_path.with_suffix(".txt")
        try:
            subprocess.run(
                ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            text = txt_path.read_text(encoding="utf-8", errors="ignore")
            if text.strip():
                return text
        except Exception:
            pass

    try:
        fallback = subprocess.check_output(["strings", str(pdf_path)], text=True, errors="ignore")
        fallback = "\n".join(fallback.splitlines()[:5000])
        if fallback.strip():
            return fallback
    except Exception:
        pass

    raise RuntimeError("Could not extract text from PDF automatically.")


def build_page_map(text: str) -> Dict[int, str]:
    if "---PAGE---" not in text:
        return {1: text}
    return {i + 1: part for i, part in enumerate(text.split("---PAGE---"))}


def find_with_page(pattern: str, page_map: Dict[int, str], flags: int = 0) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    for page_no, page_text in page_map.items():
        m = re.search(pattern, page_text, flags)
        if m:
            return normalize_multiline_value(m.group(1)), page_no, normalize_multiline_value(m.group(0))
    return None, None, None


def find_first(pattern: str, text: str, flags: int = 0) -> Optional[str]:
    m = re.search(pattern, text, flags)
    return normalize_multiline_value(m.group(1)) if m else None


def parse_use_categories(text: str) -> List[Dict[str, Any]]:
    m = re.search(
        r"Ehitise kasutamise otstarbed\s+Näitaja EHR andmed\s+Kasutamise otstarve,\s+mitteeluruumi pind \(m2\)\s+(.+?)\s+Eluruumide pind kokku",
        text, re.S
    )
    if not m:
        return []
    block = normalize_multiline_value(m.group(1)) or ""
    matches = re.findall(r"([^,]+?\(\d+\))\s*,?\s*([0-9 ]+,\d+)", block)
    out = []
    for raw_name, raw_area in matches:
        code_match = re.search(r"\((\d+)\)", raw_name)
        out.append({
            "name": re.sub(r"\s*\(\d+\)\s*$", "", normalize_multiline_value(raw_name) or "").strip(),
            "classifier_code": code_match.group(1) if code_match else None,
            "area_m2": parse_decimal(raw_area),
            "source": "pdf",
        })
    return out


def parse_geometry(page_map: Dict[int, str]) -> Dict[str, Any]:
    value, page, _ = find_with_page(
        r"Ehitise asukoht\s+Kuju nr Näitaja EHR andmed\s+1 Nimetus\s+Geomeetria moodustusviis\s+(.+?)\s+Ehitisel on",
        page_map, re.S
    )
    if value is None:
        return {"geometry_method": None, "shape_type": None, "coordinates": [], "page": None}
    method_match = re.search(r"^(.+?)\s+Tüüp", value, re.S)
    shape_type_match = re.search(r"Tüüp\s+(.+?)\s+Koordinaadid", value, re.S)
    coords_block_match = re.search(r"Koordinaadid\s+(.+?)\s+Kuju aadressid", value, re.S)
    coords = []
    if coords_block_match:
        pairs = re.findall(r"([0-9]+\.[0-9]+)\s+([0-9]+\.[0-9]+)", coords_block_match.group(1))
        for y, x in pairs:
            coords.append({"y": float(y), "x": float(x)})
    return {
        "geometry_method": normalize_multiline_value(method_match.group(1)) if method_match else None,
        "shape_type": normalize_multiline_value(shape_type_match.group(1)) if shape_type_match else None,
        "coordinates": coords,
        "page": page,
    }


def parse_building_parts(text: str) -> List[Dict[str, Any]]:
    m = re.search(r"Ehitise osad\s+Osa nr Näitaja EHR andmed\s+(.+?)\s+Kokku\s+", text, re.S)
    if not m:
        return []
    block = re.sub(r"---PAGE---.*?Osa nr Näitaja EHR andmed\s+", " ", m.group(1), flags=re.S)
    segments = re.split(r"(?=Ehitise osa tüüp)", block)
    parts = []
    idx = 1
    for seg in segments[1:]:
        seg = seg.strip()
        if not seg:
            continue
        part_type = find_first(r"^Ehitise osa tüüp\s+(.+?)\s+Sissepääsu korrus", seg, re.S)
        shape_no = find_first(r"Ehitise kuju, kus hooneosa\s+asub\s+(\d+)", seg, re.S)
        part_name = find_first(r"Ehitise osa nimetus\s*(.*?)\s+Kasutamise otstarve", seg, re.S)
        part_use = find_first(r"Kasutamise otstarve\s+(.+?)\s+Hooneosa aadress", seg, re.S)
        part_area = find_first(r"Ehitise osa pind \(m2\)\s+([0-9 ]+,\d+)", seg, re.S)
        if not any([part_type, part_name, part_use, part_area]):
            continue
        parts.append({
            "part_identifier": f"part_{idx}",
            "part_type": part_type,
            "shape_no": int(shape_no) if shape_no and shape_no.isdigit() else None,
            "part_name": part_name or None,
            "part_use": part_use,
            "part_area_m2": parse_decimal(part_area),
            "source": "pdf",
        })
        idx += 1
    return parts


def add_obs(observations: List[Observation], field_path: str, value: Any, section: str,
            page: Optional[int], evidence: Optional[str], confidence: str = "confirmed_from_pdf") -> None:
    if value is None:
        return
    observations.append(Observation(
        field_path=field_path,
        value=value,
        section=section,
        source_type="ehr_pdf",
        source_name="public_ehr_pdf",
        page=page,
        confidence=confidence,
        evidence_text=(evidence or "")[:1200],
    ))


def parse_pdf_to_passport(text: str, address_input: Optional[str], resolved_identity: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], List[Observation]]:
    page_map = build_page_map(text)
    obs: List[Observation] = []
    field_specs = {
        "identity.ehr_code": (r"Ehitisregistri kood\s+(\d+)", "identity"),
        "identity.normalized_address": (r"Ehitise aadress\s+(.+?)\s+Ehitisregistri kood", "identity"),
        "building_profile.building_type": (r"Ehitise liik\s+(.+?)\s+Ehitise seisund", "building_profile"),
        "building_profile.building_status": (r"Ehitise seisund\s+(.+?)\s+Ehitise nimetus", "building_profile"),
        "building_profile.building_name": (r"Ehitise nimetus\s+(.+?)\s+Omandi liik", "building_profile"),
        "building_profile.footprint_area_m2": (r"Ehitisealune pind \(m2\)\s+([0-9 ]+,\d+)", "building_profile"),
        "building_profile.heated_area_m2": (r"Köetav pind \(m2\)\s+([0-9 ]+,\d+)", "building_profile"),
        "building_profile.net_area_m2": (r"Suletud netopind \(m2\)\s+([0-9 ]+,\d+)", "building_profile"),
        "building_profile.public_use_area_m2": (r"Üldkasutatav pind \(m2\)\s+([0-9 ]+,\d+)", "building_profile"),
        "building_profile.technical_area_m2": (r"Tehnopind \(m2\)\s+([0-9 ]+,\d+)", "building_profile"),
        "building_profile.floors_above_ground": (r"Maapealsete korruste arv\s+(\d+)", "building_profile"),
        "building_profile.floors_below_ground": (r"Maa-aluste korruste arv\s+(\d+)", "building_profile"),
        "building_profile.height_m": (r"Kõrgus \(m\)\s+([0-9 ]+,\d+)", "building_profile"),
        "building_profile.length_m": (r"Pikkus \(m\)\s+([0-9 ]+,\d+)", "building_profile"),
        "building_profile.width_m": (r"Laius \(m\)\s+([0-9 ]+,\d+)", "building_profile"),
        "building_profile.depth_m": (r"Sügavus \(m\)\s+([0-9 ]+,\d+)", "building_profile"),
        "building_profile.volume_m3": (r"Maht \(m3\)\s+([0-9 ]+,\d+)", "building_profile"),
        "structural_systems.foundation_type": (r"Vundamendi liik\s+(.+?)\s+Kande- ja jäigastavate", "structural_systems"),
        "structural_systems.load_bearing_material": (r"Kande- ja jäigastavate\s+konstruktsioonide materjali liik\s+(.+?)\s+Välisseina liik", "structural_systems"),
        "structural_systems.wall_type": (r"Välisseina liik\s+(.+?)\s+Välisseina välisviimistluse", "structural_systems"),
        "structural_systems.facade_finish_material": (r"Välisseina välisviimistluse\s+materjali liik\s+(.+?)\s+Vahelagede kandva osa", "structural_systems"),
        "structural_systems.floor_structure_material": (r"Vahelagede kandva osa\s+materjali liik\s+(.+?)\s+Katuse ja katuslagede kandva", "structural_systems"),
        "structural_systems.roof_structure_material": (r"Katuse ja katuslagede kandva\s+osa materjali liik\s+(.+?)\s+Katusekatte materjali liik", "structural_systems"),
        "structural_systems.roof_covering_material": (r"Katusekatte materjali liik\s+(.+?)\s+Ehitise tehnilised näitajad", "structural_systems"),
        "technical_systems.electricity": (r"Elektrisüsteemi liik\s+(.+?)\s+Veevarustuse liik", "technical_systems"),
        "technical_systems.water": (r"Veevarustuse liik\s+(.+?)\s+Kanalistasiooni liik", "technical_systems"),
        "technical_systems.sewer": (r"Kanalistasiooni liik\s+(.+?)\s+Soojusallika liik", "technical_systems"),
        "technical_systems.heat_source": (r"Soojusallika liik\s+(.+?)\s+Energiaallika liik", "technical_systems"),
        "technical_systems.gas": (r"Energiaallika liik\s+(.+?)\s+Ventilatsiooni liik", "technical_systems"),
        "technical_systems.ventilation": (r"Ventilatsiooni liik\s+(.+?)\s+Jahutussüsteemi liik", "technical_systems"),
        "technical_systems.lift_count": (r"Liftide arv\s+(\d+)", "technical_systems"),
    }

    passport = {
        "identity": {
            "ehr_code": None,
            "normalized_address": None,
            "address_aliases": [],
            "country": "EE",
            "input_address": address_input,
        },
        "building_profile": {
            "building_type": None,
            "building_status": None,
            "building_name": None,
            "use_categories": [],
            "floors": {"above_ground": None, "below_ground": None},
            "footprint_area_m2": None,
            "heated_area_m2": None,
            "net_area_m2": None,
            "public_use_area_m2": None,
            "technical_area_m2": None,
            "height_m": None,
            "length_m": None,
            "width_m": None,
            "depth_m": None,
            "volume_m3": None,
        },
        "structural_systems": {
            "foundation_type": None,
            "load_bearing_material": None,
            "wall_type": None,
            "facade_finish_material": None,
            "floor_structure_material": None,
            "roof_structure_material": None,
            "roof_covering_material": None,
        },
        "technical_systems": {
            "electricity": None,
            "water": None,
            "sewer": None,
            "heat_source": None,
            "gas": None,
            "ventilation": None,
            "lift_count": None,
        },
        "location": {
            "geometry_method": None,
            "shape_type": None,
            "coordinates": [],
        },
        "building_parts": [],
        "quality": {
            "schema_completeness_score": None,
            "confidence_score": None,
            "provenance_by_section": {},
            "missing_fields": [],
        },
        "meta": {
            "schema_version": "buildloop.passport.mvp.v1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_strategy": "address_to_ehr_then_pdf_canonical",
        }
    }

    for field_path, (pattern, section) in field_specs.items():
        value, page, evidence = find_with_page(pattern, page_map, re.S)
        if value is None:
            continue
        if field_path.endswith(("_m2", "_m3", "_m")):
            v = parse_decimal(value)
        elif field_path.endswith(("lift_count", "floors_above_ground", "floors_below_ground")):
            v = int(float(value))
        else:
            v = value

        if field_path == "identity.ehr_code":
            passport["identity"]["ehr_code"] = v
        elif field_path == "identity.normalized_address":
            passport["identity"]["normalized_address"] = v
        elif field_path == "building_profile.floors_above_ground":
            passport["building_profile"]["floors"]["above_ground"] = v
        elif field_path == "building_profile.floors_below_ground":
            passport["building_profile"]["floors"]["below_ground"] = v
        elif field_path.startswith("building_profile."):
            passport["building_profile"][field_path.split(".", 1)[1]] = v
        elif field_path.startswith("structural_systems."):
            passport["structural_systems"][field_path.split(".", 1)[1]] = v
        elif field_path.startswith("technical_systems."):
            passport["technical_systems"][field_path.split(".", 1)[1]] = v

        add_obs(obs, field_path, v, section, page, evidence)

    # Prefer resolver address aliases if they exist
    if resolved_identity:
        if resolved_identity.get("normalized_address"):
            passport["identity"]["normalized_address"] = resolved_identity["normalized_address"]
        aliases = resolved_identity.get("address_aliases") or []
        if aliases:
            passport["identity"]["address_aliases"] = aliases
            add_obs(
                obs,
                "identity.address_aliases",
                aliases,
                "identity",
                None,
                "Resolver v3 aggregated address aliases",
                confidence="derived",
            )
        if resolved_identity.get("ehr_code"):
            passport["identity"]["ehr_code"] = resolved_identity["ehr_code"]

    # If no aliases from resolver, derive from normalized PDF address if it uses corner notation
    if not passport["identity"]["address_aliases"]:
        aliases = split_address_aliases(passport["identity"]["normalized_address"])
        if len(aliases) > 1:
            passport["identity"]["address_aliases"] = aliases
            add_obs(
                obs,
                "identity.address_aliases",
                aliases,
                "identity",
                None,
                "Derived from normalized address with // separator",
                confidence="derived",
            )

    use_categories = parse_use_categories(text)
    passport["building_profile"]["use_categories"] = use_categories
    if use_categories:
        add_obs(obs, "building_profile.use_categories", use_categories, "building_profile", 1, "Ehitise kasutamise otstarbed")

    geo = parse_geometry(page_map)
    passport["location"]["geometry_method"] = geo["geometry_method"]
    passport["location"]["shape_type"] = geo["shape_type"]
    passport["location"]["coordinates"] = geo["coordinates"]
    if geo["coordinates"]:
        add_obs(obs, "location.coordinates", geo["coordinates"], "location", geo["page"], "Ehitise asukoht / Koordinaadid")

    parts = parse_building_parts(text)
    passport["building_parts"] = parts
    if parts:
        add_obs(obs, "building_parts", parts, "building_parts", 4, "Ehitise osad")

    return passport, obs


def compute_quality(passport: Dict[str, Any], checklist: Dict[str, List[str]], observations: List[Observation]) -> None:
    def has_value(section: str, field: str) -> bool:
        if section == "identity":
            return passport["identity"].get(field) not in (None, "", [])
        if section == "building_profile":
            if field == "floors":
                f = passport["building_profile"]["floors"]
                return f.get("above_ground") is not None or f.get("below_ground") is not None
            return passport["building_profile"].get(field) not in (None, "", [])
        if section == "structural_systems":
            return passport["structural_systems"].get(field) not in (None, "", [])
        if section == "technical_systems":
            return passport["technical_systems"].get(field) not in (None, "", [])
        if section == "building_parts":
            return len(passport["building_parts"]) > 0
        if section == "quality":
            return True
        return False

    total = 0
    present = 0
    missing = []
    provenance = {}

    for section, fields in checklist.items():
        section_present = 0
        section_total = 0
        for field in fields:
            total += 1
            section_total += 1
            ok = has_value(section, field)
            if ok:
                present += 1
                section_present += 1
            else:
                missing.append(f"{section}.{field}")
        provenance[section] = {
            "present_fields": section_present,
            "total_fields": section_total,
            "source_types": sorted({o.source_type for o in observations if o.section == section}),
        }

    schema_completeness = round((present / total) * 100, 1) if total else 0.0
    weights = {"confirmed_from_pdf": 0.85, "confirmed_from_json": 0.95, "derived": 0.60, "debug_fallback": 0.30}
    avg_conf = (sum(weights.get(o.confidence, 0.5) for o in observations) / len(observations)) if observations else 0.0

    passport["quality"]["schema_completeness_score"] = schema_completeness
    passport["quality"]["confidence_score"] = round(avg_conf * 100, 1)
    passport["quality"]["provenance_by_section"] = provenance
    passport["quality"]["missing_fields"] = missing


def observations_to_dicts(observations: List[Observation]) -> List[Dict[str, Any]]:
    return [asdict(o) for o in observations]


def write_summary(out_dir: Path, result: Dict[str, Any]) -> None:
    passport = result.get("passport") or {}
    bp = passport.get("building_profile", {})
    lines = [
        "# BuildLoop Passport From Address Summary",
        "",
        f"- Input address: {result.get('input_address') or '<missing>'}",
        f"- Resolution status: {result.get('resolution', {}).get('status')}",
        f"- Resolved EHR code: {result.get('resolved_ehr_code') or '<missing>'}",
        f"- Fetch status: {result.get('fetch', {}).get('status')}",
        f"- Parse status: {result.get('parse_status')}",
        "",
        "## Output files",
        "",
        "- pipeline_result.json",
        "- address_resolution.json",
        "- resolver_attempts.json",
        "- source_fetch.json",
        "- passport_mvp.json",
        "- observations.json",
        "- source_manifest.json",
        "- run_summary.md",
    ]
    if passport:
        lines += [
            "",
            "## Passport draft",
            "",
            f"- Address: {passport.get('identity', {}).get('normalized_address') or '<missing>'}",
            f"- Address aliases: {len(passport.get('identity', {}).get('address_aliases', []))}",
            f"- Building type: {bp.get('building_type') or '<missing>'}",
            f"- Building status: {bp.get('building_status') or '<missing>'}",
            f"- Use categories: {len(bp.get('use_categories', []))}",
            f"- Building parts: {len(passport.get('building_parts', []))}",
            f"- Schema completeness score: {passport.get('quality', {}).get('schema_completeness_score')}",
            f"- Confidence score: {passport.get('quality', {}).get('confidence_score')}",
        ]
    (out_dir / "run_summary.md").write_text("\n".join(lines), encoding="utf-8")


def run_pipeline(address: str, batch_root: Path) -> Dict[str, Any]:
    subdir = f"{now_utc()}_{slugify(address)}_{hashlib.md5(address.encode('utf-8')).hexdigest()[:6]}"
    out_dir = batch_root / subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    checklist = load_checklist()

    result = {
        "input_address": address,
        "resolved_ehr_code": None,
        "resolution": None,
        "fetch": None,
        "parse_status": None,
        "passport": None,
        "artifacts_dir": str(out_dir),
    }

    # 1) Resolve address -> EHR code
    resolution = resolve_address_to_ehr(address, out_dir)
    result["resolution"] = resolution
    json_dump(resolution, out_dir / "address_resolution.json")

    if resolution.get("status") != "resolved":
        result["fetch"] = {"status": "blocked", "reason": "Address was not resolved to a reliable EHR code"}
        result["parse_status"] = "blocked"
        json_dump(result["fetch"], out_dir / "source_fetch.json")
        manifest = {
            "source_pdf": None,
            "source_txt": None,
            "fetch_status": result["fetch"],
            "ehr_base_url": EHR_BASE_URL,
            "notes": [
                "Address resolution did not reach auto-resolve threshold.",
                "Inspect address_resolution.json, resolver_attempts.json, resolver_inads_raw_*.json.",
            ],
        }
        json_dump(manifest, out_dir / "source_manifest.json")
        json_dump(result, out_dir / "pipeline_result.json")
        write_summary(out_dir, result)
        return {
            "input_address": address,
            "artifacts_dir": str(out_dir),
            "status": "resolution_failed",
            "resolved_ehr_code": None,
            "confidence": resolution.get("confidence"),
            "candidate_count": len(resolution.get("candidates") or []),
        }

    ehr_code = resolution["ehr_code"]
    result["resolved_ehr_code"] = ehr_code

    # 2) Fetch PDF
    fetch_meta, pdf_bytes = fetch_pdf(ehr_code)
    result["fetch"] = fetch_meta
    json_dump(fetch_meta, out_dir / "source_fetch.json")

    if fetch_meta.get("status") != "ok" or not pdf_bytes:
        result["parse_status"] = "blocked"
        manifest = {
            "source_pdf": None,
            "source_txt": None,
            "fetch_status": fetch_meta,
            "ehr_base_url": EHR_BASE_URL,
        }
        json_dump(manifest, out_dir / "source_manifest.json")
        json_dump(result, out_dir / "pipeline_result.json")
        write_summary(out_dir, result)
        return {
            "input_address": address,
            "artifacts_dir": str(out_dir),
            "status": "fetch_failed",
            "resolved_ehr_code": ehr_code,
            "confidence": resolution.get("confidence"),
            "candidate_count": len(resolution.get("candidates") or []),
        }

    source_pdf = out_dir / "source_document.pdf"
    source_pdf.write_bytes(pdf_bytes)

    # 3) Extract text
    text = extract_text_from_pdf(source_pdf)
    source_txt = out_dir / "source_document.txt"
    source_txt.write_text(text, encoding="utf-8")

    # 4) Parse
    resolved_identity = {
        "ehr_code": resolution.get("ehr_code"),
        "normalized_address": resolution.get("normalized_address"),
        "address_aliases": resolution.get("address_aliases") or [],
    }
    passport, observations = parse_pdf_to_passport(text, address, resolved_identity=resolved_identity)
    compute_quality(passport, checklist, observations)
    result["parse_status"] = "ok"
    result["passport"] = passport

    manifest = {
        "source_pdf": str(source_pdf),
        "source_txt": str(source_txt),
        "fetch_status": fetch_meta,
        "ehr_base_url": EHR_BASE_URL,
        "source_strategy": "address_to_ehr_then_pdf_canonical",
        "notes": [
            "Resolver v3 groups candidates by EHR code.",
            "Confidence is boosted when multiple query variants hit the same building.",
            "Corner / multi-address buildings preserve address aliases.",
            "PDF is the canonical source for MVP extraction.",
        ],
    }

    json_dump(passport, out_dir / "passport_mvp.json")
    json_dump(observations_to_dicts(observations), out_dir / "observations.json")
    json_dump(manifest, out_dir / "source_manifest.json")
    json_dump(result, out_dir / "pipeline_result.json")
    write_summary(out_dir, result)

    return {
        "input_address": address,
        "artifacts_dir": str(out_dir),
        "status": "ok",
        "resolved_ehr_code": ehr_code,
        "confidence": resolution.get("confidence"),
        "candidate_count": len(resolution.get("candidates") or []),
        "normalized_address": resolution.get("normalized_address"),
        "address_aliases": resolution.get("address_aliases") or [],
        "schema_completeness_score": passport["quality"]["schema_completeness_score"],
    }


if __name__ == "__main__":
    batch_root = OUTPUT_ROOT / f"batch_{now_utc()}"
    batch_root.mkdir(parents=True, exist_ok=True)

    batch_results = []
    for address in TEST_ADDRESSES:
        print(f"\n=== RUNNING: {address} ===")
        batch_results.append(run_pipeline(address, batch_root))

    batch_summary = {
        "batch_root": str(batch_root),
        "total_addresses": len(TEST_ADDRESSES),
        "results": batch_results,
    }
    json_dump(batch_summary, batch_root / "batch_summary.json")

    print(f"\nBatch root: {batch_root}")
    print("\n===== batch_summary.json =====")
    print((batch_root / "batch_summary.json").read_text(encoding="utf-8"))
