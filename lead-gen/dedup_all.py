#!/usr/bin/env python3
"""Merge and deduplicate all lead CSVs across menuBoost, menuboost, and boostsuite."""

import csv
import os
import sys
from pathlib import Path

BASE = Path("/home/darko/.openclaw/workspace/lead-gen")

# Directories to scan
DIRS = {
    "menuBoost": BASE / "menuBoost",
    "menuboost": BASE / "menuboost",
    "boostsuite": BASE / "boostsuite",
}

# Skip ListTranslate
SKIP = {"listtranslate"}

# Column mapping: normalize various headers to canonical names
COL_MAP = {
    # name
    "name": "name", "ime": "name", "company name": "name", "company": "name",
    "first_name": "_first", "last_name": "_last",
    # email
    "email": "email",
    # website/url
    "website": "website", "url": "website",
    # city
    "city": "city",
    # region/state/country
    "region": "region", "state": "region", "country": "country", "location": "location",
    # type
    "type": "type",
    # source
    "source": "source",
    # notes
    "notes": "notes",
    # specialty
    "specialty": "specialty",
    # extra
    "owner_or_chef": "contact", "contact": "contact", "pain_point": "notes",
    "verified": "_skip", "valid": "_skip", "verify_reason": "_skip",
    "page": "_skip", "line": "_skip", "context": "_skip", "number": "_skip",
    "date": "_skip", "naslov": "_skip",  # naslov = address in Slovenian, skip for dedup
}


def normalize_row(row, header):
    """Map a raw row to normalized fields."""
    out = {}
    for i, col in enumerate(header):
        key = col.strip().lower().strip('"')
        val = row[i].strip().strip('"') if i < len(row) else ""
        mapped = COL_MAP.get(key, key)
        if mapped == "_skip" or mapped == "_first" or mapped == "_last":
            continue
        if mapped and val:
            out[mapped] = val

    # Combine _first + _last into name if present
    first = ""
    last = ""
    for i, col in enumerate(header):
        key = col.strip().lower()
        if key == "first_name" and i < len(row):
            first = row[i].strip()
        elif key == "last_name" and i < len(row):
            last = row[i].strip()
    if first or last:
        out["name"] = f"{first} {last}".strip()

    return out


def dedup_key(row):
    """Generate a dedup key from email (primary) or name+city (secondary)."""
    email = row.get("email", "").lower().strip()
    if email:
        return ("email", email)
    name = row.get("name", "").lower().strip()
    city = row.get("city", "").lower().strip()
    location = row.get("location", "").lower().strip()
    if name and (city or location):
        return ("name_city", f"{name}|{city or location}")
    return None


def read_csv_flexible(filepath):
    """Read CSV trying multiple encodings and dialects."""
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            with open(filepath, "r", encoding=enc, errors="strict") as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        return [], []

    # Some files have no header or weird formats
    lines = content.strip().split("\n")
    if not lines:
        return [], []

    # Detect if first line looks like a header (contains common column names)
    first_lower = lines[0].lower()
    header_keywords = ["name", "email", "website", "url", "type", "source", "city", "ime", "company"]
    has_header = any(kw in first_lower for kw in header_keywords)

    if has_header:
        reader = csv.reader(lines)
        header = next(reader)
        rows = [r for r in reader if any(cell.strip() for cell in r)]
        return header, rows
    else:
        # Try to parse as space-separated (like leads-menuBoost.csv)
        return [], []


def merge_and_dedup():
    all_leads = {}  # key -> (row, project, source_file)
    stats = {"total_files": 0, "total_rows": 0, "duplicates": 0, "no_email": 0}

    for project, dirpath in DIRS.items():
        if not dirpath.exists():
            print(f"⚠️  Directory not found: {dirpath}")
            continue

        csv_files = sorted(dirpath.rglob("*.csv"))
        print(f"\n📁 {project}: {len(csv_files)} CSV files")

        for fpath in csv_files:
            # Skip deduped outputs
            if "DEDUPED" in fpath.name.upper():
                continue

            header, rows = read_csv_flexible(fpath)
            if not header or not rows:
                print(f"   ⏭️  {fpath.name}: skipped (no header/unparseable)")
                continue

            stats["total_files"] += 1
            file_count = 0

            for row in rows:
                stats["total_rows"] += 1
                normalized = normalize_row(row, header)

                if not normalized.get("email") and not normalized.get("name"):
                    stats["no_email"] += 1
                    continue

                key = dedup_key(normalized)
                if key is None:
                    stats["no_email"] += 1
                    continue

                if key in all_leads:
                    stats["duplicates"] += 1
                    # Keep the one with more data
                    existing = all_leads[key][0]
                    existing_fields = sum(1 for v in existing.values() if v)
                    new_fields = sum(1 for v in normalized.values() if v)
                    if new_fields > existing_fields:
                        all_leads[key] = (normalized, project, fpath.name)
                else:
                    all_leads[key] = (normalized, project, fpath.name)
                    file_count += 1

            print(f"   ✅ {fpath.name}: {len(rows)} rows → {file_count} new")

    # Split back by project
    by_project = {"menuBoost": [], "menuboost": [], "boostsuite": []}
    for key, (row, project, _) in all_leads.items():
        row["project"] = project
        by_project[project].append(row)

    # Write output files
    OUTPUT_FIELDS = ["name", "email", "website", "city", "region", "country",
                     "location", "type", "source", "specialty", "contact",
                     "notes", "project"]

    for project, leads in by_project.items():
        if not leads:
            continue
        # Sort by name, then email
        leads.sort(key=lambda x: (x.get("name", "").lower(), x.get("email", "").lower()))
        outpath = BASE / f"{project}-DEDUPED.csv"
        with open(outpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(leads)
        emails = sum(1 for l in leads if l.get("email"))
        print(f"\n💾 {project}-DEDUPED.csv: {len(leads)} leads ({emails} with email)")

    # Combined file
    all_combined = []
    for leads in by_project.values():
        all_combined.extend(leads)
    all_combined.sort(key=lambda x: (x.get("project", ""), x.get("name", "").lower()))

    combined_path = BASE / "ALL-DEDUPED.csv"
    with open(combined_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_combined)

    total_emails = sum(1 for l in all_combined if l.get("email"))
    print(f"\n💾 ALL-DEDUPED.csv: {len(all_combined)} total leads ({total_emails} with email)")

    # Summary
    print(f"\n{'='*50}")
    print(f"📊 SUMMARY")
    print(f"{'='*50}")
    print(f"Files scanned:    {stats['total_files']}")
    print(f"Total rows:       {stats['total_rows']}")
    print(f"Duplicates found: {stats['duplicates']}")
    print(f"No email/name:    {stats['no_email']}")
    print(f"Final unique:     {len(all_combined)}")
    for p, leads in by_project.items():
        if leads:
            e = sum(1 for l in leads if l.get("email"))
            print(f"  {p}: {len(leads)} ({e} with email)")


if __name__ == "__main__":
    merge_and_dedup()
