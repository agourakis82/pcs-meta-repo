# Zenodo Patch Request — DOI Consolidation (Extended Memory v4.3)

Target consolidation:

- New canonical (v4.3): 10.5281/zenodo.16921952
- Previous (v4.2): 10.5281/zenodo.16682784
- Concept DOI (aggregator): 10.5281/zenodo.16533374

## Actions (via Zenodo UI)

1) Open record 10.5281/zenodo.16921952 → Edit → Related identifiers:
   - Add: relation = `IsNewVersionOf`, identifier = `10.5281/zenodo.16682784`, scheme = `doi`.
   - Add: relation = `isPartOf`, identifier = `10.5281/zenodo.16533374`, scheme = `doi`.
   - (Optional) Add `IsSupplementTo` to list module DOIs if applicable.
   - In Description: note that v4.3 unifies and supersedes v4.2.

2) Open record 10.5281/zenodo.16682784 → Edit → Related identifiers:
   - Add: relation = `IsPreviousVersionOf`, identifier = `10.5281/zenodo.16921952`, scheme = `doi`.
   - Add: relation = `isPartOf`, identifier = `10.5281/zenodo.16533374`, scheme = `doi`.
   - In Description: insert notice that v4.2 is superseded by v4.3 (link to DOI above).

## Actions (via API) — example payloads

Note: Editing published records typically requires creating a draft (new version) or unlocking the record. Use a Zenodo access token with `deposit:write`.

PATCH /api/deposit/depositions/<DEPOSITION_ID>

For v4.3 (16921952):

```
{
  "metadata": {
    "related_identifiers": [
      {"identifier": "10.5281/zenodo.16682784", "relation": "isNewVersionOf", "scheme": "doi"},
      {"identifier": "10.5281/zenodo.16533374", "relation": "isPartOf", "scheme": "doi"}
    ]
  }
}
```

For v4.2 (16682784):

```
{
  "metadata": {
    "related_identifiers": [
      {"identifier": "10.5281/zenodo.16921952", "relation": "isPreviousVersionOf", "scheme": "doi"},
      {"identifier": "10.5281/zenodo.16533374", "relation": "isPartOf", "scheme": "doi"}
    ]
  }
}
```

Please verify DEPOSITION_IDs (not the record IDs) under your account before invoking PATCH.

