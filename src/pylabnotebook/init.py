"""
INIT MODULE

This module contains notebook init functions.
"""

import subprocess
import os
import re
from jinja2 import Environment, FileSystemLoader

from .exceptions import NotGitRepoError
from .commit import NOTEBOOK_AUTHOR_EMAIL

# useful values
GREEN: str = '\033[0;32m'
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
    environment = Environment(loader=FileSystemLoader(f"{SCRIPT_DIR}/templates/"), keep_trailing_newline = True)
    template = environment.get_template("rc")
    content = template.render(name = name,
                              author = author,
                              remote_url = remote_url,
                              notebook_author_email = NOTEBOOK_AUTHOR_EMAIL)

    with open(".labnotebookrc", mode="w", encoding="utf-8") as config:
        config.write(content)


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
