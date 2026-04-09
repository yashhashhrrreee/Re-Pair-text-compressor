# compressor_solution.py
from __future__ import annotations

import heapq
from typing import Dict, List, Tuple


def compress_text(text: str, k: int) -> str:
    """
    - Repeatedly merge the most frequent adjacent pair.
    - Tie-breaker: earliest (leftmost) occurrence in the current string.
    - Replace all non-overlapping occurrences greedily, left-to-right.
    - New symbols: 'A', 'B', 'C', ... sequentially.
    - Stop early if no adjacent pair occurs more than once.
    """

    n0 = len(text)
    if n0 <= 1 or k <= 0:
        return text

    # Represent symbols as integers to keep operations fast:
    # 'a'..'z' -> 0..25, 'A'.. -> 26.. (created)
    # Output conversion at the end.
    sym: List[int] = [ord(c) - 97 for c in text]

    # Doubly linked list in arrays over positions 0..n0-1
    nxt = list(range(1, n0)) + [-1]
    prv = [-1] + list(range(0, n0 - 1))
    alive = [True] * n0

    head = 0
    while head != -1 and not alive[head]:
        head = nxt[head]

    # Pair stats: counts and leftmost start position among current alive occurrences
    # Key for pair: (a,b) as tuple[int,int]
    counts: Dict[Tuple[int, int], int] = {}
    leftmost: Dict[Tuple[int, int], int] = {}

    def recompute_pair_stats() -> None:
        """Recompute pair counts and leftmost occurrence by scanning the current list."""
        counts.clear()
        leftmost.clear()
        i = head
        while i != -1:
            j = nxt[i]
            if j == -1:
                break
            p = (sym[i], sym[j])
            counts[p] = counts.get(p, 0) + 1
            if p not in leftmost:
                leftmost[p] = i
            i = j

    def build_heap() -> List[Tuple[int, int, int, int]]:
        """
        Heap items: (-count, leftmost_pos, a, b)
        leftmost_pos is used for tie-breaker (smaller pos => earlier in string).  
        """
        h: List[Tuple[int, int, int, int]] = []
        for (a, b), c in counts.items():
            if c > 1:
                heapq.heappush(h, (-c, leftmost[(a, b)], a, b))
        return h

    def merge_pair(a: int, b: int, new_sym: int) -> None:
        """
        Replace all non-overlapping occurrences of (a,b) with new_sym,
        greedy left-to-right.  
        """
        nonlocal head

        i = head
        while i != -1:
            j = nxt[i]
            if j == -1:
                break

            if sym[i] == a and sym[j] == b and alive[i] and alive[j]:
                # Replace at i: sym[i]=new_sym, delete j
                sym[i] = new_sym

                # Remove j from linked list
                nj = nxt[j]
                nxt[i] = nj
                if nj != -1:
                    prv[nj] = i
                alive[j] = False
                nxt[j] = -1
                prv[j] = -1

                # Greedy non-overlapping means after merging at (i,j),
                # continue scanning from i's next (which is nj now),
                # not from the removed j.  
                i = nxt[i]
            else:
                i = j

        # Fix head if needed (usually not, but safe)
        while head != -1 and not alive[head]:
            head = nxt[head]

    # Main loop: up to k merges, but stop if no pair occurs  
    next_new = 26  # 'A' starts after 0..25
    for _ in range(k):
        recompute_pair_stats()
        h = build_heap()
        if not h:
            break

        # Choose best pair by max frequency, then leftmost occurrence.  
        negc, pos, a, b = heapq.heappop(h)
        # Because we fully recompute each round, heap top is valid.
        new_sym = next_new
        next_new += 1

        merge_pair(a, b, new_sym)

    # Build output string by traversing the list
    out_chars: List[str] = []
    i = head
    while i != -1:
        s = sym[i]
        if s < 26:
            out_chars.append(chr(97 + s))        # a-z
        else:
            out_chars.append(chr(65 + (s - 26))) # A,B,C,...
        i = nxt[i]

    return "".join(out_chars)

if __name__ == "__main__":
    # Example 1 (from the assignment)
    text = "ababcababc"
    k = 2
    expected = "BcBc"
    got = compress_text(text, k)
    print("Example 1:", got)
    assert got == expected, f"Example 1 failed: got {got}, expected {expected}"

    # Example 2 (from the assignment)
    text = "aaaaa"
    k = 1
    expected = "AAa"
    got = compress_text(text, k)
    print("Example 2:", got)
    assert got == expected, f"Example 2 failed: got {got}, expected {expected}"

    print("All assignment examples passed.")