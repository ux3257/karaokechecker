# Karaokechecker

Lottozahlen nacheinander aufdecken und mitfiebern – für **Lotto 6aus49** und **Eurojackpot**.

- Ziehung über Jahr und Datum auswählen (die neueste ist vorausgewählt)
- Bis zu 5 Tipps pro Spiel, bei 6aus49 zusätzlich die Superzahl (letzte Ziffer der Losnummer)
- Die Kugeln werden einzeln gezogen, Treffer leuchten sofort grün
- Am Ende steht die Gewinnklasse je Tipp
- Tipps werden automatisch im Browser gespeichert (localStorage, nur auf dem jeweiligen Gerät)
- Fehlende Ziehungen lassen sich selbst nachtragen (ebenfalls nur lokal)

Die App ist eine einzige statische HTML-Seite ohne Server und ohne Abhängigkeiten.

## Auf GitHub Pages veröffentlichen

1. Neues Repository anlegen und den **gesamten** Inhalt dieses Ordners hochladen, also auch den
   versteckten Ordner `.github/`. Am einfachsten geht das per `git push`. Beim Hochladen im Browser
   werden versteckte Ordner leicht vergessen.
2. **Settings → Pages**: Source „Deploy from a branch“, Branch `main`, Ordner `/ (root)`.
3. Nach ca. einer Minute läuft die App unter `https://<dein-name>.github.io/<repo>/`.

Lokal testen: `python3 -m http.server` im Ordner starten und `http://localhost:8000` öffnen.
Ein Doppelklick auf `index.html` reicht nicht, weil der Browser dann keine Daten laden darf.

## Auf dem Handy installieren

Die App ist eine installierbare Web-App (PWA): `manifest.webmanifest`, `sw.js` und `icons/`.

- **Android (Chrome):** Seite öffnen → Menü ⋮ → **App installieren** (oder „Zum Startbildschirm hinzufügen“).
- **iPhone (Safari):** Teilen-Symbol → **Zum Home-Bildschirm**.

Danach startet sie mit eigenem Icon ohne Browserleiste. Offline zeigt sie die zuletzt geladenen Ziehungen.
Neue Versionen von `index.html` lädt sie im Hintergrund und zeigt sie beim nächsten Öffnen.
Ändert sich etwas Grundlegendes, `VERSION` in `sw.js` hochzählen.

## Eurojackpot automatisch aktualisieren

Die Workflow-Datei `.github/workflows/update-eurojackpot.yml` startet `scripts/update_eurojackpot.py`:

- **Wann:** Di und Fr abends alle 20 Minuten, Mi und Sa nachts bis morgens alle 30 Minuten, dazu einmal täglich.
  GitHub startet geplante Läufe oft verspätet oder lässt einzelne aus, deshalb die vielen Versuche.
  Ist die CSV schon aktuell, beendet sich der Lauf nach Sekunden, ohne eine Seite abzurufen.
  Manuell geht es über **Actions → „Eurojackpot-Zahlen aktualisieren“ → Run workflow**. Das prüft immer alle Quellen.
- **Was:** Das Skript liest die Jahresarchive von drei unabhängigen Seiten:
  [euro-jackpot.net](https://www.euro-jackpot.net/de/gewinnzahlen-archiv-2026),
  [eurojackpot-zahlen.eu](https://www.eurojackpot-zahlen.eu/eurojackpot-zahlenarchiv.php) und
  [lotterien1x1.de](https://www.lotterien1x1.de/eurojackpot/archiv/2026).
  Neue Ziehungen hängt es an `data/eurojackpot.csv` an.
- **Sicherungen:**
  - Übernommen wird eine Ziehung, sobald zwei Quellen sie identisch liefern. Fällt eine Quelle aus, reichen die anderen beiden.
    Weicht eine dritte ab, gilt die Mehrheit, mit einer Warnung im Log.
  - Kennt nur eine Quelle die Ziehung, wird sie erst nach 2 Tagen übernommen, ebenfalls mit Warnung.
  - Gibt es keine Mehrheit, wird nichts geschrieben und der Lauf schlägt fehl. GitHub schickt dann eine Mail.
  - Selbsttest bei jedem Abruf: Die Ziehungen, die schon in der CSV stehen, müssen mit dem übereinstimmen, was gelesen wurde.
  - Jede Ziehung wird geprüft: 5 aus 50, 2 Eurozahlen, Ziehungstag Di/Fr.
- **Zusammenfassung:** Auf der Seite jedes Laufs steht eine Tabelle mit allen Quellen (erreichbar oder Fehler, neueste Ziehung)
  und was übernommen wurde. Dafür muss man das Log nicht öffnen.
- Nur Python-Standardbibliothek. Trockenlauf lokal: `python3 scripts/update_eurojackpot.py --dry-run --force`

Bricht ein Lauf beim `git push` mit „Permission denied“ ab, setze unter
**Settings → Actions → General → Workflow permissions** „Read and write permissions“.

Auf GitHub Pages lädt die App die CSV direkt aus dem Repo (`raw.githubusercontent.com/<name>/<repo>/main/…`).
So sind neue Ziehungen sichtbar, sobald die Action committet hat.
Heißt dein Branch nicht `main`, passe `BRANCH` oben im Script-Teil von `index.html` an.

## Datenquellen

| Spiel | Quelle |
|---|---|
| 6aus49 | wird direkt geladen von [daowa89/lottery-archive](https://github.com/daowa89/lottery-archive) (`de/lotto_6aus49/results.csv`), dort an jedem Ziehungstag aktualisiert |
| Eurojackpot | `data/eurojackpot.csv` in diesem Repo: 23.03.2012 – 01.11.2024 aus dem npm-Paket `tsch-ej-numbers` (ISC-Lizenz), ab 05.11.2024 aus den oben genannten Archiven (jede Ziehung von mindestens zwei Quellen bestätigt) |

Format `data/eurojackpot.csv`:

```
date,n1,n2,n3,n4,n5,e1,e2
2026-10-30,21,26,37,39,42,5,7
```

## Regeln, die die App abbildet

- **6aus49:** Gewinnklassen 1–9 nach den Regeln seit Mai 2013. Ältere Ziehungen werden nach diesen Regeln bewertet, darauf weist die App hin.
  Superzahl erst ab 1992.
- **Eurojackpot:** 12 Gewinnklassen. Bis 24.03.2022 war Klasse 6 = 4+0 und Klasse 7 = 3+2, seitdem umgekehrt. Beides ist berücksichtigt.
  Eurozahlen waren 2 aus 8 (bis Okt. 2014), dann 2 aus 10, seit März 2022 2 aus 12. Tipps werden immer mit 1–12 erfasst.
- Die Archive speichern die Zahlen sortiert, deshalb ist die Reihenfolge beim Aufdecken zufällig.

Alle Angaben ohne Gewähr.
