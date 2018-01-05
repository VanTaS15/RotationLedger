"""rotationledger: track the lifetime of leaked secrets through git history.

rotationledger reads a committed ``git log -p`` export offline, detects
credential-shaped strings with Shannon entropy plus named rules, then
reconstructs each secret's lifetime: where it was introduced, how many days it
stayed exposed, where it was removed or rotated, and whether it is still present
