# Sample fixtures

## history.gitlog

This is a hand authored test vector, not production data. It imitates the output
of:

```
git log -p --date=iso
```

for a small imaginary service repository. It was written by hand so the
credential lifetimes are known exactly and can be asserted in the tests. Git was
not run to produce it.

Every credential in the file is synthetic and obviously invalid. None of these
values authenticate against any real system:

- `AKIAEXAMPLE00000FAKE` is an AWS access key id shape that carries the literal
  words EXAMPLE and FAKE. Real AWS key ids are 20 characters of uppercase and
  digits after the AKIA prefix and never spell words.
- `Bearer EXAMPLEfakeTOKENzzz0000abcd1234EXAMPLE` is a placeholder bearer token
