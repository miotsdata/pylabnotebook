"""Run with: PYTHONPATH=src python3 -m pytest tests"""
import os
import subprocess

from pylabnotebook.export import export_labnotebook
from pylabnotebook.init import init_labnotebook


def git(*git_arguments):
    return subprocess.run(["git", *git_arguments], check = True, capture_output = True, text = True).stdout


def make_repository(repository_dir):
    os.chdir(repository_dir)
    git("init", "-q")
    git("config", "user.name", "tester")
    git("config", "user.email", "tester@example.org")
    init_labnotebook("demo")


def commit_file(file_path, content, message):
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok = True)
    with open(file_path, "w", encoding = "utf-8") as file_handle:
        file_handle.write(content)
    git("add", "-A")
    git("commit", "-q", "-m", message)


def export_html(output_file = "notebook.html", **export_options):
    export_labnotebook(output_file, force = True, link = True, **export_options)
    with open(output_file, encoding = "utf-8") as notebook_file:
        return notebook_file.read()


def test_commit_text_is_escaped(tmp_path):
    make_repository(tmp_path)
    commit_file("a.txt", "a", "fix a<b\n\nline one\nline two <script>")
    notebook_html = export_html()
    assert "fix a&lt;b" in notebook_html
    assert "<script>alert" not in notebook_html and "&lt;script&gt;" in notebook_html
    assert "line one\nline two" in notebook_html


def test_analysis_ignore_uses_wildcards():
    from pylabnotebook.export import is_ignored
    assert is_ignored("reports/a.html", ["*.html"])
    assert is_ignored("old/reports/a.html", ["reports/"])
    assert is_ignored("draft_a.html", ["draft_*"])
    assert not is_ignored("reports/a.html", ["*.txt", "old"])


def test_analysis_ext_matches_suffix_only(tmp_path):
    make_repository(tmp_path)
    commit_file("report.html", "r", "report")
    commit_file("report.html.bak", "b", "backup")
    notebook_html = export_html()
    assert 'href="report.html"' in notebook_html
    assert 'href="report.html.bak"' not in notebook_html
