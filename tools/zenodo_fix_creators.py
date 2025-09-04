#!/usr/bin/env python3
import os, sys, json, urllib.request, urllib.error

BASE = 'https://zenodo.org/api'

TOKEN = os.environ.get('ZENODO_TOKEN')
if not TOKEN:
    print('[zenodo-fix] ERROR: ZENODO_TOKEN not set in environment', file=sys.stderr)
    sys.exit(1)

TITLE_HINT = os.environ.get('ZENODO_TITLE_HINT', 'Symbolic Manifolds v4.3.2')

def req(method, path, data=None):
    url = BASE + path
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
    }
    body = None
    if data is not None:
        body = json.dumps(data).encode('utf-8')
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.getcode(), json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            payload = e.read().decode('utf-8')
            return e.code, json.loads(payload)
        except Exception:
            return e.code, {'error': str(e)}

def upload_to_bucket(bucket_url, filepath):
    # bucket_url like https://zenodo.org/api/files/<bucket-id>
    name = os.path.basename(filepath)
    url = bucket_url.rstrip('/') + '/' + name
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/octet-stream',
    }
    with open(filepath, 'rb') as f:
        data = f.read()
    r = urllib.request.Request(url, data=data, headers=headers, method='PUT')
    with urllib.request.urlopen(r, timeout=300) as resp:
        return resp.getcode(), json.loads(resp.read().decode('utf-8'))

def list_depositions():
    code, data = req('GET', '/deposit/depositions?size=200')
    if code != 200:
        raise RuntimeError(f'list_depositions failed: {code} {data}')
    return data

def find_candidate(depositions):
    # prefer drafts/unsubmitted first
    drafts, published = [], []
    for dep in depositions:
        md = dep.get('metadata') or {}
        title = md.get('title', '')
        if TITLE_HINT.lower() in title.lower() or 'Symbolic Manifolds' in title:
            if dep.get('state') != 'done' and not dep.get('submitted', False):
                drafts.append(dep)
            else:
                published.append(dep)
    drafts.sort(key=lambda d: d.get('created', ''), reverse=True)
    published.sort(key=lambda d: d.get('created', ''), reverse=True)
    return (drafts[0] if drafts else (published[0] if published else None))

def ensure_related_identifiers(md):
    ril = md.get('related_identifiers') or []
    concept = {'identifier': '10.5281/zenodo.16533374', 'relation': 'isVersionOf', 'scheme': 'doi'}
    if not any(x.get('identifier') == concept['identifier'] and x.get('relation') == concept['relation'] for x in ril):
        ril.append(concept)
    md['related_identifiers'] = ril

def main():
    deps = list_depositions()
    cand = find_candidate(deps)
    if not cand:
        print('[zenodo-fix] No matching deposition found. Is the GitHub→Zenodo draft created?')
        sys.exit(2)
    dep_id = cand.get('id')
    state = cand.get('state')
    links = cand.get('links', {})
    print(f"[zenodo-fix] Found deposition id={dep_id} state={state}")

    # Load full deposition to get metadata
    code, detail = req('GET', f'/deposit/depositions/{dep_id}')
    if code != 200:
        print(f"[zenodo-fix] ERROR fetching deposition: {code} {detail}")
        sys.exit(3)
    md = detail.get('metadata') or {}

    # Prepare creators with valid ORCID format
    creators = [
        {
            'person_or_org': {
                'type': 'personal',
                'given_name': 'Demetrios C.',
                'family_name': 'Agourakis',
                'identifiers': [
                    {'scheme': 'orcid', 'identifier': '0000-0002-8596-5097'}
                ]
            }
        },
        {
            'person_or_org': {
                'type': 'personal',
                'given_name': 'Dionisio Chiuratto',
                'family_name': 'Agourakis'
            }
        }
    ]

    # Build minimal patch to avoid tripping on unrelated invalid fields
    patch_md = {'creators': creators}
    ensure_related_identifiers(patch_md)

    update_payload = {'metadata': patch_md}
    code, upd = req('PUT', f'/deposit/depositions/{dep_id}', update_payload)
    if code not in (200, 201):
        print(f"[zenodo-fix] ERROR updating deposition: {code} {upd}")
        # If record is published, try creating a new draft version
        if dep_id and state == 'done':
            print('[zenodo-fix] Trying to create a new version draft...')
            code2, newv = req('POST', f'/deposit/depositions/{dep_id}/actions/newversion')
            if code2 in (201, 202):
                latest_draft = (newv.get('links', {}) or {}).get('latest_draft')
                if latest_draft:
                    # latest_draft is a URL like .../deposit/depositions/<id>
                    try:
                        new_id = latest_draft.rstrip('/').split('/')[-1]
                        print(f"[zenodo-fix] New draft id={new_id}")
                        # Fetch new draft full metadata
                        code3, newdetail = req('GET', f'/deposit/depositions/{new_id}')
                        if code3 != 200:
                            print(f"[zenodo-fix] ERROR fetching new draft: {code3} {newdetail}")
                            sys.exit(4)
                        new_md = newdetail.get('metadata') or {}
                        # Heuristic: use RDM-style creators if keys present, else deposit style
                        use_rdm = True
                        # Prepare both creator formats
                        creators_rdm = [
                            {
                                'person_or_org': {
                                    'type': 'personal',
                                    'given_name': 'Demetrios C.',
                                    'family_name': 'Agourakis',
                                    'identifiers': [ {'scheme': 'orcid', 'identifier': '0000-0002-8596-5097'} ],
                                }
                            },
                            {
                                'person_or_org': {
                                    'type': 'personal',
                                    'given_name': 'Dionisio Chiuratto',
                                    'family_name': 'Agourakis'
                                }
                            }
                        ]
                        creators_deposit = [
                            { 'name': 'Agourakis, Demetrios C.', 'orcid': '0000-0002-8596-5097' },
                            { 'name': 'Agourakis, Dionisio Chiuratto' }
                        ]
                        # Decide on schema: prefer RDM
                        if use_rdm:
                            new_md['creators'] = creators_rdm
                            # Ensure RDM resource_type
                            if not isinstance(new_md.get('resource_type'), dict):
                                new_md['resource_type'] = {'type': 'software'}
                        else:
                            new_md['creators'] = creators_deposit
                            new_md['upload_type'] = 'software'
                            if 'resource_type' in new_md:
                                new_md.pop('resource_type', None)
                        ensure_related_identifiers(new_md)
                        # Remove dates if present and potentially invalid
                        if 'dates' in new_md:
                            new_md.pop('dates', None)
                        # Ensure required fields
                        if not new_md.get('title'):
                            new_md['title'] = md.get('title') or 'Symbolic Manifolds v4.3.2 — data crystallization patch'
                        if not new_md.get('description'):
                            new_md['description'] = 'Patch release focusing on data crystallization (L0→L1→L2), provenance, and reproducibility.'
                        code4, upd2 = req('PUT', f'/deposit/depositions/{new_id}', {'metadata': new_md})
                        if code4 in (200, 201):
                            dep_id = new_id
                            print('[zenodo-fix] Draft metadata updated.')
                            # Upload asset if missing
                            files = newdetail.get('files') or []
                            want = 'data_release.tar.gz'
                            has = any(f.get('filename') == want for f in files)
                            if not has and os.path.isfile(want):
                                bucket = (newdetail.get('links') or {}).get('bucket')
                                if bucket:
                                    try:
                                        codeu, updr = upload_to_bucket(bucket, want)
                                        if codeu in (200, 201):
                                            print('[zenodo-fix] Uploaded data_release.tar.gz to draft.')
                                        else:
                                            print(f"[zenodo-fix] WARN upload failed: {codeu} {updr}")
                                    except Exception as ue:
                                        print(f"[zenodo-fix] WARN upload exception: {ue}")
                            else:
                                print('[zenodo-fix] Draft already has asset attached.')
                        else:
                            print(f"[zenodo-fix] ERROR patching new draft: {code4} {upd2}")
                            sys.exit(4)
                    except Exception as e:
                        print(f"[zenodo-fix] ERROR parsing latest_draft url: {e}")
                        sys.exit(4)
                else:
                    print('[zenodo-fix] No latest_draft link returned.')
                    sys.exit(4)
            else:
                print(f"[zenodo-fix] ERROR creating new version: {code2} {newv}")
                sys.exit(4)
        else:
            sys.exit(4)
    else:
        print('[zenodo-fix] Creators updated successfully.')

    # Try to publish
    code, pub = req('POST', f'/deposit/depositions/{dep_id}/actions/publish')
    if code not in (200, 201, 202):
        print(f"[zenodo-fix] WARN: publish failed or not allowed: {code} {pub}")
        print('[zenodo-fix] You may need to publish manually in the UI.')
    else:
        rec_url = pub.get('links', {}).get('html') or pub.get('links', {}).get('latest_html', '')
        doi = pub.get('doi') or (pub.get('metadata', {})).get('doi')
        print(f"[zenodo-fix] Published. Record URL: {rec_url} DOI: {doi}")

if __name__ == '__main__':
    main()
