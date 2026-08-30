# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Windows-only Rainmeter skin backed by a Python script that polls the Deye solar inverter cloud API and renders inverter status on the desktop (grid/battery power, SOC, temperatures, power source).

The Python side is not a long-running service. It is a one-shot CLI that authenticates, fetches the latest device snapshot, prints `key: value` lines to stdout, and exits. Rainmeter invokes it on a timer, captures stdout into a text file, and a `WebParser` regex extracts the fields back out.

## Run / develop

```powershell
# Run a single fetch (uses .venv pinned by Rainmeter and #launch.bat)
.venv\Scripts\python.exe main.py

# How Rainmeter invokes it (see rainmeter_plugin/DeyeStatusEng.ini, MeasureRunPython)
#   <app_path>\.venv\Scripts\python.exe <app_path>\main.py
# stdout is redirected to #DataFile# (currently t:/deye_status.txt)

# #launch.bat does the same by hand, writing to ./out.txt instead
```

There is no test suite, linter, or build step.

`config_local.ini` (gitignored) holds `BASE_URL`, `EMAIL`, `PASSW`, `APP_ID`, `APP_SECRET`. The password is SHA-256 hashed in `main.py` before being passed to `ApiClient`; the ini stores it in plaintext.

## Architecture

**Three layers, one direction of data flow:**

1. **`handlers/ApiClient.py`** — thin requests wrapper around the Deye Cloud API (`/account/token`, `/device/latest`). Caches the bearer token to `token.json` keyed by email so subsequent runs skip the login round-trip. On a `auth invalid token` response from `/device/latest`, it forces a re-login and retries once. On HTTP 500 it sleeps 5s and retries once.
2. **`worker.py` (`Worker.work`)** — calls `auth()` then `get_device_info(station=...)`, picks a fixed subset of keys out of `deviceDataList[0].dataList` (`TotalGridPower`, `SOC`, `DC Temperature`, `AC Temperature`, `Temperature- Battery`, `InverterOutputPowerL1L2`), and synthesizes a `Source` field: `BATTERY` if `TotalGridPower == 0`, else `Grid` (and the inverter output is zeroed out in the Grid branch — only one of the two power readings is reported as non-zero at a time). Station ID is currently hardcoded as the default arg `'2508271645'`.
3. **`main.py`** — entry point. Sets up a `RotatingFileHandler` to `app.log` (100KB × 10), constructs `ApiClient` + `Worker`, and prints each result item as `key: value` to stdout. For dict-valued items it prints `value_str` (the unit-formatted form, with `℃` normalized to `°C`).

**`app_init.py` + `handlers/Configs.py`** load `config_local.ini` against a default-config dict; only keys present in the defaults are read, and boolean defaults trigger `getboolean` parsing.

**`rainmeter_plugin/DeyeStatusEng.ini`** is the Rainmeter skin (English labels; it is the only skin file — the Russian `DeyeStatus2.ini` was retired, see `git log`):
- `MeasureRunInterval` fires `MeasureRunPython` every 180 update ticks (~6 min at Update=2000ms).
- `MeasureRunPython` (RunCommand plugin) runs `main.py`, captures stdout to `#DataFile#`, then triggers `MeasureFile`.
- `MeasureFile` is a `WebParser` reading the file with a single multi-group regex — **the order and exact key names in `main.py`'s output must match the regex in `DeyeStatusEng.ini` line-for-line**. Changing the param list in `Worker.work` requires updating both the regex and the per-field `MeasureXxx` `StringIndex` numbers.
- `MeasureSource` flips the power-source indicator image (`@Resources/bullet_red.png` / `bullet_green.png`) and the `refreshButtonColor` variable based on whether the `Source` field matches `BATTERY`. It is deliberately written as `IfMatch=(?i)BATTERY` + `IfNotMatchAction=<green>`, so anything else — including an empty value mid-update — falls back to green rather than flashing red.
- **Encoding round-trip:** `MeasureRunPython` captures stdout as `OutputType=ANSI` and `MeasureFile` reads it back with `CodePage=1251`. That pairing is what makes `°C` survive; changing one without the other garbles the temperature units (`rainmeter_plugin/out.txt` is such a capture, and looks mojibake'd when viewed as UTF-8).
- **`Timeout=5000` on `MeasureRunPython`** while `ApiClient` uses `timeout=10` per request and sleeps 5s between retries — a slow or retrying API call can outlive Rainmeter's patience and yield a truncated/empty `#DataFile#`.

## Things to know before editing

- **Output contract is positional.** `main.py` iterates a Python dict; insertion order in `Worker.work`'s `result` dict drives the line order in stdout, which drives the regex group indices in `DeyeStatusEng.ini`. Reorder with care.
- **`DeyeStatusEng.ini` is UTF-16 LE with BOM (`FF FE`).** Read/write byte-aware — naïve text edits as UTF-8 will corrupt it. In PowerShell use `[System.IO.File]::ReadAllText($p, [System.Text.Encoding]::Unicode)` and `WriteAllText` with the same encoding to preserve the BOM.
- **Hardcoded paths in the skin.** `app_path` and `DataFile` are absolute paths in `DeyeStatusEng.ini` (`D:\projects\python\DeyeApi_rainmeter`, `T:\deye_status.txt`). The skin also assumes `.venv\Scripts\python.exe` exists at that path.
- **Token cache invalidation is implicit.** Deleting `token.json` forces re-login on the next run; this is the recovery path when auth state goes weird.
- **`demo/`** (screenshot + sample output) and `rainmeter_plugin/out.txt` are reference material, not active code. `app.log.*` are rotated log files. The `old/` directory referenced in earlier commits no longer exists.
- **No retries beyond the two specific cases** in `ApiClient.get_device_info` (HTTP 500 once, invalid-token once). Network failures bubble up to `main.py`'s top-level `except` and are logged but produce no stdout — which means Rainmeter sees stale data from the previous successful run.
- **`README.md` is the user-facing counterpart to this file** and documents the same output contract, setup steps and gotchas. Changes to the field list, the skin filename, or the project layout need to land in both.