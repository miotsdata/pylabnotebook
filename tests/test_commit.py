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


def test_export_with_commit_flag(tmp_path, monkeypatch):
    from pylabnotebook.cli import main
    from pylabnotebook.init import init_labnotebook
    os.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], check = True)
    subprocess.run(["git", "config", "user.name", "tester"], check = True)
    subprocess.run(["git", "config", "user.email", "tester@example.org"], check = True)
    init_labnotebook("demo")
    subprocess.run(["git", "add", "-A"], check = True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], check = True)
    os.makedirs("docs")
    os.chdir("docs")
    monkeypatch.setattr("sys.argv", ["labnotebook", "export", "-o", "notebook.html", "--commit"])
    main()
    last_commit = subprocess.check_output(["git", "log", "-1", "--format=%ae %s", "--name-only"], text = True)
    assert NOTEBOOK_AUTHOR_EMAIL in last_commit and "docs/notebook.html" in last_commit
