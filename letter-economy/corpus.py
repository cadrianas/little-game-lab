"""Word corpus for Letter Economy: ENABLE dictionary + Google web frequencies.

ENABLE is public domain. The frequency list (Norvig, Google Web Trillion Word
Corpus) is used only to rank words by commonness, so puzzle answers can be
gated on being words a normal person actually knows.
"""

from collections import Counter
from pathlib import Path

DATA = Path(__file__).parent / "data"
DICTIONARY_FILES = (DATA / "enable1.txt", DATA / "custom_words.txt")
DEEP_CUT_FILE = DATA / "deep_cut_words.tsv"

MIN_LEN = 4
MAX_LEN = 12

# A word is only allowed to be a puzzle's *answer* if it is at least this
# common. The frequency list is raw web text, so it ranks plenty of obscure
# words higher than you would expect; 14k is where AMANITIN and CLERISIES stop
# turning up as answers.
ANSWER_FREQ_RANK = 14_000


def load_deep_cuts():
    """Curated rare answers, kept separate from broad guess acceptance."""
    cuts = {}
    with open(DEEP_CUT_FILE) as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            word, part_of_speech, definition, source = line.rstrip("\n").split("\t")
            cuts[word] = {
                "part_of_speech": part_of_speech,
                "definition": definition,
                "source": source,
            }
    return cuts


class Word:
    __slots__ = ("text", "mask", "counts", "rank")

    def __init__(self, text, rank):
        self.text = text
        self.mask = 0
        for ch in set(text):
            self.mask |= 1 << (ord(ch) - 97)
        self.counts = Counter(text)
        self.rank = rank

    def cost(self, prices, charge="per_use"):
        if charge == "per_letter":
            # Buy each distinct letter once, then reuse it freely.
            return sum(prices[ch] for ch in self.counts)
        return sum(prices[ch] * n for ch, n in self.counts.items())

    def __repr__(self):
        return f"<{self.text} r{self.rank}>"


def load_ranks():
    ranks = {}
    with open(DATA / "count_1w.txt") as fh:
        for i, line in enumerate(fh):
            word = line.split("\t", 1)[0]
            if word not in ranks:
                ranks[word] = i
    return ranks


def load_words():
    """Return (all_words, by_mask) where by_mask groups words by letter-set.

    Grouping by letter-set is what makes puzzle search fast: to find every word
    spellable from a 7-letter pool we look up the pool's 128 sub-masks rather
    than scanning 170k words.
    """
    ranks = load_ranks()
    word_ranks = {}
    for path in DICTIONARY_FILES:
        if not path.exists():
            continue
        with open(path) as fh:
            for line in fh:
                parts = line.split("#", 1)[0].split()
                if not parts:
                    continue
                text = parts[0]
                custom_rank = None
                if path.name == "custom_words.txt" and len(parts) > 1:
                    try:
                        custom_rank = int(parts[1])
                    except ValueError as exc:
                        raise ValueError(
                            f"invalid custom rank in {path}: {line.strip()}"
                        ) from exc
                if path.name == "custom_words.txt":
                    # A bare custom entry expands accepted guesses only. It
                    # must be explicitly assigned a rank before it can become
                    # a generated answer or side-goal word.
                    rank = custom_rank if custom_rank is not None else 10**9
                else:
                    rank = ranks.get(text, 10**9)
                previous = word_ranks.get(text)
                if previous is None or rank < previous:
                    word_ranks[text] = rank

    words = []
    for text, rank in word_ranks.items():
            if not (MIN_LEN <= len(text) <= MAX_LEN):
                continue
            if not text.isalpha() or not text.isascii() or not text.islower():
                continue
            words.append(Word(text, rank))

    by_mask = {}
    for w in words:
        by_mask.setdefault(w.mask, []).append(w)
    return words, by_mask


def submasks(mask):
    """Every subset of a bitmask, including the mask itself (excluding empty)."""
    out = []
    sub = mask
    while sub:
        out.append(sub)
        sub = (sub - 1) & mask
    return out


def spellable(pool_mask, by_mask):
    """All words using only letters from the pool (repeats allowed)."""
    out = []
    for sub in submasks(pool_mask):
        got = by_mask.get(sub)
        if got:
            out.extend(got)
    return out


def mask_of(letters):
    m = 0
    for ch in letters:
        m |= 1 << (ord(ch) - 97)
    return m


def letters_of(mask):
    return [chr(97 + i) for i in range(26) if mask >> i & 1]
