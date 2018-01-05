"""rotationledger: track the lifetime of leaked secrets through git history.

rotationledger reads a committed ``git log -p`` export offline, detects
