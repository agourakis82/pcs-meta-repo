#!/usr/bin/env python3
import os, sys, json, urllib.request, urllib.error, datetime

BASE = 'https://zenodo.org/api'

TOKEN = os.environ.get('ZENODO_TOKEN')
if not TOKEN:
    print('[zenodo-complete] ERROR: ZENODO_TOKEN not set', file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    print('Usage: tools/zenodo_complete_draft.py <deposition_id>', file=sys.stderr)
    sys.exit(1)

DEP_ID = sys.argv[1].strip()

def req(method, path, data=None, headers=None, timeout=120):
    url = BASE + path
    h = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode('utf-8')
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            payload = resp.read()
            try:
                return resp.getcode(), json.loads(payload.decode('utf-8'))
            except Exception:
                return resp.getcode(), payload.decode('utf-8')
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode('utf-8'))
        except Exception:
            return e.code, {'error': str(e)}

def upload_file(bucket_url, local_path):
    name = os.path.basename(local_path)
    url = bucket_url.rstrip('/') + '/' + name
    headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/octet-stream'}
    with open(local_path, 'rb') as f:
        data = f.read()
    r = urllib.request.Request(url, data=data, headers=headers, method='PUT')
    with urllib.request.urlopen(r, timeout=600) as resp:
        payload = resp.read()
        try:
            return resp.getcode(), json.loads(payload.decode('utf-8'))
        except Exception:
            return resp.getcode(), payload.decode('utf-8')

def main():
    code, detail = req('GET', f'/deposit/depositions/{DEP_ID}')
    if code != 200:
        print(f'[zenodo-complete] ERROR fetching draft {DEP_ID}: {code} {detail}')
        sys.exit(2)
    state = detail.get('state')
    print(f'[zenodo-complete] Draft id={DEP_ID} state={state}')

    today = datetime.date.today().isoformat()
    # Minimal RDM metadata
    md = {
        'title': 'Symbolic Manifolds v4.3.2 — data crystallization patch',
        'publication_date': today,
        'version': '4.3.2',
        'description': 'Patch release focusing on data crystallization (L0→L1→L2), provenance, and reproducibility. Excludes L0 raw data; includes L1/L2, provenance, and checks.',
        'resource_type': {'id': 'software'},
        'creators': [
            {
                'person_or_org': {
                    'type': 'personal',
                    'given_name': 'Demetrios',
                    'family_name': 'Chiuratto Agourakis',
                    'identifiers': [{'scheme': 'orcid', 'identifier': '0000-0002-8596-5097'}]
                }
            },
            {
                'person_or_org': {
                    'type': 'personal',
                    'given_name': 'Dionisio',
                    'family_name': 'Chiuratto Agourakis'
                }
            }
        ],
        'related_identifiers': [
            {'scheme': 'doi', 'identifier': '10.5281/zenodo.16533374', 'relation_type': {'id': 'isversionof'}}
        ],
    }

    # Patch metadata
    code, upd = req('PUT', f'/deposit/depositions/{DEP_ID}', {'metadata': md})
    if code not in (200, 201):
        print(f'[zenodo-complete] ERROR updating metadata: {code} {upd}')
        sys.exit(3)
    print('[zenodo-complete] Metadata updated.')

    # Ensure file
    asset = 'data_release.tar.gz'
    files = detail.get('files') or []
    has = any(f.get('filename') == asset for f in files)
    if not has:
        bucket = (detail.get('links') or {}).get('bucket')
        if not bucket:
            # refetch to get bucket link if missing
            code, detail2 = req('GET', f'/deposit/depositions/{DEP_ID}')
            bucket = (detail2.get('links') or {}).get('bucket') if code == 200 else None
        if bucket and os.path.isfile(asset):
            try:
                codeu, out = upload_file(bucket, asset)
                if codeu in (200, 201):
                    print('[zenodo-complete] File uploaded to bucket.')
                else:
                    print(f'[zenodo-complete] WARN upload failed: {codeu} {out}')
            except Exception as e:
                print(f'[zenodo-complete] WARN upload exception: {e}')
        else:
            print('[zenodo-complete] WARN: missing bucket link or local asset, skipping upload')
    else:
        print('[zenodo-complete] File already present.')

    # Publish
    code, pub = req('POST', f'/deposit/depositions/{DEP_ID}/actions/publish')
    if code in (200, 201, 202):
        rec_url = (pub.get('links', {}) or {}).get('html') or (pub.get('links', {}) or {}).get('latest_html')
        doi = pub.get('doi') or (pub.get('metadata', {}) or {}).get('doi')
        print(f'[zenodo-complete] Published. Record: {rec_url} DOI: {doi}')
    else:
        print(f'[zenodo-complete] WARN: publish failed {code} {pub}')
        sys.exit(4)

if __name__ == '__main__':
    main()
