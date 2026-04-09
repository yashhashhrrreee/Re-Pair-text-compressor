#!/usr/bin/env python3
"""
re-pair-compressor CLI
Usage:
    python -m src "your text here" 5
    echo "your text here" | python -m src - 5
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from compressor import compress_text


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m src <text> <k>")
        print("       echo 'text' | python -m src - <k>")
        sys.exit(1)

    text_arg = sys.argv[1]
    k = int(sys.argv[2])

    if text_arg == "-":
        text = sys.stdin.read().rstrip("\n")
    else:
        text = text_arg

    result = compress_text(text, k)
    print(result)


if __name__ == "__main__":
    main()
