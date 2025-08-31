#!/usr/bin/env python3
# RAG++ Query CLI (skeleton).
import argparse
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', required=True)
    args = ap.parse_args()
    print('RAG++ placeholder. Query:', args.q)
if __name__ == '__main__':
    main()
