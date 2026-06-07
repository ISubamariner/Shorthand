from checker.teeline import decompose, decompose_to_letters, resolve_special_outline

KNOWN_GROUPINGS = [
    "ABT", "ANY", "AS", "BD", "BT", "CD", "CHF", "CM", "CR", "CV",
    "DB", "DR", "FB", "FL", "FM", "FR", "FW", "HV", "IF", "IS",
    "IT", "MB", "MN", "MNY", "MR", "NO", "NV", "NW", "OM",
    "ON", "OTHR", "PV", "RF", "SD", "SE", "SHE", "SM", "SN", "SO",
    "TB", "THS", "TLN", "TR/THR", "US", "VN", "WF", "WN", "WR", "WRD", "WS",
]


class TestPhoneticSubstitutions:
    def test_ph_becomes_f(self):
        result = decompose("phase")
        letters = "".join(c["letter"] for c in result)
        assert "F" in letters
        assert "P" not in letters
        assert "H" not in letters

    def test_qu_becomes_q(self):
        result = decompose("queen")
        letters = "".join(c["letter"] for c in result)
        assert letters[0] == "Q"
        assert "U" not in letters


class TestSilentLetters:
    def test_silent_k_in_know(self):
        result = decompose("know")
        letters = "".join(c["letter"] for c in result)
        assert letters[0] == "N"

    def test_silent_w_in_write(self):
        result = decompose("write")
        letters = "".join(c["letter"] for c in result)
        assert letters[0] == "R"


class TestDoubleLetterReduction:
    def test_double_l(self):
        result = decompose("tall")
        letters = "".join(c["letter"] for c in result)
        assert letters.count("L") == 1

    def test_double_s(self):
        result = decompose("pass")
        letters = "".join(c["letter"] for c in result)
        assert letters.count("S") == 1


class TestInteriorVowelDropping:
    def test_keeps_leading_vowel(self):
        result = decompose("about")
        letters = "".join(c["letter"] for c in result)
        assert letters[0] == "A"

    def test_keeps_trailing_vowel(self):
        result = decompose("go")
        letters = "".join(c["letter"] for c in result)
        assert letters[-1] == "O"

    def test_drops_interior_vowels(self):
        result = decompose("people")
        letters = "".join(c["letter"] for c in result)
        assert letters == "PPL"

    def test_single_consonant_word(self):
        result = decompose("be")
        letters = "".join(c["letter"] for c in result)
        assert letters == "B"


class TestBlendDetection:
    def test_sh_blend(self):
        result = decompose("ship")
        s_comp = next(c for c in result if c["letter"] == "S")
        h_comp = next(c for c in result if c["letter"] == "H")
        assert s_comp["blend_with"] == "H"
        assert h_comp["blend_with"] == "S"

    def test_th_blend(self):
        result = decompose("the")
        t_comp = next(c for c in result if c["letter"] == "T")
        assert t_comp["blend_with"] == "H"


class TestRDoubling:
    def test_dr_doubling(self):
        result = decompose("drive")
        d_comp = next(c for c in result if c["letter"] == "D")
        assert d_comp["is_doubled_for_r"] is True

    def test_tr_doubling(self):
        result = decompose("tree")
        t_comp = next(c for c in result if c["letter"] == "T")
        assert t_comp["is_doubled_for_r"] is True


class TestPositionIndexing:
    def test_positions_sequential(self):
        result = decompose("the")
        positions = [c["position"] for c in result]
        assert positions == list(range(len(result)))


class TestComponentStructure:
    def test_returns_list_of_dicts(self):
        result = decompose("go")
        assert isinstance(result, list)
        assert all(isinstance(c, dict) for c in result)
        assert all("letter" in c for c in result)
        assert all("blend_with" in c for c in result)
        assert all("is_doubled_for_r" in c for c in result)
        assert all("position" in c for c in result)


class TestGreedyDecomposition:
    def test_simple_word_uses_grouping(self):
        result = decompose("command", known_groupings=KNOWN_GROUPINGS)
        letters = [c["letter"] for c in result]
        assert "CM" in letters

    def test_greedy_picks_longest_match(self):
        result = decompose("money", known_groupings=KNOWN_GROUPINGS)
        letters = [c["letter"] for c in result]
        assert "MNY" in letters

    def test_no_grouping_falls_back_to_individual(self):
        result = decompose("dog", known_groupings=KNOWN_GROUPINGS)
        letters = [c["letter"] for c in result]
        assert letters == ["D", "G"]

    def test_mixed_grouping_and_individual(self):
        result = decompose("discover", known_groupings=KNOWN_GROUPINGS)
        letters = [c["letter"] for c in result]
        assert "CV" in letters

    def test_empty_groupings_list_falls_back(self):
        result = decompose("command", known_groupings=[])
        letters = [c["letter"] for c in result]
        assert all(len(l) == 1 for l in letters)

    def test_none_groupings_backward_compatible(self):
        result = decompose("command")
        letters = [c["letter"] for c in result]
        assert all(len(l) == 1 for l in letters)

    def test_decompose_to_letters_passes_groupings(self):
        result = decompose_to_letters("command", known_groupings=KNOWN_GROUPINGS)
        assert "CM" in result


class TestSpecialOutlineResolution:
    def test_known_special_outline(self):
        specials = {"business": "BS", "account": "AC"}
        result = resolve_special_outline("business", specials)
        assert result is not None
        assert result["letter"] == "BS"
        assert result["is_special_outline"] is True

    def test_unknown_word(self):
        result = resolve_special_outline("xylophone", {"business": "BS"})
        assert result is None

    def test_case_insensitive(self):
        result = resolve_special_outline("Business", {"business": "BS"})
        assert result is not None

    def test_no_specials_dict(self):
        result = resolve_special_outline("business")
        assert result is None
