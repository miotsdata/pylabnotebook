"""PYLABNOTEBOOK
This module is the cli module where cli functionality of pylabnotebook is defined.
"""

# pylint: disable=line-too-long

import argparse
import os
import subprocess
import sys

from .version import __version__
from .init import init_labnotebook
from .export import export_labnotebook
from .commit import commit_labnotebook, NOTEBOOK_AUTHOR_NAME, NOTEBOOK_AUTHOR_EMAIL
from .exceptions import NotGitRepoError, NotInitializedError, OutputAlreadyExistsError, EmptyHistoryError, InvalidConfigError

def main():
    """Main cli function handler.

    This function is the main function of the module, which handles command line input values to run
    the different functions of the labnotebook.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Lab Notebook Tool")
    parser.add_argument('--version', action = 'version', version = '%(prog)s ' + __version__,
                        help = "Show package version")

    subparsers: argparse._SubParsersAction = parser.add_subparsers(dest = "command")

    init_parser: argparse.ArgumentParser = subparsers.add_parser("init",
                                                                 help = "Init labnotebook by creating .labnotebookrc in git root folder.") # pylint: disable=line-too-long
    init_parser.add_argument("-n", "--name", required = True,
                               help="Name of the lab notebook. If the name should contain more words, wrap them into quotes") # pylint: disable=line-too-long

    export_parser: argparse.ArgumentParser = subparsers.add_parser("export", help = "Export lab notebook to an html file") # pylint: disable=line-too-long
    export_parser.add_argument("-o", "--output", required = True,
                               help = "Path/name of the output HTML file")
    export_parser.add_argument("-f", "--force",
                               help = "Force the overwriting of the output file if already present",
                               default = False, action = "store_true")
    export_parser.add_argument("--no-link", default = False, action = "store_true",
                               help = "Disable links to analyses files.") # pylint: disable=line-too-long
    export_parser.add_argument("-c", "--commit", default = False, action = "store_true",
                               help = "Commit the exported notebook (same as labnotebook commit)")
    export_parser.add_argument("--since", help = "Only commits more recent than this date (eg. 2024-01-31 or '2 weeks ago')")
    export_parser.add_argument("--until", help = "Only commits older than this date")
    export_parser.add_argument("--branch", help = "Branch, tag or revision range (eg. main..feature) to export instead of the current branch")
    export_parser.add_argument("--path", action = "append", dest = "paths",
                               help = "Only commits changing this file/folder (can be repeated)")

    commit_parser: argparse.ArgumentParser = subparsers.add_parser("commit", help = f"Commit the exported notebook as {NOTEBOOK_AUTHOR_NAME} <{NOTEBOOK_AUTHOR_EMAIL}>, so that it is excluded from the notebook (see IGNORE_AUTHORS)") # pylint: disable=line-too-long
    commit_parser.add_argument("notebook_file", help = "Path of the exported notebook HTML file")
    commit_parser.add_argument("-m", "--message", default = "Update lab notebook",
                               help = "Commit message (default: %(default)s)")

    args = parser.parse_args()

    if args.command == "init":
        try:
            init_labnotebook(args.name)
        except NotGitRepoError as e:
            print(e)
            sys.exit(128)
    elif args.command == "export":
        try:
            output_path: str = os.path.abspath(args.output)  # export moves to the git root
            export_labnotebook(output_path, args.force, not args.no_link, since = args.since,
                               until = args.until, branch = args.branch, paths = args.paths)
            if args.commit:
                commit_labnotebook(output_path)
        except NotGitRepoError as e:
            print(e)
            sys.exit(128)
        except NotInitializedError as e:
            print(e)
            sys.exit(2)
        except OutputAlreadyExistsError as e:
            print(e)
            sys.exit(17)
        except EmptyHistoryError as e:
            print(e)
            sys.exit(5)
        except InvalidConfigError as e:
            print(e)
            sys.exit(22)
        except subprocess.CalledProcessError as error:
            sys.exit(error.returncode)
    elif args.command == "commit":
        try:
            commit_labnotebook(args.notebook_file, args.message)
        except subprocess.CalledProcessError as error:
            sys.exit(error.returncode)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
