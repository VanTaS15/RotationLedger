"""Line-oriented, deterministic reports.

Every function here returns a list of text lines with no trailing whitespace so
output diffs cleanly in git. No wall-clock time is read; all dates come from the
parsed commits.
"""

