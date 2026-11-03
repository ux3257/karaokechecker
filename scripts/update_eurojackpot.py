#!/usr/bin/env python3
"""
Holt neue Eurojackpot-Ziehungen und hängt sie an data/eurojackpot.csv an.

Zwei unabhängige Archivseiten werden gelesen und gegeneinander geprüft:
  A  https://www.euro-jackpot.net/de/gewinnzahlen-archiv-JJJJ
  B  https://www.eurojackpot-zahlen.eu/eurojackpot-zahlenarchiv.php?j=JJJJ

Regeln
  * Eine neue Ziehung wird übernommen, wenn beide Quellen sie identisch liefern.
  * Liefert nur eine Quelle die Ziehung, wird sie erst übernommen, wenn sie
    mindestens SINGLE_SOURCE_AFTER_DAYS Tage alt ist (Warnung im Log).
  * Widersprechen sich die Quellen, wird nichts geschrieben und das Skript
    endet mit Fehler (GitHub schickt dann eine Mail).
  * Selbsttest: Ziehungen, die schon in der CSV stehen, müssen mit den
    gelesenen Werten übereinstimmen – sonst ist der Parser kaputt -> Fehler.

Nur Python-Standardbibliothek, keine Installation nötig.

  python scripts/update_eurojackpot.py            # aktualisieren
  python scripts/update_eurojackpot.py --dry-run  # nur anzeigen, nichts schreiben
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import re
import sys
import time
import urllib.request
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "eurojackpot.csv"
SOURCES = {
    "euro-jackpot.net": "https://www.euro-jackpot.net/de/gewinnzahlen-archiv-{year}",
    "eurojackpot-zahlen.eu": "https://www.eurojackpot-zahlen.eu/eurojackpot-zahlenarchiv.php?j={year}",
}
SINGLE_SOURCE_AFTER_DAYS = 2
USER_AGENT = "Mozilla/5.0 (compatible; ziehungsabend-updater/1.0)"

MONTHS = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5, "juni": 6,
    "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}
DATE_RE = re.compile(
    r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(\d{4})(?![\d.])"                    # 30.10.2026
    r"|(?<!\d)(\d{1,2})\.\s*(" + "|".join(MONTHS) + r")\s+(\d{4})(?!\d)",  # 30. Oktober 2026
    re.IGNORECASE,
)
# Einzelne Zahl 1–2-stellig, nicht Teil von Beträgen (10.000.000) oder Uhrzeiten (21:00)
INT_RE = re.compile(r"(?<![\d.,:])\d{1,2}(?![\d.,:])")

Draw = tuple  # (n1..n5, e1, e2)


def log(msg: str) -> None:
    print(msg, flush=True)


def warn(msg: str) -> None:
    print(f"::warning::{msg}", flush=True)


# ---------------------------------------------------------------- Regeln
def euro_max(date: dt.date) -> int:
    if date < dt.date(2014, 10, 10):
        return 8
    if date < dt.date(2022, 3, 25):
        return 10
    return 12


def is_valid(date: dt.date, draw: Draw) -> bool:
    n, e = draw[:5], draw[5:]
    weekdays = (1, 4) if date >= dt.date(2022, 3, 25) else (4,)  # Di+Fr bzw. nur Fr
    return (
        len(n) == 5 and len(e) == 2
        and len(set(n)) == 5 and all(1 <= x <= 50 for x in n)
        and len(set(e)) == 2 and all(1 <= x <= euro_max(date) for x in e)
        and date.weekday() in weekdays
    )


# ---------------------------------------------------------------- Parsing
def html_to_text(page: str) -> str:
    page = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", page)
    page = re.sub(r"(?s)<!--.*?-->", " ", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page))


def parse_archive(page: str, year: int) -> tuple[dict[str, Draw], list[str]]:
    """Findet jedes Datum und nimmt die ersten 7 Zahlen danach (bis zum nächsten Datum)."""
    text = html_to_text(page)
    matches = list(DATE_RE.finditer(text))
    draws: dict[str, Draw] = {}
    conflicted: set[str] = set()
    problems: list[str] = []
    today = dt.date.today()
    for i, m in enumerate(matches):
        try:
            if m.group(1):
                d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            else:
                d, mo, y = int(m.group(4)), MONTHS[m.group(5).lower()], int(m.group(6))
            date = dt.date(y, mo, d)
        except (ValueError, KeyError):
            continue
        if date.year != year or date > today:
            continue  # anderes Jahr oder „nächste Ziehung“-Hinweis
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        nums = [int(x) for x in INT_RE.findall(text[m.end():end])][:7]
        if len(nums) < 7:
            continue  # z. B. Datum in Fließtext ohne Zahlen
        draw = tuple(sorted(nums[:5]) + sorted(nums[5:7]))
        if not is_valid(date, draw):
            continue
        key = date.isoformat()
        if key in conflicted:
            continue
        if key in draws and draws[key] != draw:
            problems.append(f"{key}: widersprüchlich auf derselben Seite {draws[key]} / {draw} – verworfen")
            conflicted.add(key)
            del draws[key]
            continue
        draws[key] = draw
    return draws, problems


def fetch(url: str, tries: int = 3) -> str:
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT, "Accept-Language": "de-DE,de;q=0.9"})
            with urllib.request.urlopen(req, timeout=30) as r:
                charset = r.headers.get_content_charset() or "utf-8"
                return r.read().decode(charset, errors="replace")
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{url}: {last}")


# ---------------------------------------------------------------- CSV
def read_csv() -> dict[str, Draw]:
    with CSV_PATH.open(newline="") as f:
        return {r["date"]: tuple(int(r[k]) for k in ("n1", "n2", "n3", "n4", "n5", "e1", "e2"))
                for r in csv.DictReader(f)}


def append_csv(rows: list[tuple[str, Draw]]) -> None:
    with CSV_PATH.open("a", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        for date, draw in rows:
            w.writerow([date, *draw])


# ---------------------------------------------------------------- Ablauf
def collect(years: list[int]) -> tuple[dict[str, dict[str, Draw]], list[str]]:
    per_source: dict[str, dict[str, Draw]] = {}
    errors: list[str] = []
    for name, tpl in SOURCES.items():
        found: dict[str, Draw] = {}
        try:
            for y in years:
                draws, problems = parse_archive(fetch(tpl.format(year=y)), y)
                for p in problems:
                    warn(f"{name}: {p}")
                found.update(draws)
            per_source[name] = found
            log(f"{name}: {len(found)} Ziehungen gelesen"
                + (f", neueste {max(found)}" if found else ""))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {exc}")
            warn(f"Quelle nicht erreichbar – {name}: {exc}")
    return per_source, errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="nichts schreiben")
    args = ap.parse_args()

    today = dt.date.today()
    existing = read_csv()
    last = max(existing)
    years = sorted({today.year, dt.date.fromisoformat(last).year})
    log(f"CSV: {len(existing)} Ziehungen, letzte {last}. Lese Jahre {years}.")

    per_source, errors = collect(years)
    usable = {k: v for k, v in per_source.items() if v}
    if not usable:
        log("::error::Keine Quelle lieferte Daten. Seiten erreichbar? Aufbau geändert?")
        return 1

    # Selbsttest gegen bekannte Ziehungen
    failed = False
    for name, draws in usable.items():
        overlap = [d for d in draws if d in existing]
        bad = [d for d in overlap if draws[d] != existing[d]]
        log(f"{name}: Selbsttest {len(overlap) - len(bad)}/{len(overlap)} bekannte Ziehungen stimmen")
        if bad:
            log(f"::error::{name} weicht bei bekannten Ziehungen ab: {bad[:5]} – Parser prüfen")
            failed = True
        if not overlap:
            warn(f"{name}: keine Überlappung mit der CSV – Selbsttest nicht möglich")
    if failed:
        return 1

    # Neue Ziehungen zusammenführen
    candidates = sorted({d for draws in usable.values() for d in draws if d > last})
    accepted: list[tuple[str, Draw]] = []
    for date in candidates:
        values = {name: draws[date] for name, draws in usable.items() if date in draws}
        distinct = set(values.values())
        if len(distinct) > 1:
            log(f"::error::{date}: Quellen widersprechen sich: {values}")
            return 1
        draw = distinct.pop()
        if len(values) == len(SOURCES):
            accepted.append((date, draw))
            continue
        age = (today - dt.date.fromisoformat(date)).days
        if age >= SINGLE_SOURCE_AFTER_DAYS:
            warn(f"{date}: nur von {list(values)} bestätigt (seit {age} Tagen) – übernommen")
            accepted.append((date, draw))
        else:
            log(f"{date}: bisher nur in {list(values)} – warte auf zweite Quelle")
            break  # Reihenfolge wahren: keine späteren Ziehungen vor dieser eintragen

    if not accepted:
        log("Keine neuen Ziehungen.")
        return 0
    for date, draw in accepted:
        log(f"neu: {date}  {' '.join(map(str, draw[:5]))} | {draw[5]} {draw[6]}")
    if args.dry_run:
        log("--dry-run: nichts geschrieben.")
    else:
        append_csv(accepted)
        log(f"{len(accepted)} Ziehung(en) an {CSV_PATH.name} angehängt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
