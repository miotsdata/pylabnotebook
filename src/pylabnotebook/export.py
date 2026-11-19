"""
EXPORT MODULE

This module contains notebook export functions.
"""

# pylint: disable=line-too-long

import subprocess
import os
import re
import yaml
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from .exceptions import NotGitRepoError, NotInitializedError, OutputAlreadyExistsError, EmptyHistoryError, InvalidConfigError
from .commit import NOTEBOOK_AUTHOR_EMAIL
from .version import __version__

# useful values
RED: str = '\033[0;31m'
NCOL: str = '\033[0m'
SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IMAGE_EXT: list[str] = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']

def export_labnotebook(output_file: str, force: bool, link: bool, since: str = None, until: str = None,
                       branch: str = None, paths: list[str] = None) -> None:
    """Export labnotebook to html.

    This function exports the labnotebook into a single html file ready to read and share.

    :param output_file: path of the file to create
    :type output_file: str
    :param force: whether to force the overwriting of output_file if exists.
    :type force: bool
    :param link: whether to create links to analysis files in analysis files bullet list. These links can be used to open the analysis files directly from the notebook. # pylint: disable=line-too-long
    :type link: bool
    :param since: only commits more recent than this date (any git date, eg. 2024-01-31 or "2 weeks ago").
    :type since: str
    :param until: only commits older than this date.
    :type until: str
    :param branch: branch, tag or revision range to export instead of the current branch.
    :type branch: str
    :param paths: only commits changing these files/folders (relative to the current folder).
    :type paths: list[str]
    """

    # 1. Go to git root dir (output_file is relative to where the command is run)
    output_path: str = os.path.abspath(output_file)
    log_arguments: list[str] = []
    if since:
        log_arguments.append(f"--since={since}")
    if until:
        log_arguments.append(f"--until={until}")
    if branch:
        log_arguments.append(branch)
    if paths:
        log_arguments += ["--full-diff", "--", *(os.path.abspath(path) for path in paths)]
    try:
        git_root: str = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                        universal_newlines = True, stderr=subprocess.PIPE).strip()
    except subprocess.CalledProcessError:
        raise NotGitRepoError("fatal: not a git repository (or any of the parent directories): .git") from None

    os.chdir(git_root)

    # 2. Check for .labnotebookrc
    if not os.path.exists(".labnotebookrc"):
        raise NotInitializedError(f"{RED}Error: There is no .labnotebookrc file in git repository root folder. Please, run labnotebook init -n <name_of_the_project>{NCOL}")

    with open(".labnotebookrc", "r", encoding = 'utf8') as config_file:
        config: dict = yaml.safe_load(config_file)
    check_regex_options(config)

    # 3. Check if file already exists and force is False
    if os.path.exists(output_path) and not force:
        raise OutputAlreadyExistsError(f"{RED}Error: {output_file} already exists. Use -f/--force to overwrite it.{NCOL}")

    # 5. Get commits
    # Old .labnotebookrc files have no IGNORE_AUTHORS: still skip `labnotebook commit` commits
    commits: list[dict] = get_commits(reverse_history = config.get("REVERSE_HISTORY"),
                                      ignored_authors = config.get("IGNORE_AUTHORS", [NOTEBOOK_AUTHOR_EMAIL]) or [],
                                      ignored_messages = config.get("IGNORE_MESSAGES") or [],
                                      analysis_ext = config.get("ANALYSIS_EXT") or [],
                                      excluded_patterns = config.get("ANALYSIS_IGNORE") or [],
                                      image_ext = config.get("IMAGE_EXT", DEFAULT_IMAGE_EXT) or [],
                                      log_arguments = log_arguments)

    # Links must work from the folder the notebook is saved in
    output_dir: str = os.path.dirname(output_path)
    for commit in commits:
        for changed_file in commit["changed_files"]:
            changed_file["href"] = os.path.relpath(changed_file["path"], output_dir).replace(os.sep, "/")

    # 6. Read style.css. Old .labnotebookrc files point to the css of the install that created them
    lab_css: str = config.get("LAB_CSS") or ""
    if not lab_css or is_bundled_css_path(lab_css):
        lab_css = f"{SCRIPT_DIR}/templates/style.css"
    with open(lab_css, 'r', encoding='utf-8') as css_file:
        style_css = css_file.read()

    environment = Environment(loader=FileSystemLoader(f"{SCRIPT_DIR}/templates/"), autoescape = True)
    template = environment.get_template("base.html")
    content = template.render(config = config,
                              create_date = datetime.today().strftime('%Y-%m-%d'),
                              link = link,
                              commits = commits,
                              style_css = style_css,
                              version = __version__,
                              remote_url = (config.get("REMOTE_URL") or "").rstrip("/"))

    with open(output_path, mode="w", encoding="utf-8") as message:
        message.write(content)
        print(f"Notebook successfully exported to {output_file}.")


# Field/record separators that cannot appear in commit metadata
FIELD_SEPARATOR: str = "\x1f"
RECORD_SEPARATOR: str = "\x1e"
LOG_FIELDS: list[str] = ["sha", "author", "author_email", "date", "title", "message"]


def get_commits(reverse_history: bool, ignored_authors: list[str], analysis_ext: list[str],
                excluded_patterns: list[str], log_arguments: list[str] = (),
                ignored_messages: list[str] = (), image_ext: list[str] = ()) -> list[dict]:
    """Get the commits to show in the notebook, with a single git log call.

    :param reverse_history: Whether commits should be returned from first to last.
    :type reverse_history: bool
    :param ignored_authors: author names or emails whose commits are left out of the notebook.
    :type ignored_authors: list[str]
    :param analysis_ext: list of the file extensions used as reference for analysis files.
    :type analysis_ext: list[str]
    :param excluded_patterns: list of the pattern to be excluded from the analysis files.
    :type excluded_patterns: list[str]
    :param log_arguments: extra git log arguments (filters, revision, -- paths), appended last.
    :type log_arguments: list[str]
    :param ignored_messages: regular expressions: commits whose title matches any are left out.
    :type ignored_messages: list[str]
    :param image_ext: extensions of the images to show as thumbnails (only if unchanged since).
    :type image_ext: list[str]
    :return: one dict per commit with sha, short_sha, tags, author, author_email, date, title, message,
        changed_files (list of dicts, see parse_raw_changes), analysis_files and images (subsets of
        changed_files).
    :rtype: list[dict]
    """
    log_format: str = "%x1e" + "%x1f".join(["%H", "%an", "%ae", "%as", "%s", "%b"]) + "%x1f"
    git_command: list[str] = ["git", "log", "-z", "--raw", "--no-abbrev", "--author-date-order", f"--format={log_format}"]
    if reverse_history:
        git_command.append("--reverse")
    git_command += log_arguments

    try:
        git_log: str = subprocess.check_output(git_command, text = True, stderr = subprocess.PIPE)
    except subprocess.CalledProcessError:
        raise EmptyHistoryError(f"{RED}Error: Git history is empty{NCOL}") from None

    # Blob of each file in HEAD, to tell whether a link still shows the version of that commit
    head_files: list[str] = subprocess.check_output(["git", "ls-tree", "-r", "-z", "HEAD"], text = True).split("\0")
    head_blobs: dict = {tree_entry.split("\t", 1)[1]: tree_entry.split()[2] for tree_entry in head_files if tree_entry}

    # Tags by commit (%(*objectname) is the commit of annotated tags)
    tag_refs: list[str] = subprocess.check_output(["git", "for-each-ref", "refs/tags",
                                                   "--format=%(objectname) %(*objectname) %(refname:short)"],
                                                  text = True).splitlines()
    tags_by_sha: dict = {}
    for tag_ref in tag_refs:
        tag_object, tagged_commit, tag_name = tag_ref.split(" ", 2)
        tags_by_sha.setdefault(tagged_commit or tag_object, []).append(tag_name)

    ignored_authors = set(ignored_authors)
    commits: list[dict] = []
    for commit_record in git_log.split(RECORD_SEPARATOR)[1:]:
        *field_values, raw_changes = commit_record.split(FIELD_SEPARATOR, len(LOG_FIELDS))
        commit: dict = dict(zip(LOG_FIELDS, field_values))
        if commit["author"] in ignored_authors or commit["author_email"] in ignored_authors:
            continue
        if any(re.search(message_pattern, commit["title"]) for message_pattern in ignored_messages):
            continue
        commit["short_sha"] = commit["sha"][:7]
        commit["tags"] = tags_by_sha.get(commit["sha"], [])
        commit["message"] = commit["message"].strip()
        commit["changed_files"] = parse_raw_changes(raw_changes)
        for changed_file in commit["changed_files"]:
            changed_file["changed_later"] = head_blobs.get(changed_file["path"]) != changed_file["blob"]
        shown_files: list[dict] = [changed_file for changed_file in commit["changed_files"]
                                   if changed_file["status"] != "D" and
                                   not is_ignored(changed_file["path"], excluded_patterns)]
        commit["analysis_files"] = [changed_file for changed_file in shown_files
                                    if changed_file["path"].endswith(tuple(analysis_ext)) and
                                    os.path.isfile(changed_file["path"])]
        # A thumbnail of a later version would be misleading
        commit["images"] = [changed_file for changed_file in shown_files
                            if changed_file["path"].lower().endswith(tuple(image_ext)) and
                            not changed_file["changed_later"]]
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
    """Check file_path against regular expressions (re.search, so they match anywhere in the path).

    :param file_path: path relative to the git root, with / separators.
    :type file_path: str
    :param ignore_patterns: regular expressions, eg. ``^old/`` or ``\\.tmp\\.html$``.
    :type ignore_patterns: list[str]
    :return: whether file_path matches any pattern.
    :rtype: bool
    """
    return any(re.search(ignore_pattern, file_path) for ignore_pattern in ignore_patterns)


def check_regex_options(config: dict) -> None:
    """Raise a readable error for invalid regular expressions in the config.

    :param config: content of .labnotebookrc.
    :type config: dict
    :raises InvalidConfigError: if a pattern of ANALYSIS_IGNORE or IGNORE_MESSAGES is not a valid regex.
    """
    for option_name in ("ANALYSIS_IGNORE", "IGNORE_MESSAGES"):
        for pattern in config.get(option_name) or []:
            try:
                re.compile(pattern)
            except re.error as regex_error:
                raise InvalidConfigError(f"{RED}Error: {option_name} in .labnotebookrc: {pattern!r} is not a valid regular expression ({regex_error}). Patterns are regular expressions, eg. '\\.tmp\\.html$' instead of '*.tmp.html'.{NCOL}") from None


def is_bundled_css_path(lab_css: str) -> bool:
    """Whether lab_css is the absolute path of the bundled css that old versions wrote in .labnotebookrc.

    :param lab_css: LAB_CSS value.
    :type lab_css: str
    :rtype: bool
    """
    return lab_css.replace(os.sep, "/").endswith("pylabnotebook/templates/style.css")
