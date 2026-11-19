"""
EXPORT MODULE

This module contains notebook export functions.
"""

# pylint: disable=line-too-long

import subprocess
import os
import yaml
from fnmatch import fnmatch
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from .exceptions import NotGitRepoError, NotInitializedError, OutputAlreadyExistsError, EmptyHisoryError
from .commit import NOTEBOOK_AUTHOR_EMAIL

# useful values
RED: str = '\033[0;31m'
NCOL: str = '\033[0m'
SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))

def export_labnotebook(output_file: str, force: bool, link: bool) -> None:
    """Export labnotebook to html.

    This function exports the labnotebook into a single html file ready to read and share.

    :param output_file: path of the file to create
    :type output_file: str
    :param force: whether to force the overwriting of output_file if exists.
    :type force: bool
    :param link: whether to create links to analysis files in analysis files bullet list. These links can be used to open the analysis files directly from the notebook. # pylint: disable=line-too-long
    :type link: bool

    """

    # 1. Go to git root dir
    try:
        git_root: str = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                        universal_newlines = True, stderr=subprocess.PIPE).strip()
    except subprocess.CalledProcessError:
        raise NotGitRepoError("fatal: not a git repository (or any of the parent directories): .git") from None

    os.chdir(git_root)

    # 2. Check for .labnotebookrc
    if not os.path.exists(".labnotebookrc"):
        raise NotInitializedError(f"{RED}Error: There is no .labnotebookrc file in git repository root folder. Please, run labnotebook create -n <name_of_the_project>{NCOL}")

    with open(".labnotebookrc", "r", encoding = 'utf8') as config_file:
        config: dict = yaml.safe_load(config_file)

    # 3. Check if file already exists and force is False
    if os.path.exists(output_file) and not force:
        raise OutputAlreadyExistsError(f"{RED}Error: {output_file} already exists. Use -f/--force to overwrite it.{NCOL}")

    # 5. Get commits
    # Old .labnotebookrc files have no IGNORE_AUTHORS: still skip `labnotebook commit` commits
    commits: list[dict] = get_commits(reverse_history = config.get("REVERSE_HISTORY"),
                                      ignored_authors = config.get("IGNORE_AUTHORS", [NOTEBOOK_AUTHOR_EMAIL]) or [],
                                      analysis_ext = config.get("ANALYSIS_EXT") or [],
                                      excluded_patterns = config.get("ANALYSIS_IGNORE") or [])

    # 6. Read style.css
    with open(config.get('LAB_CSS'), 'r', encoding='utf-8') as css_file:
        style_css = css_file.read()

    environment = Environment(loader=FileSystemLoader(f"{SCRIPT_DIR}/templates/"), autoescape = True)
    template = environment.get_template("base.html")
    content = template.render(config = config,
                              create_date = datetime.today().strftime('%Y-%m-%d'),
                              link = link,
                              commits = commits,
                              style_css = style_css)

    with open(output_file, mode="w", encoding="utf-8") as message:
        message.write(content)
        print(f"Notebook succesfully exported to {output_file}.")


# Field/record separators that cannot appear in commit metadata
FIELD_SEPARATOR: str = "\x1f"
RECORD_SEPARATOR: str = "\x1e"
LOG_FIELDS: list[str] = ["sha", "author", "author_email", "date", "title", "message"]


def get_commits(reverse_history: bool, ignored_authors: list[str], analysis_ext: list[str],
                excluded_patterns: list[str]) -> list[dict]:
    """Get the commits to show in the notebook, with a single git log call.

    :param reverse_history: Whether commits should be returned from first to last.
    :type reverse_history: bool
    :param ignored_authors: author names or emails whose commits are left out of the notebook.
    :type ignored_authors: list[str]
    :param analysis_ext: list of the file extensions used as reference for analysis files.
    :type analysis_ext: list[str]
    :param excluded_patterns: list of the pattern to be excluded from the analysis files.
    :type excluded_patterns: list[str]
    :return: one dict per commit with sha, short_sha, author, author_email, date, title, message,
        changed_files (list of dicts with status, path, old_path) and analysis_files.
    :rtype: list[dict]
    """
    log_format: str = "%x1e" + "%x1f".join(["%H", "%an", "%ae", "%cs", "%s", "%b"]) + "%x1f"
    git_command: list[str] = ["git", "log", "-z", "--raw", "--no-abbrev", f"--format={log_format}"]
    if reverse_history:
        git_command.append("--reverse")

    try:
        git_log: str = subprocess.check_output(git_command, text = True, stderr = subprocess.PIPE)
    except subprocess.CalledProcessError:
        raise EmptyHisoryError(f"{RED}Error: Git history is empty{NCOL}") from None

    ignored_authors = set(ignored_authors)
    commits: list[dict] = []
    for commit_record in git_log.split(RECORD_SEPARATOR)[1:]:
        *field_values, raw_changes = commit_record.split(FIELD_SEPARATOR, len(LOG_FIELDS))
        commit: dict = dict(zip(LOG_FIELDS, field_values))
        if commit["author"] in ignored_authors or commit["author_email"] in ignored_authors:
            continue
        commit["short_sha"] = commit["sha"][:7]
        commit["message"] = commit["message"].strip()
        commit["changed_files"] = parse_raw_changes(raw_changes)
        commit["analysis_files"] = [changed_file["path"] for changed_file in commit["changed_files"]
                                    if changed_file["status"] != "D" and
                                    changed_file["path"].endswith(tuple(analysis_ext)) and
                                    os.path.isfile(changed_file["path"]) and
                                    not is_ignored(changed_file["path"], excluded_patterns)]
        commits.append(commit)

    return commits


def parse_raw_changes(raw_changes: str) -> list[dict]:
    """Parse the NUL separated output of git log -z --raw for one commit.

    Each change is ``:<modes> <blobs> <status>\\0<path>\\0``, with two paths for renames/copies.

    :param raw_changes: raw changes of one commit.
    :type raw_changes: str
    :return: list of dicts with status (one letter), path, old_path (None unless renamed/copied)
        and blob (the new blob id).
    :rtype: list[dict]
    """
    raw_tokens: list[str] = raw_changes.lstrip("\0\n").split("\0")
    changed_files: list[dict] = []
    token_index: int = 0
    while token_index < len(raw_tokens) and raw_tokens[token_index].startswith(":"):
        _, _, _, new_blob, status = raw_tokens[token_index].split(" ")
        if status[0] in "RC":
            old_path, new_path = raw_tokens[token_index + 1], raw_tokens[token_index + 2]
            token_index += 3
        else:
            old_path, new_path = None, raw_tokens[token_index + 1]
            token_index += 2
        changed_files.append({"status": status[0], "path": new_path, "old_path": old_path,
                              "blob": new_blob})
    return changed_files


def is_ignored(file_path: str, ignore_patterns: list[str]) -> bool:
    """Check file_path against gitignore-like wildcard patterns.

    A pattern matches the whole path, any path component (``*.tmp``, ``old_reports``) or any
    folder (``old_reports/``, ``reports/2023``).

    :param file_path: path relative to the git root, with / separators.
    :type file_path: str
    :param ignore_patterns: wildcard patterns (``*``, ``?``, ``[]``).
    :type ignore_patterns: list[str]
    :return: whether file_path matches any pattern.
    :rtype: bool
    """
    for ignore_pattern in ignore_patterns:
        ignore_pattern = ignore_pattern.strip("/")
        if any(fnmatch(file_path, candidate) for candidate in
               (ignore_pattern, f"{ignore_pattern}/*", f"*/{ignore_pattern}", f"*/{ignore_pattern}/*")):
            return True
    return False
