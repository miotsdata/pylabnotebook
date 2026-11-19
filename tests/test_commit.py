"""Run with: pdm run pytest"""
import os
import subprocess

from pylabnotebook.commit import commit_labnotebook, NOTEBOOK_AUTHOR_EMAIL
from pylabnotebook.export import get_commits


def count_commits(ignored_authors):
    return len(get_commits(False, ignored_authors, [".html"], []))


def test_notebook_commits_are_ignored(tmp_path):
    os.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], check = True)
    subprocess.run(["git", "config", "user.name", "tester"], check = True)
    subprocess.run(["git", "config", "user.email", "tester@example.org"], check = True)
    subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "analysis"], check = True)
    with open("notebook.html", "w", encoding = "utf-8") as notebook_file:
        notebook_file.write("<html></html>")
    commit_labnotebook("notebook.html")

    assert count_commits([]) == 2
    assert count_commits([NOTEBOOK_AUTHOR_EMAIL]) == 1
    assert count_commits(["tester"]) == 1
