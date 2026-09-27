---
name: wiki-analyser
description: Extract analytics data from Wikipedia, analyse interest rate of article, create plots and export summary data in PDF files.
---

# Wiki analyser

## Fetching page view data

Use `scripts/wiki_cli.py` (Python 3.11+, standard library only, no install needed). It prints JSON to stdout.
On an API error it prints `{"error", "status", "url"}` to stderr and exits with 1. Invalid arguments exit with 2.

```bash
python3 scripts/wiki_cli.py <command> [options]
python3 scripts/wiki_cli.py <command> --help
```

| Command | What it returns |
|---|---|
| `article TITLE --start D --end D` | views of one article over time |
| `views --start D --end D` | total views of a project over time |
| `countries --month YYYY-MM` | countries ranked by views of a project |
| `top --date D` / `top --month YYYY-MM` | top 1000 articles of a project for a day or a month |
| `top-country CC --date D` | top articles across all projects in a country (ISO code, e.g. `DE`) |
| `editor-views USER_ID --start D --end D` | views of pages edited by a user (central user id) |
| `editor-top USER_ID --start D --end D` | top pages edited by a user, per month |

Dates `D` are `YYYY-MM-DD`, ranges are inclusive. Data is available from 2015-07-01.

Common options:
- `--project` defaults to `en.wikipedia.org`. Use the language subdomain for other wikis (`ru.wikipedia.org`), or `all-projects` for `views` and `countries`.
- `--access`: `all-access` (default), `desktop`, `mobile-app`, `mobile-web`.
- `--agent`: `user` (default, humans only), `all-agents`, `spider`, `automated`.
- `--granularity`: `daily` (default), `monthly`, `hourly`.
- `--limit N` goes **before** the command and truncates the list: `python3 scripts/wiki_cli.py --limit 20 top --date 2025-08-01`. Always use it for `top` and `top-country`, which return up to 1000 items.

Examples:

```bash
python3 scripts/wiki_cli.py article "Albert Einstein" --granularity monthly --start 2025-01-01 --end 2025-08-31
python3 scripts/wiki_cli.py article "Москва" --project ru.wikipedia.org --start 2025-09-01 --end 2025-09-07
python3 scripts/wiki_cli.py --limit 10 top --month 2025-08
```

Gotchas:
- Article titles are case-sensitive and must match the exact page title; spaces are fine. Resolve redirects yourself: views of a redirect are not counted in its target.
- A 404 means either a wrong title or no data for the dates; the API does not distinguish them. Check the title before retrying with other dates.
- `countries` and `top-country` give rounded numbers: use `views_ceil`, not the `views` range string.
- `top` includes service pages such as `Main_Page` and `Special:Search`; filter them out when analysing interest in articles.
- Recent data appears with a delay of about one day.

## Plotting

Pick the chart from the data, then hand off rendering by output format:
- In chat: draw the chart inline, no file.
- Excel: follow the xlsx skill (native charts).
- Slides: follow the pptx skill.
- PDF report: draw PNGs with matplotlib, then follow the pdf skill to lay them out.

Chart conventions:
- `article`/`views` over time → line chart, x = `timestamp` (YYYYMMDDHH), y = `views`.
- Comparing articles → one line per article on a shared axis; use log scale if one dwarfs the rest.
- `top`/`top-country` → horizontal bar, top 10–20, service pages removed.
- `countries` → bar of `views_ceil`, noting in the caption that values are rounded.
- Always state project, access, agent and date range in the title or caption.