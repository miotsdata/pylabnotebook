"""Run with: PYTHONPATH=src python3 -m pytest tests (or python3 tests/test_commit.py)."""
import os
import subprocess
import tempfile

from pylabnotebook.commit import commit_labnotebook, NOTEBOOK_AUTHOR_EMAIL
from pylabnotebook.export import get_commits


def test_notebook_commits_are_ignored():
    with tempfile.TemporaryDirectory() as repository_dir:
        os.chdir(repository_dir)
        subprocess.run(["git", "init", "-q"], check = True)
        subprocess.run(["git", "config", "user.name", "tester"], check = True)
        subprocess.run(["git", "config", "user.email", "tester@example.org"], check = True)
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "analysis"], check = True)
        with open("notebook.html", "w", encoding = "utf-8") as notebook_file:
            notebook_file.write("<html></html>")
        commit_labnotebook("notebook.html")

        def count_commits(ignored_authors):
            return len(get_commits(False, ignored_authors, [".html"], []))
        assert count_commits([]) == 2
        assert count_commits([NOTEBOOK_AUTHOR_EMAIL]) == 1
        assert count_commits(["tester"]) == 1


if __name__ == "__main__":
    test_notebook_commits_are_ignored()
    print("ok")
