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

Rules are tried in a fixed order. The four structural rules are checked first;
the generic high-entropy rule only fires on a captured region that no
structural rule already claimed, which avoids double counting one value.

| Rule                   | What it matches                                              | Confidence                                  |
|------------------------|-------------------------------------------------------------|---------------------------------------------|
| `aws-access-key`       | `AKIA` or `ASIA` then 16 uppercase or digit characters      | High: the shape is specific to AWS keys     |
| `private-key-header`   | a PEM `BEGIN ... PRIVATE KEY` header line                   | High: the header is unambiguous             |
| `bearer-token`         | a `Bearer` value of 20+ URL-safe base64 characters          | High: structural, though value is opaque    |
| `connection-string`    | a password inside a `postgres/mysql/mongodb/redis/amqp` URL | High: password position in the URL is fixed |
| `generic-high-entropy` | a secret/token/api-key/password assignment, 20+ chars       | Heuristic: entropy and length gated only    |

The structural rules are high confidence because they match a shape that is
specific to a kind of credential, not just to "long random string". The generic
rule is a heuristic and is described honestly in the next section.

## Entropy scoring and its false positives

The `generic-high-entropy` rule fires only when a value assigned to a
secret-like name is at least 20 characters, mixes at least two character classes
(lower, upper, digit, symbol), and has Shannon entropy of at least 3.5 bits per
character. The thresholds live as named constants in `detect.py`
(`GENERIC_MIN_LEN`, `GENERIC_MIN_ENTROPY`) so a reader can reproduce any generic
finding by hand.

This rule is a heuristic, and heuristics are wrong in both directions:

- False negatives. A genuinely secret value that happens to be short or
  low-entropy will not trip the gate. A 16-character password made of dictionary
  words can sit below 3.5 bits per character and be missed.
- False positives. A long, mixed, high-entropy string that is assigned to a
  secret-like name but is not actually a credential (a hash, a UUID list, a
  base64 blob of test data) will be flagged. The rule cannot tell a real API key
  from a random-looking constant; it only measures shape.

Entropy is a proxy for randomness, not a proof of secrecy. Treat generic
findings as candidates to review, and tune the two thresholds in `detect.py` to
your codebase rather than assuming the defaults are correct for your data.

## Why fingerprints and not values

rotationledger never stores or prints a raw secret value. Every finding is keyed
to a fingerprint, which is a truncated SHA-256 of the matched bytes: the full
digest computed with `hashlib.sha256`, hex-encoded, then cut to the first 12
characters (`_fingerprint` in `detect.py`).

That choice does two things. It gives each logical secret a stable identity, so
the same value added in one commit and deleted in another is recognised as one
credential rather than two unrelated hits, which is what makes lifetime tracking
possible at all. And it means the tool's output, its logs, and its reports can
be committed, shared, or pasted into a ticket without leaking the secret they
describe. The fingerprint identifies the secret without being the secret. A test
(`test_fingerprint_never_contains_secret`) asserts the secret string never
appears inside its own fingerprint.

The truncation to 12 hex characters (48 bits) is a readability tradeoff. It is
short enough to scan by eye in a report and long enough that an accidental
collision between two different secrets in one export is very unlikely. It is not
a security boundary: a fingerprint is a label, not a commitment scheme.

## Output format

Every report is a list of text lines with no trailing whitespace, so runs diff
cleanly in git. No wall-clock time is ever read; all dates come from the parsed
commits, which keeps output deterministic.

`scan` prints one line per finding per commit that adds it:

```
python -m rotationledger scan samples/history.gitlog
```

```
3e2f1a0b9c 2026-01-05 aws-access-key 5dacc6454799 config.py len=20 entropy=3.00
3e2f1a0b9c 2026-01-05 bearer-token 63c44ec215be services/client.py len=38 entropy=4.29
5c4d3e2f1a 2026-02-14 generic-high-entropy a99fa712c31c settings.py len=51 entropy=4.76
```

| Field       | Example                | Meaning                                    |
|-------------|------------------------|--------------------------------------------|
| short sha   | `3e2f1a0b9c`           | first 10 chars of the commit that added it |
| date        | `2026-01-05`           | commit date, `YYYY-MM-DD`                  |
| rule        | `aws-access-key`       | which detection rule matched               |
| fingerprint | `5dacc6454799`         | 12-char truncated SHA-256 of the value     |
| path        | `config.py`            | file the added line touched                |
| `len=`      | `len=20`               | length of the matched value in characters  |
| `entropy=`  | `entropy=3.00`         | Shannon entropy, bits/char, two decimals   |

`lifetime` prints one line per tracked credential:

```
python -m rotationledger lifetime samples/history.gitlog
```

```
5dacc6454799 aws-access-key introduced=3e2f1a0b9c@2026-01-05 removed=7a2b9c8d1e@2026-03-20 state=rotated exposure_days=74
63c44ec215be bearer-token introduced=3e2f1a0b9c@2026-01-05 removed=9f3c1a7d24@2026-04-02 state=rotated exposure_days=87
a99fa712c31c generic-high-entropy introduced=5c4d3e2f1a@2026-02-14 removed=-@- state=live exposure_days=47
```

| Field            | Meaning                                                     |
|------------------|-------------------------------------------------------------|
| fingerprint      | the secret's stable identity                                |
| rule             | the rule that first matched it                              |
| `introduced=`    | `sha@date` of the commit that first added the value         |
| `removed=`       | `sha@date` of the removal, or `-@-` when still live         |
| `state=`         | `live` or `rotated`                                         |
| `exposure_days=` | whole days the value was live (see the lower-bound note)    |

`report` is the headline: exposure days, worst window first, with a summary
footer.

```
python -m rotationledger report samples/history.gitlog
```

```
EXPOSURE DAYS REPORT

  87d  bearer-token           63c44ec215be rotated
  74d  aws-access-key         5dacc6454799 rotated
  47d  generic-high-entropy   a99fa712c31c live (open, measured to newest commit)

total=3 live=1 rotated=2 exposure_days_sum=208
```

The footer counts total findings, splits them into live and rotated, and sums
the exposure days across all findings. The `(open, measured to newest commit)`
annotation marks any window that is a lower bound rather than a closed measure.

## Exit codes

The exit code lets you gate a pipeline on findings without parsing the text.

| Code | Meaning                                             |
|------|-----------------------------------------------------|
| 0    | ran cleanly and found nothing (`version` also exits 0) |
| 1    | ran cleanly and findings are present                |
| 2    | usage error or the input file could not be read     |

Verified in this session:

```
report samples/history.gitlog  -> 1   (findings present)
scan   samples/history.gitlog  -> 1   (findings present)
version                        -> 0
report nope.gitlog             -> 2   (file not found)
```

In CI, a non-zero exit from `report` fails the job. To gate specifically on new
exposure between two revisions, run `report` against a `git log -p` export of
each and diff the two outputs; because the output is sorted and deterministic,
the diff is stable.

## The sample history

`samples/history.gitlog` is a hand-authored test vector, not production data. It
imitates the output of `git log -p --date=iso` for a small imaginary service
repository. It was written by hand so the credential lifetimes are known exactly
and can be asserted in the tests; git was not run to produce it.

Every credential in the file is synthetic and obviously invalid. None of these
values authenticate against anything, and each spells out placeholder words so a
reader is never confused about whether it is real:

- `AKIAEXAMPLE00000FAKE` is an AWS access key id shape carrying the literal
  words EXAMPLE and FAKE.
- `Bearer EXAMPLEfakeTOKENzzz0000abcd1234EXAMPLE` is a placeholder bearer token.
- `sk-live-EXAMPLE9d4f7b2a6c8e1f3a5b7d9e0c2f4a6b8dFAKE` uses the common
  `sk-live-` prefix but is padded with the words EXAMPLE and FAKE.

The export holds four commits, printed newest first as git does. The initial
commit plants the AWS key and bearer token; a later commit rotates the AWS key;
a later commit removes the bearer token; and one commit adds a generic analytics
key that is never removed, so it stays live. That is one live and two rotated
findings, matching the report above. See `samples/README.md` for the full
timeline table.

## Limitations

Things this tool does not do, stated plainly:

- It does not run git. It parses a `git log -p` text export you provide. If a
  secret existed only in a commit that is not in the export, it is invisible.
- Exposure days for a still-live secret are measured against the newest commit
  in the export, because the tool is offline and has no later reference point.
  It is a lower bound, labelled `open` in the report, not the days since today.
- Detection is line oriented. A multi-line PEM key body is recognised only by
  its BEGIN header line, and a secret split across diff lines is not
  reassembled.
- The generic high-entropy rule is a heuristic. It will miss a low-entropy
  secret and can flag a long random-looking value that is not actually a
  credential. Tune the thresholds in `detect.py` for your data.
- Fingerprints match exact byte-identical values. A secret that is reformatted,
  re-encoded, or re-cased between commits reads as two different secrets.
- There is no binary or large-file handling; the input is expected to be a text
  diff export.

## Design decisions

The choices below are the ones a reader is most likely to question, with the
alternative that was rejected.

Parse an offline `git log -p` export instead of invoking git. The obvious
alternative is to shell out to git (or use a git library) and walk history
directly. That was rejected for three reasons. It removes a dependency on git
being installed and on the analysed repository being present, so the tool can
