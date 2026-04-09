# Re-Pair Text Compressor

A fast Python implementation of the **Re-Pair** (Recursive Pairing) algorithm — the foundational compression technique behind modern **Byte Pair Encoding (BPE)** tokenizers used in large language models like GPT and BERT.

---

## What Is Re-Pair?

Re-Pair is an off-line dictionary-based compression algorithm originally proposed by [Larsson & Moffat (1999)](https://doi.org/10.1109/5.892840). The core idea is simple but powerful:

1. Find the most frequent adjacent pair of symbols in the string.
2. Replace every non-overlapping occurrence of that pair with a new, single symbol.
3. Repeat up to _k_ times (or until no pair appears more than once).

This is exactly what modern BPE tokenizers do — they learn a vocabulary by repeatedly merging frequent character pairs in a training corpus.

### Example

```
Input:  "ababcababc"   k=2

Step 1: "ab" appears 4 times → replace with 'A'
        "AAcAAc"

Step 2: "AA" appears 2 times, "Ac" appears 2 times → tie broken by leftmost → replace "AA" with 'B'
        "BcBc"

Output: "BcBc"
```

---

## Algorithm Design

The naive approach (re-scan the string each round) is **O(n·k)** and hits the time limit on large inputs. This implementation is designed for efficiency:

| Component             | Approach                                                  | Complexity           |
| --------------------- | --------------------------------------------------------- | -------------------- |
| String representation | Doubly-linked list over index arrays (`next[]`, `prev[]`) | O(1) insert/delete   |
| Pair counting         | Hash map + full rescan per round                          | O(n) per round       |
| Best pair selection   | Min-heap keyed on `(-count, leftmost_pos)`                | O(p log p) per round |
| Replacement pass      | Single left-to-right traversal of live nodes              | O(n) per round       |

**Overall: O(k·n)** time, **O(n)** space — practical up to ~1M characters with k=26.

### Data Structures

```
Index arrays (size = original string length N):
  sym[i]   — current symbol at position i (int; 0–25 = a–z, 26+ = A, B, C…)
  nxt[i]   — index of the next live character (linked list "next" pointer)
  prv[i]   — index of the previous live character
  alive[i] — whether position i is still active

Per round:
  counts   — dict mapping (a, b) → occurrence count
  leftmost — dict mapping (a, b) → index of first occurrence
  heap     — min-heap of (-count, leftmost_pos, a, b)
```

When a pair `(a, b)` is merged into new symbol `X` at position `i`:

- `sym[i]` is updated to `X`
- position `j` (the `b` in the pair) is unlinked and marked dead
- the heap is rebuilt from scratch next round (simple & correct for k ≤ 26)

---

## Project Structure

```
re-pair-compressor/
├── src/
│   ├── compressor.py      # Core algorithm — compress_text(text, k)
│   ├── __init__.py        # Package exports
│   └── __main__.py        # CLI entry point
├── tests/
│   ├── conftest.py        # pytest path setup
│   └── test_compressor.py # 17 test cases covering correctness & edge cases
├── benchmarks/
│   └── benchmark.py       # Scalability & stress benchmark suite
├── results/
│   └── benchmark_results.json  # Pre-run benchmark output
├── docs/
│   └── algorithm_notes.md      # Deeper dive into the algorithm
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- No third-party dependencies (stdlib only)

### Installation

```bash
git clone https://github.com/yashhashhrrreee/Re-Pair-text-compressor.git
cd re-pair-compressor
```

### Run the compressor

```python
from src.compressor import compress_text

result = compress_text("ababcababc", k=2)
print(result)  # → "BcBc"

result = compress_text("aaaaa", k=1)
print(result)  # → "AAa"
```

### CLI usage

```bash
# Compress a string directly
python -m src "ababcababc" 2
# → BcBc

# Pipe from stdin
echo "ababcababc" | python -m src - 2
# → BcBc
```

---

## Running Tests

```bash
# Using the test script directly
python tests/test_compressor.py

# Or with pytest
pip install pytest
pytest tests/ -v
```

### Test coverage

| Category                           | Tests                                     |
| ---------------------------------- | ----------------------------------------- |
| Assignment examples                | `test_basic_examples`                     |
| No possible merges                 | `test_no_merges_possible`                 |
| Single pair patterns               | `test_single_pair`                        |
| Tie-breaking (leftmost wins)       | `test_tie_breaking`                       |
| Non-overlapping greedy replacement | `test_non_overlapping_replacement`        |
| Recursive merging (A→B chains)     | `test_recursive_merging`                  |
| Early stopping                     | `test_early_stopping`                     |
| Edge cases (k=0, empty string)     | `test_k_equals_zero`, `test_empty_string` |
| Length invariant                   | `test_length_property`                    |
| k=26 stress                        | `test_k_equal_26_on_various_patterns`     |
| Large random inputs                | `test_long_repeating_pattern_edge`        |

---

## Benchmarks

```bash
python benchmarks/benchmark.py
```

Results are saved to `results/benchmark_results.json`.

### Performance summary (pre-run results)

| Input size | Pattern                  | k   | Time     |
| ---------- | ------------------------ | --- | -------- |
| 100k       | uniform (aaaa…)          | 26  | ~0.01s   |
| 100k       | repeated pairs (ababab…) | 26  | ~0.02s   |
| 500k       | random                   | 20  | ~2.0s    |
| 750k       | mixed                    | 26  | ~1.6s    |
| 1M         | random                   | 26  | ~5.1s ⚠️ |

> **Note:** The 1M-char random k=26 case exceeds the 3s classroom time limit. Random strings have many unique pairs surviving each round, making each scan expensive. Structured/compressible inputs (uniform, repeated) are significantly faster since the string shrinks rapidly after each merge.

---

## Connection to BPE Tokenization

This algorithm is the direct ancestor of **Byte Pair Encoding**, used to build vocabularies for:

- **GPT-2 / GPT-3 / GPT-4** (OpenAI)
- **BERT / RoBERTa** (uses WordPiece, a variant)
- **LLaMA, Mistral** and most modern open-source LLMs

The difference: BPE tokenizers run Re-Pair on a large corpus to learn a _fixed vocabulary_, then apply that vocabulary at inference time. This implementation shows the core merge loop in its purest form.

---

## Algorithm Notes

See [`docs/algorithm_notes.md`](docs/algorithm_notes.md) for:

- Detailed walkthrough of the linked-list trick
- Why naive approaches fail at scale
- Potential O(n log n) improvements using incremental pair tracking

---

## References

- Larsson, N. J., & Moffat, A. (2000). _Off-line dictionary-based compression_. Proceedings of the IEEE, 88(11), 1722–1732.
- Sennrich, R., Haddow, B., & Birch, A. (2016). _Neural machine translation of rare words with subword units_ (BPE for NLP). ACL 2016.
