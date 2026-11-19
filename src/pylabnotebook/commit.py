"""
COMMIT MODULE

This module contains the function to commit the exported notebook under a dedicated git identity,
so that notebook updates can be excluded from the notebook itself (see IGNORE_AUTHORS).
"""

import subprocess

NOTEBOOK_AUTHOR_NAME: str = "labnotebook"
NOTEBOOK_AUTHOR_EMAIL: str = "labnotebook@localhost"


def commit_labnotebook(notebook_file: str, message: str = "Update lab notebook") -> None:
    """Commit the notebook file as the labnotebook user.

    Only notebook_file is committed: anything else already staged is left staged and untouched.

    :param notebook_file: path of the exported notebook to commit.
    :type notebook_file: str
    :param message: commit message.
    :type message: str
    :raises subprocess.CalledProcessError: if git add or git commit fails (e.g. nothing to commit).
    """
    notebook_identity: list[str] = ["-c", f"user.name={NOTEBOOK_AUTHOR_NAME}",
                                    "-c", f"user.email={NOTEBOOK_AUTHOR_EMAIL}"]
    subprocess.run(["git", "add", "--", notebook_file], check = True)
    subprocess.run(["git", *notebook_identity, "commit", "-m", message, "--", notebook_file],
                   check = True)
