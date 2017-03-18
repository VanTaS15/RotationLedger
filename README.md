<img align="right" width="190" src="docs/assets/logo.svg" alt="rotationledger wordmark with a single lifetime segment running from an amber introduce point on the left to a teal rotate point on the right">

# rotationledger

Track the lifetime of leaked secrets through git history, and report how long
each one stayed exposed.

rotationledger reads a committed `git log -p` export, offline, with no call to
git at run time. It detects credential-shaped strings using Shannon entropy
plus named rules, then reconstructs each secret's lifetime: the commit that
introduced it, the exposure window in days, the commit that removed or rotated
it, and whether it is still present at HEAD.

The headline output is an exposure-days report, not a raw hit list. A scanner
that only counts secrets treats a value you rotated three months ago and a
value that is still live in your tree as the same finding. They are not the
same finding, and this tool is built around that distinction: a rotated secret
is a closed incident with a known window, a live secret is an open one.

<br clear="all">

## The question this answers

Most secret scanners answer "does a secret exist in this file". That is the
wrong question once a secret has already been committed. By the time you run a
scan, the interesting facts are historical: when did this value first enter the
repository, how many days did it sit there readable to anyone with clone
access, and did anyone ever actually remove it.

rotationledger reframes the finding around exposure duration. Every detected
credential is keyed to a fingerprint and followed across the whole commit
range. The output separates two populations that a count-based scanner blends
together:

- Rotated secrets: introduced at one commit, removed at a later commit. These
  have a closed exposure window measured in days. The window is what tells you
  how large the incident was.
- Live secrets: introduced and never removed within the analysed history.
  These are open incidents. Their window is a lower bound, measured to the
  newest commit in the export, because the tool has no reference point later
  than the data you gave it.

If you only remember one thing about the output, remember that a live finding
and a rotated finding demand different actions. A live finding means rotate the
credential now. A rotated finding means confirm the window, and treat anything
that was exposed for weeks as compromised regardless of the later rotation.

## Install

No third-party dependencies. Python 3.11 or newer, standard library only.

```
pip install -e .
```

Or run straight from the source tree without installing:

```
set PYTHONPATH=src
python -m rotationledger report samples/history.gitlog
```

## Commands

Four subcommands. Each reads a `git log -p` export path, except `version`.

| Command    | Argument  | What it prints                                          |
|------------|-----------|---------------------------------------------------------|
| `scan`     | `logfile` | Every credential-shaped finding, one line per hit       |
| `lifetime` | `logfile` | Introduce, rotate, and still-live state per secret      |
| `report`   | `logfile` | The exposure-days report, worst window first (headline) |
| `version`  | none      | The package version string                              |

```
rotationledger scan     <logfile>
rotationledger lifetime <logfile>
rotationledger report   <logfile>
rotationledger version
```

## The lifetime state machine

Each distinct credential fingerprint moves through a small state machine as the
walk proceeds oldest commit to newest. There are three observable states:
`absent` (never seen, the starting point), `live` (added and not yet removed),
and `rotated` (added and later removed). The report calls a still-open window
`live` and a closed window `rotated`.

| From state | Event in a commit                     | To state  | Recorded                          |
|------------|---------------------------------------|-----------|-----------------------------------|
| absent     | fingerprint appears in added lines    | live      | `introduced_sha`, `introduced_at` |
| live       | same fingerprint appears in del lines | rotated   | `removed_sha`, `removed_at`       |
| live       | end of history reached, still present | live      | window measured to newest commit  |
| rotated    | fingerprint added again later         | live      | a new, separate lifetime opens    |

Two details are worth stating because they change the numbers:

- Within a single commit, a line that is edited shows up as both a deletion and
  an addition. If a fingerprint appears in both the added and removed sets of
  the same commit, it is treated as still present, not rotated. Only a deletion
  with no matching addition closes the window (`lifetime.py`, the removal loop
  guards on `fp not in added`).
- A value that is removed and later re-added is modelled as two separate
  lifetimes rather than one merged span, so a rotation that reuses the same
  value is never silently collapsed into a single window.

## A worked example

Follow one real secret from the sample export to its exposure number. Take the
bearer token planted in `services/client.py`.

In the initial commit (`3e2f1a0b`, dated 2026-01-05) the sample adds this line:

```
+        self.auth_header = "Bearer EXAMPLEfakeTOKENzzz0000abcd1234EXAMPLE"
```

The `bearer-token` rule matches the value after `Bearer`, and it is fingerprinted
to `63c44ec215be`. The state machine moves this fingerprint from `absent` to
`live`, recording `introduced_at = 2026-01-05`.

Nothing touches that line until commit `9f3c1a7d`, dated 2026-04-02, which
removes it:

```
-        self.auth_header = "Bearer EXAMPLEfakeTOKENzzz0000abcd1234EXAMPLE"
+        self.auth_header = "Bearer " + os.environ["SERVICE_TOKEN"]
```

The old value appears in the removed set and not in the added set of that
commit, so the window closes: state becomes `rotated`, `removed_at =
2026-04-02`. The exposure is the whole-day delta between the two dates, from
2026-01-05 to 2026-04-02, which is 87 days. That is exactly what `lifetime`
prints for `63c44ec215be`, and what lands at the top of the report:

```
5dacc6454799 aws-access-key introduced=3e2f1a0b9c@2026-01-05 removed=7a2b9c8d1e@2026-03-20 state=rotated exposure_days=74
63c44ec215be bearer-token introduced=3e2f1a0b9c@2026-01-05 removed=9f3c1a7d24@2026-04-02 state=rotated exposure_days=87
a99fa712c31c generic-high-entropy introduced=5c4d3e2f1a@2026-02-14 removed=-@- state=live exposure_days=47
```

## Detection rules

