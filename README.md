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
