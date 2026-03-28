import unittest
from types import SimpleNamespace

from adapters.imdb.imdb_adapter import IMDBAdapter


class IMDBAdapterSearchRankingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = IMDBAdapter()
        self.addCleanup(self.adapter.executor.shutdown, wait=False)

    def test_derivative_titles_are_demoted_for_base_query(self) -> None:
        results = [
            SimpleNamespace(title="All of Us Are Dead Roblox", kind="tvSeries"),
            SimpleNamespace(title="Jigeum uri hakgyoneun", kind="tvSeries"),
        ]

        ranked = self.adapter._rank_search_results("All of Us Are Dead", results)

        self.assertEqual("Jigeum uri hakgyoneun", ranked[0].title)

    def test_exact_derivative_query_keeps_exact_match_first(self) -> None:
        results = [
            SimpleNamespace(title="All of Us Are Dead Roblox", kind="tvSeries"),
            SimpleNamespace(title="Jigeum uri hakgyoneun", kind="tvSeries"),
        ]

        ranked = self.adapter._rank_search_results("All of Us Are Dead Roblox", results)

        self.assertEqual("All of Us Are Dead Roblox", ranked[0].title)

    def test_live_event_suffix_is_demoted(self) -> None:
        penalty = self.adapter._search_result_penalty(
            "Crash Landing on You",
            "Crash Landing on You: Live in Seoul",
            "movie",
        )

        self.assertGreater(penalty, 0)
