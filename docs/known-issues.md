# Known issues

**Gate layout.** When you reopen a gate made from a circuit, operations that shared a column appear in separate columns. The gate still gives the same result.

## Retired issues

The old shared `data/custom_gates.json` file could lose changes when two windows saved at once. Invalid UTF-8 in that file could also block saves. The app now stores custom gates in circuit files or individual gate files.
