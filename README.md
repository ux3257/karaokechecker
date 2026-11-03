# Ziehungsabend

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

## Eurojackpot automatisch aktualisieren

Die Workflow-Datei `.github/workflows/update-eurojackpot.yml` startet `scripts/update_eurojackpot.py`:

- **Wann:** Di und Fr um 22:40 Uhr (Winterzeit), dazu Mi und Sa morgens und nachmittags als Nachzügler.
  Manuell geht es über **Actions → „Eurojackpot-Zahlen aktualisieren“ → Run workflow**.
- **Was:** Das Skript liest die Jahresarchive von zwei unabhängigen Seiten
  ([euro-jackpot.net](https://www.euro-jackpot.net/de/gewinnzahlen-archiv-2026) und
  [eurojackpot-zahlen.eu](https://www.eurojackpot-zahlen.eu/eurojackpot-zahlenarchiv.php)) und hängt neue Ziehungen an
  `data/eurojackpot.csv` an, mit einem Commit des `github-actions[bot]`.
- **Sicherungen:**
  - Übernommen wird eine Ziehung nur, wenn beide Quellen sie identisch liefern. Kennt sie nur eine Quelle,
    wird sie erst nach 2 Tagen übernommen, mit einer Warnung im Log.
  - Widersprechen sich die Quellen, wird nichts geschrieben und der Lauf schlägt fehl.
    GitHub schickt dir dann eine Mail.
  - Selbsttest bei jedem Lauf: Die Ziehungen, die schon in der CSV stehen, müssen mit dem übereinstimmen,
    was der Parser liest. Ändert eine Seite ihren Aufbau, fällt das sofort auf.
  - Jede Ziehung wird geprüft: 5 aus 50, 2 Eurozahlen, Ziehungstag Di/Fr.
- Nur Python-Standardbibliothek, keine Pakete. Trockenlauf lokal: `python3 scripts/update_eurojackpot.py --dry-run`

**Beim ersten Mal:** Starte den Workflow einmal manuell und schau ins Log. Dort muss bei beiden Quellen
„Selbsttest x/x bekannte Ziehungen stimmen“ stehen. Bricht der Lauf beim `git push` mit „Permission denied“ ab,
setze unter **Settings → Actions → General → Workflow permissions** „Read and write permissions“.

Auf GitHub Pages lädt die App die CSV direkt aus dem Repo (`raw.githubusercontent.com/<name>/<repo>/main/…`).
So sind neue Ziehungen sichtbar, sobald die Action committet hat, egal ob die Pages-Seite schon neu gebaut ist.
Heißt dein Branch nicht `main`, passe `BRANCH` oben im Script-Teil von `index.html` an.

## Datenquellen

| Spiel | Quelle |
|---|---|
| 6aus49 | wird direkt geladen von [daowa89/lottery-archive](https://github.com/daowa89/lottery-archive) (`de/lotto_6aus49/results.csv`), dort an jedem Ziehungstag aktualisiert |
| Eurojackpot | `data/eurojackpot.csv` in diesem Repo: 23.03.2012 – 01.11.2024 aus dem npm-Paket `tsch-ej-numbers` (ISC-Lizenz), ab 05.11.2024 aus den beiden oben genannten Archiven (jede Ziehung in beiden Quellen identisch) |

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
