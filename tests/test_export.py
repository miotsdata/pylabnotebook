"""Run with: pdm run pytest"""
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


def test_renames_and_non_ascii_paths(tmp_path):
    make_repository(tmp_path)
    commit_file("café.html", "content", "add report")
    git("mv", "café.html", "renamed.html")
    git("commit", "-q", "-m", "rename report")
    notebook_html = export_html()
    assert "café.html &rarr; renamed.html" in notebook_html
    assert 'href="renamed.html"' in notebook_html
    assert notebook_html.count('class="commit-el"') == 2


def test_date_is_author_date(tmp_path):
    make_repository(tmp_path)
    os.environ["GIT_AUTHOR_DATE"] = "2020-01-02T10:00:00"
    try:
        commit_file("a.txt", "a", "old work")
    finally:
        del os.environ["GIT_AUTHOR_DATE"]
    git("commit", "-q", "--amend", "--no-edit")  # rewriting changes the committer date only
    assert ">2020-01-02</h2>" in export_html()


def test_output_relative_to_cwd_and_links_relative_to_output(tmp_path):
    make_repository(tmp_path)
    commit_file("reports/a.html", "a", "report")
    os.makedirs("docs")
    os.chdir("docs")
    export_labnotebook("notebook.html", force = True, link = True)
    notebook_html = (tmp_path / "docs" / "notebook.html").read_text(encoding = "utf-8")
    assert 'href="../reports/a.html"' in notebook_html
    assert not (tmp_path / "notebook.html").exists()


def test_custom_and_default_css(tmp_path):
    make_repository(tmp_path)
    commit_file("a.txt", "a", "work")
    assert "#bottom-btn" in export_html()
    commit_file("my.css", "body { color: purple; }", "css")
    with open(".labnotebookrc", "a", encoding = "utf-8") as config_file:
        config_file.write("LAB_CSS: my.css\n")
    assert "color: purple" in export_html()


def test_analysis_file_changed_later_is_flagged(tmp_path):
    make_repository(tmp_path)
    commit_file("a.html", "first", "first version")
    commit_file("a.html", "second", "second version")
    assert export_html().count("changed in a later commit") == 1


def test_init_without_git_user_name(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    os.chdir(tmp_path)
    git("init", "-q")
    init_labnotebook("demo")
    assert os.path.exists(".labnotebookrc")


def test_history_filters(tmp_path):
    make_repository(tmp_path)
    commit_file("analyses/a.txt", "a", "in analyses")
    commit_file("other.txt", "o", "outside analyses")
    git("checkout", "-q", "-b", "feature")
    commit_file("feature.txt", "f", "on feature")
    git("checkout", "-q", "-")
    assert "outside analyses" not in export_html(paths = ["analyses"])
    assert "on feature" not in export_html()
    assert "on feature" in export_html(branch = "feature")
    assert 'class="commit-el"' not in export_html(since = "2090-01-01")


def test_ignore_messages(tmp_path):
    make_repository(tmp_path)
    commit_file("a.txt", "a", "real work")
    commit_file("b.txt", "b", "wip: half done")
    with open(".labnotebookrc", "a", encoding = "utf-8") as config_file:
        config_file.write("IGNORE_MESSAGES: ['^wip']\n")
    notebook_html = export_html()
    assert "real work" in notebook_html and "half done" not in notebook_html


def test_remote_url(tmp_path):
    os.chdir(tmp_path)
    git("init", "-q")
    git("remote", "add", "origin", "git@github.com:someone/project.git")
    from pylabnotebook.init import get_remote_web_url
    assert get_remote_web_url() == "https://github.com/someone/project"
    git("remote", "set-url", "origin", "https://user:token@gitlab.com/someone/project.git")
    assert get_remote_web_url() == "https://gitlab.com/someone/project"
    git("config", "user.name", "tester")
    git("config", "user.email", "tester@example.org")
    init_labnotebook("demo")
    commit_file("my report.html", "first", "first version")
    commit_file("my report.html", "second", "second version")
    notebook_html = export_html()
    first_sha = git("rev-list", "--max-parents=0", "HEAD").strip()
    assert f"https://gitlab.com/someone/project/commit/{first_sha}" in notebook_html
    assert f"https://gitlab.com/someone/project/blob/{first_sha}/my%20report.html" in notebook_html
