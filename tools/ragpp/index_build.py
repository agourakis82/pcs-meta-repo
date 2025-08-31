#!/usr/bin/env python3
"""RAG++ Index Builder (skeleton).
Usage:
  python tools/ragpp/index_build.py --root . --out data/rag_index
"""
import argparse, os
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.', help='Repository root')
    ap.add_argument('--out', default='data/rag_index', help='Output dir')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, 'INDEX_README.txt'), 'w') as f:
        f.write('RAG++ index placeholder. Fill with embeddings later.\n')
if __name__ == '__main__':
    main()
