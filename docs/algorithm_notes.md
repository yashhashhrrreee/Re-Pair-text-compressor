# Algorithm Notes: Re-Pair Compressor

## Why the Naive Approach Fails

The obvious implementation looks like this:

```python
def compress_text_naive(text, k):
    for _ in range(k):
        # Count all pairs — O(n)
        counts = Counter(zip(text, text[1:]))
        if not counts or max(counts.values()) < 2:
            break
        best = max(counts, key=lambda p: (counts[p], -text.index(''.join(p))))
        new_sym = next_symbol()
        text = text.replace(''.join(best), new_sym)  # ← O(n) but with huge constant
    return text
```

The problem: `str.replace` creates a new string of length O(n) each round, AND Python string operations on unicode are slow. On a 1M-char string with k=26, this means 26 full string reconstructions — easily 30–60 seconds.

## The Linked List Trick

Instead of rebuilding the string, we simulate it as a doubly-linked list embedded in fixed-size arrays:

```
Original: a b c a b c
Index:    0 1 2 3 4 5

nxt = [1, 2, 3, 4, 5, -1]
prv = [-1, 0, 1, 2, 3, 4]
sym = [0, 1, 2, 0, 1, 2]   # a=0, b=1, c=2
```

When we merge pair `(a=0, b=1)` at positions `(0,1)` and `(3,4)`:
- Set `sym[0] = 26` (new symbol 'A'), unlink position 1
- Set `sym[3] = 26`, unlink position 4

```
After merge:
nxt = [2, -, 3, 5, -, -1]    (positions 1,4 are dead)
sym = [26, -, 2, 26, -, 2]

Logical string: A c A c
```

Deletions are O(1). The full merge pass is O(n) — one scan of live nodes.

## Tie-Breaking: Leftmost First Occurrence

When two pairs have equal frequency, the one with the **smaller index of first occurrence** wins. This is tracked in the `leftmost` dict during the scan.

The heap key is `(-count, leftmost_pos, a, b)` — Python's min-heap naturally returns the highest count first, then smallest position as tiebreaker.

## Greedy Non-Overlapping Replacement

For a string like `"aaa"` with pair `(a, a)`:
- Positions: `(0,1)` and `(1,2)` both match
- We take `(0,1)` first, skip to position 2 (the `nxt` after the deleted position 1)
- Position 2 is now a lone `a` — no second match
- Result: `"Aa"` ✓ (not `"aA"` or `"A"`)

This is handled automatically by the left-to-right scan: after merging at `i`, we advance to `nxt[i]` (which skips the deleted `j`).

## Where the O(kn) Comes From

Each of the k rounds:
1. **Rescan** all live nodes to count pairs → O(current_length)
2. **Build heap** from pair counts → O(p log p) where p ≤ distinct pairs
3. **Merge pass** → O(current_length)

Since each merge reduces the string by at least 1 character (often many more), total work across all rounds is bounded by O(k·n). In practice, highly compressible strings (uniform, repeated) shrink rapidly, making later rounds very fast.

## Potential Improvements (Beyond Assignment Scope)

### Incremental pair tracking

Instead of rescanning every round, maintain pair counts incrementally:
- When merging `(a,b)` at position `i`:
  - Decrement count of `(prv_sym, a)` and `(b, nxt_sym)` (they lose one occurrence)
  - Increment count of `(prv_sym, X)` and `(X, nxt_sym)` (new pairs formed)

This brings the total complexity to **O(n log n)** for all k rounds combined — the true Re-Pair complexity from the original paper.

### Why we didn't do it here

Incremental tracking is correct but tricky to implement with the leftmost-position tiebreaker. The assignment allows k ≤ 26 and n ≤ 10^6, so O(k·n) = O(26·10^6) ≈ 26M operations is fast enough for most cases.

## Memory Layout

```
Arrays allocated once at size N (original string length):
  sym[N]   — 8 bytes each (Python int) → ~8 MB for N=1M
  nxt[N]   — 8 bytes each              → ~8 MB
  prv[N]   — 8 bytes each              → ~8 MB
  alive[N] — 1 byte each (bool)        → ~1 MB

Total: ~25 MB for N=1M — well within the 256 MB limit.
```

Python lists of ints use more memory than raw C arrays, but are fast enough in practice. For extreme performance, `array.array('i', ...)` or numpy arrays could reduce memory by 4–8x.
