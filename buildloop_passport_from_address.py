#!/usr/bin/env python3
"""
BuildLoop address-only passport pipeline (MVP)

Usage:
    python buildloop_passport_from_address.py "Lai 1, Nunne tn 4, 10133 Tallinn, Estonia"

What it does:
1. Accepts one address from the user
2. Resolves address -> EHR code using public address search
3. Fetches the public EHR PDF by EHR code
4. Extracts structured passport data from the PDF
5. Writes artifacts:
   - address_resolution.json
   - source_fetch.json
   - source_document.pdf
   - source_document.txt
   - passport_mvp.json
   - observations.json
   - source_manifest.json
   - pipeline_result.json
   - run_summary.md

Notes:
- PDF is treated as the canonical source for MVP passport extraction.
- Address resolution is best-effort. If the match is weak or ambiguous, the script
  writes candidates and exits without guessing.
- If TLS verification fails in notebook/runtime environments, the script retries once
  with SSL verification disabled and records that in the manifest.
"""

from __future__ import annotations

import argparse
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


OUTPUT_ROOT = Path(os.environ.get("OUTPUT_ROOT", "./artifacts")).resolve()
EHR_BASE_URL = os.environ.get("EHR_BASE_URL", "https://livekluster.ehr.ee/api/document/v1").rstrip("/")
INADS_BASE_URL = os.environ.get("INADS_BASE_URL", "https://inaadress.maaamet.ee/inaadress").rstrip("/")
INADS_FEATURES = os.environ.get("INADS_FEATURES", "EHAK,VAIKEKOHT,TANAV,KATASTRIYKSUS,EHITISHOONE")
CHECKLIST_JSON_ENV = os.environ.get("CHECKLIST_JSON", "").strip()

# Auto-resolve only if score is strong. Otherwise return candidates.
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
        "User-Agent": "BuildLoop-Passport-From-Address/1.0",
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
# Address resolution
# ----------------------------

def normalize_address_for_match(address: str) -> str:
    address = address.lower()
    address = address.replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("õ", "o")
    address = re.sub(r"[^a-z0-9]+", " ", address)
    return re.sub(r"\s+", " ", address).strip()


def walk_for_ehr_candidates(node: Any, bag: List[Dict[str, Any]]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            lk = str(k).lower()
            if lk in {"ehr_kood", "ehrcode", "ehr_code"} and isinstance(v, (str, int)):
                bag.append({"ehr_code": str(v), "raw_candidate": node})
            elif lk == "ehr" and isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        for kk in ("ehr_kood", "ehrcode", "ehr_code"):
                            if kk in item and item[kk]:
                                bag.append({"ehr_code": str(item[kk]), "raw_candidate": item})
            walk_for_ehr_candidates(v, bag)
    elif isinstance(node, list):
        for item in node:
            walk_for_ehr_candidates(item, bag)


def extract_candidate_address(candidate: Dict[str, Any]) -> Optional[str]:
    raw = candidate.get("raw_candidate", {})
    if not isinstance(raw, dict):
        return None

    possible_keys = [
        "taisaadress", "aadress", "address", "lahiaadress",
        "nimi", "nimetus", "ads_lahiaadress"
    ]
    for key in possible_keys:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for v in raw.values():
        if isinstance(v, dict):
            for key in possible_keys:
                value = v.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return None


def score_candidate(address_input: str, candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
    reasons: List[str] = []
    score = 0.0

    normalized_input = normalize_address_for_match(address_input)
    normalized_candidate = normalize_address_for_match(candidate.get("normalized_address") or "")

    input_tokens = set(normalized_input.split())
    cand_tokens = set(normalized_candidate.split())
    overlap = input_tokens & cand_tokens
    if overlap:
        overlap_ratio = len(overlap) / max(1, len(input_tokens))
        score += 0.45 * overlap_ratio
        reasons.append(f"token_overlap={overlap_ratio:.2f}")

    input_nums = re.findall(r"\d+[a-z]?", normalized_input)
    cand_nums = re.findall(r"\d+[a-z]?", normalized_candidate)
    if input_nums and cand_nums and any(n in cand_nums for n in input_nums):
        score += 0.30
        reasons.append("house_number_match")

    for token in ("tallinn", "kesklinna", "harju", "estonia"):
        if token in normalized_input and token in normalized_candidate:
            score += 0.03
            reasons.append(f"locality_match:{token}")

    ehr_code = str(candidate.get("ehr_code") or "")
    if ehr_code.isdigit():
        score += 0.10
        reasons.append("numeric_ehr_code_present")

    return min(score, 0.99), reasons


def resolve_address_to_ehr(address_input: str, out_dir: Path, session: requests.Session) -> Dict[str, Any]:
    result = {
        "status": "unresolved",
        "ehr_code": None,
        "normalized_address": None,
        "confidence": 0.0,
        "candidates": [],
        "reason": None,
        "source": "inads_gazetteer",
        "query_url": None,
    }

    query_url = (
        f"{INADS_BASE_URL}/gazetteer"
        f"?results=10&features={INADS_FEATURES}&address={requests.utils.quote(address_input, safe='')}"
        f"&seosreg=1&ehr1=1&ehr2=1"
    )
    result["query_url"] = query_url

    raw_body_path = out_dir / "resolver_inads_raw.json"
    try:
        resp = session.get(query_url, timeout=60)
        raw_body_path.write_text(resp.text, encoding="utf-8", errors="ignore")
    except Exception as e:
        result["reason"] = f"resolver_network_error: {type(e).__name__}: {e}"
        return result

    if resp.status_code != 200:
        result["reason"] = f"resolver_http_{resp.status_code}"
        return result

    try:
        data = resp.json()
    except Exception:
        result["reason"] = "resolver_non_json_body"
        return result

    raw_candidates: List[Dict[str, Any]] = []
    walk_for_ehr_candidates(data, raw_candidates)

    seen = set()
    candidates: List[Dict[str, Any]] = []
    for c in raw_candidates:
        ehr_code = str(c.get("ehr_code") or "")
        if not ehr_code.isdigit() or ehr_code in seen:
            continue
        seen.add(ehr_code)

        norm_addr = extract_candidate_address(c)
        score, reasons = score_candidate(address_input, {
            "ehr_code": ehr_code,
            "normalized_address": norm_addr,
        })
        candidates.append({
            "ehr_code": ehr_code,
            "normalized_address": norm_addr,
            "source": "inads",
            "confidence": round(score, 3),
            "match_reasons": reasons,
            "raw_candidate": c.get("raw_candidate"),
        })

    candidates.sort(key=lambda x: x["confidence"], reverse=True)
    result["candidates"] = candidates

    if not candidates:
        result["reason"] = "no_extractable_ehr_code_found"
        return result

    top = candidates[0]
    if top["confidence"] >= AUTO_RESOLVE_THRESHOLD:
        result["status"] = "resolved"
        result["ehr_code"] = top["ehr_code"]
        result["normalized_address"] = top["normalized_address"]
        result["confidence"] = top["confidence"]
        return result

    if top["confidence"] >= AMBIGUOUS_THRESHOLD:
        result["status"] = "ambiguous"
        result["reason"] = "multiple_or_weak_candidates"
        result["confidence"] = top["confidence"]
        return result

    result["reason"] = "no_reliable_candidate"
    result["confidence"] = top["confidence"]
    return result


# ----------------------------
# Source fetch
# ----------------------------

def fetch_pdf(ehr_code: str, out_path: Path) -> Dict[str, Any]:
    url = f"{EHR_BASE_URL}/pdf/document/file/{ehr_code}"

    # First try verified TLS
    session = make_session(ssl_verify=True)
    try:
        resp = session.get(url, headers={"Accept": "application/pdf"}, timeout=90)
        if resp.status_code == 200:
            out_path.write_bytes(resp.content)
            return {
                "status": "ok",
                "url": url,
                "http_code": resp.status_code,
                "content_type": resp.headers.get("Content-Type", ""),
                "bytes": len(resp.content),
                "ssl_verify": True,
            }
        return {
            "status": "failed",
            "url": url,
            "http_code": resp.status_code,
            "response_preview": resp.text[:1000],
            "ssl_verify": True,
        }
    except requests.exceptions.SSLError as e:
        ssl_error = str(e)
    except Exception as e:
        return {"status": "failed", "url": url, "error": f"{type(e).__name__}: {e}", "ssl_verify": True}

    # Retry once without TLS verification for dev/notebook environments
    session = make_session(ssl_verify=False)
    try:
        resp = session.get(url, headers={"Accept": "application/pdf"}, timeout=90)
        if resp.status_code == 200:
            out_path.write_bytes(resp.content)
            return {
                "status": "ok",
                "url": url,
                "http_code": resp.status_code,
                "content_type": resp.headers.get("Content-Type", ""),
                "bytes": len(resp.content),
                "ssl_verify": False,
                "warning": f"retried_without_tls_verification_after_ssl_error: {ssl_error}",
            }
        return {
            "status": "failed",
            "url": url,
            "http_code": resp.status_code,
            "response_preview": resp.text[:1000],
            "ssl_verify": False,
            "warning": f"retried_without_tls_verification_after_ssl_error: {ssl_error}",
        }
    except Exception as e:
        return {
            "status": "failed",
            "url": url,
            "error": f"{type(e).__name__}: {e}",
            "ssl_verify": False,
            "warning": f"initial_ssl_error: {ssl_error}",
        }


# ----------------------------
# PDF parsing
# ----------------------------

def extract_text_from_pdf(pdf_path: Path) -> str:
    # 1) Try pypdf, auto-install if needed.
    if ensure_package("pypdf"):
        try:
            from pypdf import PdfReader  # type: ignore
            reader = PdfReader(str(pdf_path))
            text = "\n---PAGE---\n".join((page.extract_text() or "") for page in reader.pages)
            if text.strip():
                return text
        except Exception:
            pass

    # 2) Try system pdftotext if available.
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

    # 3) Last resort: printable strings.
    try:
        fallback = subprocess.check_output(["strings", str(pdf_path)], text=True, errors="ignore")
        fallback = "\n".join(fallback.splitlines()[:5000])
        if fallback.strip():
            return fallback
    except Exception:
        pass

    raise RuntimeError(
        "Could not extract text from PDF automatically. "
        "Install pypdf/pdftotext in the environment."
    )


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


def parse_pdf_to_passport(text: str, address_input: Optional[str]) -> Tuple[Dict[str, Any], List[Observation]]:
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
            f"- Building type: {bp.get('building_type') or '<missing>'}",
            f"- Building status: {bp.get('building_status') or '<missing>'}",
            f"- Use categories: {len(bp.get('use_categories', []))}",
            f"- Building parts: {len(passport.get('building_parts', []))}",
            f"- Schema completeness score: {passport.get('quality', {}).get('schema_completeness_score')}",
            f"- Confidence score: {passport.get('quality', {}).get('confidence_score')}",
        ]
    (out_dir / "run_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="BuildLoop address-only passport pipeline")
    parser.add_argument("address", help="User-provided address")
    args = parser.parse_args()

    input_address = args.address.strip()
    if not input_address:
        parser.error("Address must not be empty")

    run_id = f"pipeline_{now_utc()}"
    out_dir = OUTPUT_ROOT / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    checklist = load_checklist()

    result = {
        "input_address": input_address,
        "resolved_ehr_code": None,
        "resolution": None,
        "fetch": None,
        "parse_status": None,
        "passport": None,
        "artifacts_dir": str(out_dir),
    }

    # 1) Resolve address -> EHR code
    resolver_session = make_session(ssl_verify=True)
    resolution = resolve_address_to_ehr(input_address, out_dir, resolver_session)
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
                "Inspect address_resolution.json and resolver_inads_raw.json.",
            ],
        }
        json_dump(manifest, out_dir / "source_manifest.json")
        json_dump(result, out_dir / "pipeline_result.json")
        write_summary(out_dir, result)
        print(out_dir)
        return 0

    ehr_code = resolution["ehr_code"]
    result["resolved_ehr_code"] = ehr_code

    # 2) Fetch PDF by EHR code
    source_pdf = out_dir / "source_document.pdf"
    fetch_meta = fetch_pdf(ehr_code, source_pdf)
    result["fetch"] = fetch_meta
    json_dump(fetch_meta, out_dir / "source_fetch.json")

    if fetch_meta.get("status") != "ok" or not source_pdf.exists():
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
        print(out_dir)
        return 0

    # 3) Extract text from PDF
    text = extract_text_from_pdf(source_pdf)
    source_txt = out_dir / "source_document.txt"
    source_txt.write_text(text, encoding="utf-8")

    # 4) Parse PDF -> passport
    passport, observations = parse_pdf_to_passport(text, input_address)
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
            "Address resolution is best-effort and does not auto-pick weak matches.",
            "PDF is the canonical source for MVP extraction.",
        ],
    }

    json_dump(passport, out_dir / "passport_mvp.json")
    json_dump(observations_to_dicts(observations), out_dir / "observations.json")
    json_dump(manifest, out_dir / "source_manifest.json")
    json_dump(result, out_dir / "pipeline_result.json")
    write_summary(out_dir, result)

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
