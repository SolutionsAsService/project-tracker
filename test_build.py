"""Self-check for build.py without network: python3 -m unittest test_build"""
import datetime as dt, unittest
from unittest import mock
import build

NOW = dt.datetime(2026, 10, 13, tzinfo=dt.timezone.utc)
LIVE = {"visibility": "public", "url": "u", "description": None, "stars": 1, "open_prs": 0, "open_issues": 2, "languages": ["Python"],
        "head": "abc1234", "head_date": "2026-09-01T00:00:00Z", "head_subject": "secret commit msg", "ci": "success", "ci_url": None,
        "milestones": [{"title": "M1", "open": 1, "closed": 3, "due_on": None}]}
SECRET = {"id": "p", "name": "P", "repo": "o/p", "visibility": "private", "one_line": "ok", "rag": "green", "state": "doing",
          "north_star": "internal", "next_actions": [{"action": "internal"}], "milestone": {"exit_test": "internal"}, "local": "/x"}


def run(projects, tokens, live=LIVE):
    with mock.patch.object(build, "fetch_live", return_value=live) as f:
        return build.build([{"portfolio": "G", "stale_days": 14, "projects": projects}], tokens, NOW), f


class T(unittest.TestCase):
    def test_private_default_is_public_safe(self):
        for opt_in, token in ((False, "t"), (True, None), (False, None)):
            data, f = run([dict(SECRET, show_private_details=opt_in)], {"public": "g", "private": token})
            p = data["projects"][0]
            f.assert_not_called()
            self.assertEqual(p["details"], "public-safe")
            self.assertNotIn("internal", str(p))
            self.assertNotIn("repo", p)
            self.assertIsNone(p["live"])
            self.assertEqual(p["group"], "G")

    def test_private_opt_in_with_token(self):
        data, f = run([dict(SECRET, show_private_details=True)], {"public": "g", "private": "t"})
        f.assert_called_once_with("o/p", "t")
        self.assertEqual(data["projects"][0]["details"], "full")
        self.assertNotIn("local", data["projects"][0])

    def test_public_marked_but_private_on_github_is_stripped(self):
        data, _ = run([dict(SECRET, visibility="public")], {"public": "g", "private": "t"}, dict(LIVE, visibility="private"))
        p = data["projects"][0]
        self.assertEqual(p["details"], "public-safe")
        self.assertNotIn("secret", str(p))

    def test_public_progress_and_stale(self):
        data, _ = run([{"id": "a", "name": "A", "repo": "o/a", "visibility": "public"}], {"public": "g", "private": None})
        p = data["projects"][0]
        self.assertEqual((p["progress"], p["progress_source"]), (75, "github-milestone:M1"))
        self.assertTrue(p["stale"])
        self.assertEqual(p["days_since_commit"], 42)
        data, _ = run([{"id": "a", "name": "A", "repo": "o/a", "progress": 10}], {"public": "g", "private": None})
        self.assertEqual(data["projects"][0]["progress_source"], "manual")

    def test_ci_summary(self):
        c = lambda s, k="completed": {"status": k, "conclusion": s}
        self.assertEqual(build.ci_summary([]), "none")
        self.assertEqual(build.ci_summary([c("success"), c(None, "in_progress")]), "pending")
        self.assertEqual(build.ci_summary([c("success"), c("failure")]), "failure")
        self.assertEqual(build.ci_summary([c("success"), c("skipped")]), "success")


if __name__ == "__main__":
    unittest.main()
