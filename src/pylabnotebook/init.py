"""
INIT MODULE

This module contains notebook init functions.
"""

import subprocess
import os
import re
import shutil
import yaml
from jinja2 import Environment, FileSystemLoader

from .exceptions import NotGitRepoError, NotInitializedError, InvalidConfigError
from .export import is_bundled_css_path, check_regex_options
from .commit import NOTEBOOK_AUTHOR_EMAIL

# useful values
GREEN: str = '\033[0;32m'
YELLOW: str = '\033[0;33m'
NCOL: str = '\033[0m'
SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))


def init_labnotebook(name: str) -> None:
    """Create new labnotebook.

    This function creates a new labnotebook by creating a new .labnotebook folder with all the 
    necessary files included.

    :param name: Name of the project.
    :type name: str
    """

    # 1. Go to git root dir
    try:
        git_root: str = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                        universal_newlines = True, stderr=subprocess.PIPE).strip()
    except subprocess.CalledProcessError:
        raise NotGitRepoError("fatal: not a git repository (or any of the parent directories): .git") from None # pylint: disable=line-too-long

    os.chdir(git_root)

    # 2. Get useful variables
    # Empty when git user.name is not set: LAB_AUTHOR can be filled in .labnotebookrc
    author: str = subprocess.run(["git", "config", "--get", "user.name"],
                                 capture_output = True, text = True, check = False).stdout.strip()

    # 3. Create config file
    create_config_json(name = name, author = author, remote_url = get_remote_web_url())

    # 4. Return messages
    print(f"\n{GREEN}Created .labnotebookrc in {git_root}. Please edit it if you want to change labnotebook export behaviour.{NCOL}") # pylint: disable=line-too-long


def create_config_json(name: str, author: str, remote_url: str = "") -> None:
    """Create configuration file.

    This function creates the config.json file of the notebook inside .labnotebook folder.

    :param name: Name of the notebook.
    :type name: str
    :param author: Author of the notebook.
    :type author: str
    :param remote_url: web url of the repository (eg. https://github.com/user/repo).
    :type remote_url: str
    """
    with open(".labnotebookrc", mode="w", encoding="utf-8") as config:
        config.write(render_config(name, author, remote_url))


def render_config(name: str, author: str, remote_url: str = "") -> str:
    """Render the .labnotebookrc template with the default settings.

    :param name: Name of the notebook.
    :type name: str
    :param author: Author of the notebook.
    :type author: str
    :param remote_url: web url of the repository.
    :type remote_url: str
    :return: content of a new .labnotebookrc.
    :rtype: str
    """
    environment = Environment(loader=FileSystemLoader(f"{SCRIPT_DIR}/templates/"), keep_trailing_newline = True)
    template = environment.get_template("rc")
    return template.render(name = name,
                           author = author,
                           remote_url = remote_url,
                           notebook_author_email = NOTEBOOK_AUTHOR_EMAIL)


def get_remote_web_url() -> str:
    """Web url of the origin remote (GitHub/GitLab/... style), empty if there is none.

    :return: eg. https://github.com/user/repo for git@github.com:user/repo.git, without credentials.
    :rtype: str
    """
    remote_url: str = subprocess.run(["git", "remote", "get-url", "origin"],
                                     capture_output = True, text = True, check = False).stdout.strip()
    remote_url = re.sub(r"^(ssh://)?git@([^:/]+)[:/]", r"https://\2/", remote_url)
    remote_url = re.sub(r"^https?://[^@/]+@", "https://", remote_url)  # never write tokens to the rc
    return remote_url.removesuffix(".git") if remote_url.startswith("http") else ""


def upgrade_labnotebook(dry_run: bool = False) -> None:
    """Add the settings introduced by newer versions to .labnotebookrc, keeping the existing ones.

    Missing settings are appended with their default value; existing lines (and comments) are not
    touched, except an old absolute LAB_CSS path to the bundled css, which is emptied. The previous
    file is saved as .labnotebookrc.bak.

    :param dry_run: only print what would change.
    :type dry_run: bool
    """
    try:
        git_root: str = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                                text = True, stderr = subprocess.PIPE).strip()
    except subprocess.CalledProcessError:
        raise NotGitRepoError("fatal: not a git repository (or any of the parent directories): .git") from None # pylint: disable=line-too-long
    os.chdir(git_root)
    if not os.path.exists(".labnotebookrc"):
        raise NotInitializedError("Error: There is no .labnotebookrc file in git repository root folder. Please, run labnotebook init -n <name_of_the_project>") # pylint: disable=line-too-long

    with open(".labnotebookrc", encoding = "utf-8") as config_file:
        old_text: str = config_file.read()
    old_config: dict = yaml.safe_load(old_text) or {}

    default_lines: list[str] = render_config(old_config.get("NOTEBOOK_NAME") or "",
                                             old_config.get("LAB_AUTHOR") or "",
                                             get_remote_web_url()).splitlines()
    added_lines: list[str] = [default_line for default_line in default_lines
                              if default_line.split(":", 1)[0] not in old_config]
    new_text: str = old_text if old_text.endswith("\n") or not old_text else old_text + "\n"
    changes: list[str] = [f"+ {added_line}" for added_line in added_lines]

    if is_bundled_css_path(old_config.get("LAB_CSS") or ""):
        default_css_line: str = next(default_line for default_line in default_lines if default_line.startswith("LAB_CSS:"))
        new_text = re.sub(r"^LAB_CSS:.*$", lambda _: default_css_line, new_text, count = 1, flags = re.MULTILINE)
        changes.append(f"~ {default_css_line}  (was the absolute path of the bundled css)")
    new_text += "".join(f"{added_line}\n" for added_line in added_lines)

    # Not fixable automatically: report invalid patterns
    try:
        check_regex_options(old_config)
    except InvalidConfigError as invalid_config_error:
        print(f"{YELLOW}Warning: {str(invalid_config_error).replace('Error: ', '')}{NCOL}")

    if not changes:
        print(".labnotebookrc is already up to date.")
        return
    print("\n".join(changes))
    if dry_run:
        print("Dry run: .labnotebookrc not changed.")
        return
    shutil.copyfile(".labnotebookrc", ".labnotebookrc.bak")
    with open(".labnotebookrc", mode = "w", encoding = "utf-8") as config_file:
        config_file.write(new_text)
    print(f"{GREEN}Upgraded .labnotebookrc (previous version saved as .labnotebookrc.bak).{NCOL}")
