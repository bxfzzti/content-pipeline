#!/usr/bin/env python3
"""Run hotspot collection and one-shot semantic screening end to end."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def run(command: list[str], timeout: float) -> None:
    subprocess.run(command, check=True, timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='/tmp/article-pipeline')
    parser.add_argument('--hotspot-deadline', type=float, default=120.0)
    parser.add_argument('--screening-timeout', type=float, default=75.0)
    args = parser.parse_args()

    started = time.monotonic()
    home = Path.home() / '.hermes' / 'skills'
    run([
        sys.executable,
        str(home / 'sourcing-hotspots/scripts/full_hotspot_run.py'),
        '--output-dir', args.output_dir,
        '--deadline-seconds', str(args.hotspot_deadline),
    ], args.hotspot_deadline + 15)
    run([
        sys.executable,
        str(home / 'screening-topics/scripts/run_screening_once.py'),
        '--candidates', str(Path(args.output_dir) / '01c-screening-candidates.json'),
        '--judgments', str(Path(args.output_dir) / '02a-model-judgments.json'),
        '--output-json', str(Path(args.output_dir) / '02-topic-suggestion.json'),
        '--output-md', str(Path(args.output_dir) / '02-topic-suggestion.md'),
        '--timeout', str(args.screening_timeout),
    ], args.screening_timeout + 15)
    print(json.dumps({'ok': True, 'elapsed_seconds': round(time.monotonic() - started, 3)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
