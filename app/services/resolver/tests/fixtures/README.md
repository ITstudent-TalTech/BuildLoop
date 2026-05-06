# In-ADS Response Fixtures

These JSON files simulate In-ADS gazetteer API responses for the resolver
test suite. Each file exercises a specific code path.

## Files

| File | Status | Description |
|------|--------|-------------|
| `lai_1_resolved.json` | **constructed** | Clean single-match response for "Lai 1, Tallinn". One EHR code (101035685), full `taisaadress`, scores ≥ 0.85 → auto-resolved. |
| `lai_1_corner.json` | **constructed** | Corner-address response for "Lai 1, Tallinn". EHR 101035685 returned with a `//` composite address ("Lai tn 1 // Nunne tn 4"). Tests Rule 2 (doc 03) alias extraction. |
| `pelguranna_ambiguous.json` | **constructed** | Two candidates for "Pelguranna, Tallinn" with no house number in the input. Both score ≈ 0.58 (∈ [0.50, 0.85)) → ambiguous. |
| `gibberish_unresolved.json` | **constructed** | Empty `addresses` list for an unrecognisable query. Zero candidates → unresolved with reason `no_extractable_ehr_code_found`. |

## Status key

- **captured** — raw response from a real In-ADS API call (with `RESOLVER_DEBUG_DUMP_INADS=1`).
- **constructed** — hand-authored to match the shape the resolver code expects,
  verified against the walker and scoring logic in the test suite.

## Capturing real responses

To replace any constructed fixture with a live capture, set the environment
variable `RESOLVER_DEBUG_DUMP_INADS=1` before running
`buildloop_passport_from_address.py` with the matching address. The file
`artifacts/resolver_inads_raw.json` will contain the raw response body.
