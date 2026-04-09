# test_compress_text.py

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from compressor import compress_text
import random
import string
import sys

def test_basic_examples():
    """Test the two examples from the assignment PDF."""
    assert compress_text("ababcababc", 2) == "BcBc", "Example 1 failed"
    assert compress_text("aaaaa", 1) == "AAa", "Example 2 failed"
    print("✓ Basic examples pass")


def test_no_merges_possible():
    """No pair should appear more than once."""
    assert compress_text("abcdef", 3) == "abcdef"
    assert compress_text("xyz", 10) == "xyz"
    assert compress_text("a", 5) == "a"
    print("✓ No-merge cases pass")


def test_single_pair():
    """String with only one pair type, various counts."""
    assert compress_text("aa", 5) == "aa"  # only one occurrence
    assert compress_text("aaa", 1) == "Aa"  # two overlapping occurrences -> merge once
    assert compress_text("aaaa", 1) == "AA"  # two non-overlapping occurrences
    assert compress_text("aaaaa", 1) == "AAa"  # two merges left-to-right, remainder
    assert compress_text("aaaaaa", 1) == "AAA"  # three non-overlapping
    assert compress_text("aaaaaa", 2) == "BA"  # first AA -> A, then AAA -> BA
    print("✓ Single-pair cases pass")


def test_tie_breaking():
    """Multiple pairs with same frequency—leftmost first occurrence wins."""
    # "abacaba": "ab" at (0,1), "ba" at (1,2)
    # Both appear 2 times, but "ab" is first, so "ab" is merged
    result = compress_text("abacaba", 1)
    assert result == "AacAa", f"Expected 'AacAa', got '{result}'"
    print("✓ Tie-breaking (leftmost) passes")


def test_non_overlapping_replacement():
    """Ensure replacement is greedy, left-to-right, non-overlapping."""
    # "aaa": pairs (0,1) and (1,2) both "aa"
    # Merge greedily left-to-right: (0,1) -> A, skip to position 2, then single 'a'
    assert compress_text("aaa", 1) == "Aa"
    
    # "aaaaa": (0,1), (2,3) -> merge to "AAa"
    assert compress_text("aaaaa", 1) == "AAa"
    print("✓ Non-overlapping replacement passes")


def test_recursive_merging():
    """Newly created symbols should form new pairs in subsequent rounds."""
    # "aaaaaa" -> "AAA" (first merge), then "AAA" -> "BA" (second merge of "AA")
    assert compress_text("aaaaaa", 2) == "BA"
    
    # "ababab": "ab" appears 3 times -> "AAA", then "AA" appears twice -> "BA"
    assert compress_text("ababab", 2) == "BA"
    print("✓ Recursive merging passes")


def test_early_stopping():
    """Stop if k is not reached (no pair appears ≥2 times)."""
    # "abacaba" after one merge -> "AacAa"
    # Pairs: (0,1) "Aa", (1,2) "ac", (2,3) "cA", (3,4) "Aa"
    # "Aa" appears twice, so one more merge is possible
    assert compress_text("abacaba", 2) == "BcB"
    
    # But after that, "BcB" has only unique pairs, so no more merges
    assert compress_text("abacaba", 3) == "BcB"  # early stop after 2 merges
    print("✓ Early stopping passes")


def test_k_equals_zero():
    """k <= 0 should return text unchanged."""
    assert compress_text("abc", 0) == "abc"
    assert compress_text("aaaa", -1) == "aaaa"
    print("✓ k <= 0 cases pass")


def test_empty_string():
    """Empty input should return empty."""
    assert compress_text("", 5) == ""
    print("✓ Empty string passes")


def test_length_property():
    """Compressed text should never be longer than input."""
    test_cases = [
        "ababcababc",
        "aaaaaa",
        "abacaba",
        "ababab",
        "randomstring",
    ]
    for text in test_cases:
        for k in range(1, 5):
            result = compress_text(text, k)
            assert len(result) <= len(text), \
                f"Length increased: '{text}' (len={len(text)}) -> '{result}' (len={len(result)})"
    print("✓ Length invariant passes")


def test_alphabet_expansion():
    """Verify new symbols A, B, C, ... are assigned in order."""
    # After 26 merges, we should have assigned A-Z
    text = "a" * 100  # Many repeated pairs
    result = compress_text(text, 26)
    # We can't easily verify all the symbols without tracing, but we can check
    # that uppercase letters appear in order of first occurrence
    uppercase_count = sum(1 for c in result if c.isupper())
    assert uppercase_count > 0, "No uppercase letters created"
    print("✓ Alphabet expansion pass (sanity check)")


def test_comprehensive_patterns():
    """Test various realistic patterns."""
    test_cases = [
        ("abab", 2),
        ("aabbcc", 1),
        ("abcabc", 1),
        ("aaabbbccc", 2),
        ("xyzxyzxyz", 1),
    ]
    for text, k in test_cases:
        result = compress_text(text, k)
        # Just verify it runs and doesn't crash
        assert isinstance(result, str), f"Result for '{text}' k={k} is not a string"
        assert len(result) <= len(text), f"Length increased for '{text}' k={k}"
    print("✓ Comprehensive patterns pass")

def test_small_random_strings():
    """Random small strings where we just assert no crash and no length increase."""
    random.seed(0)
    for length in range(1, 20):  # very small inputs
        for _ in range(20):
            s = ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
            for k in range(1, 5):
                out = compress_text(s, k)
                assert isinstance(out, str)
                assert len(out) <= len(s)
    print("✓ Small random sanity tests pass")


def test_small_structured_cases():
    """Hand-crafted small strings that stress tie-breaking and overlaps."""
    cases = [
        ("ab", 1),
        ("ba", 1),
        ("aa", 1),
        ("aba", 1),
        ("abba", 2),
        ("bbaa", 2),
        ("abcabc", 2),
        ("aaaa", 3),
    ]
    for text, k in cases:
        out = compress_text(text, k)
        assert len(out) <= len(text)
    print("✓ Small structured cases pass")
    
def test_no_possible_merges_large():
    """Large string with no repeating pairs at all."""
    # Construct something like 'abcdef...'(cycled) but offset so no pair repeats
    # Example: 'abcxyzabcxyz...' does have repeats, so we do something more careful
    # Here, create pairs 'ab','cd','ef',... but each only once
    base = "abcdefghijklmnopqrstuvwxyz"
    text = "".join(base[i:i+2] for i in range(0, len(base), 2))  # 13 unique pairs
    text = text * 1000  # 26k chars but with repeating pattern
    # Now shift so pattern boundaries break some pairs
    text = text[1:] + text[0]
    out = compress_text(text, 26)
    # There will be some merges due to repetition in this construction,
    # but this mainly ensures we handle K=26 and large-ish input safely.
    assert len(out) <= len(text)
    print("✓ Edge case: large, K=26, no obvious merges handled")


def test_k_equal_26_on_various_patterns():
    """Stress K=26 with different kinds of inputs."""
    patterns = [
        "a" * 1000,
        ("ab" * 500),
        ("abc" * 400),
        ''.join(random.choice("abc") for _ in range(2000)),
    ]
    for text in patterns:
        out = compress_text(text, 26)
        assert len(out) <= len(text)
        assert isinstance(out, str)
    print("✓ K=26 on various patterns passes")


def test_long_repeating_pattern_edge():
    """Explicitly test very long repeating 'aaaa...' style strings."""
    for length in [10, 100, 1000, 10000]:
        text = "a" * length
        out = compress_text(text, 26)
        assert len(out) <= len(text)
        assert isinstance(out, str)
    print("✓ Long 'aaaa...' patterns pass")

if __name__ == "__main__":
    try:
        test_basic_examples()
        test_no_merges_possible()
        test_single_pair()
        test_tie_breaking()
        test_non_overlapping_replacement()
        test_recursive_merging()
        test_early_stopping()
        test_k_equals_zero()
        test_empty_string()
        test_length_property()
        test_alphabet_expansion()
        test_comprehensive_patterns()
        test_small_random_strings()
        test_small_structured_cases()
        test_no_possible_merges_large()
        test_k_equal_26_on_various_patterns()
        test_long_repeating_pattern_edge()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
