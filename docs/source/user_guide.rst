|PyPI version fury.io| |PyPI license|

.. |PyPI version fury.io| image:: https://badge.fury.io/py/pylabnotebook.svg
   :target: https://pypi.org/project/pylabnotebook/

.. |PyPI license| image:: https://img.shields.io/pypi/l/pylabnotebook.svg
   :target: https://pypi.org/project/pylabnotebook/

CLI Documentation
=======================

This is the official documentation for the CLI version of pylabnotebook. All commands explained here have a corresponding function (see API), but I highly recommend to run this package from the command line, as it was created for.

Installation
----------------

Pylabnotebook can be installed via `pip` in an isolated environment (suggested):

.. code-block:: console

   (.venv) $ pip install pylabnotebook

To check the installation:

.. code-block:: console

   (.venv) $ labnotebook --version

.. warning::
    Whilst the python dependencies are automatically downloaded and installed, this package highly relies on git. Therefore, there are some git requirements that need to be fulfilled:

    * **git version** >= 2.40.1, otherwise some functionalities do not work
    * **git author and git email** set, otherwise the tool cannot create a notebook, as it checks for git author.



Init a notebook
--------------------------------

To init a new notebook, just type the following code in any folder of a git directory:

.. code-block:: console

   (.venv) $ labnotebook init -n "my project"

A message that confirms the creation of the .labnotebookrc file should appear on the console as stout.

.. note::
    Remember to never change the name of .labnotebookrc file.

Upgrade the configuration
--------------------------------

After updating pylabnotebook, add the new settings to an existing `.labnotebookrc` with:

.. code-block:: console

   (.venv) $ labnotebook upgrade

Your settings (and comments) are kept: missing settings are appended with their default value, and an old absolute *LAB_CSS* path to the default style is emptied. The previous file is saved as `.labnotebookrc.bak`. Use ``--dry-run`` to only see what would change.

Export a notebook
--------------------------------

To export the notebook as a single .html file, from any folder of the project type:

.. code-block:: console

   (.venv) $ labnotebook export -o my_project.html

It will create a my_project.html file with the notebook, with a sidebar of dates, a search box to filter commits and git tags shown as badges (useful to mark milestones, eg. ``git tag -a submitted-paper``) (the path is relative to the current folder). You can then share the notebook with peers.

To export only part of the history:

* ``--since 2024-01-01`` / ``--until "2 weeks ago"``: commits in a date range (any date git understands).
* ``--branch feature`` (or a range like ``main..feature``): another branch instead of the current one.
* ``--path analyses/`` (repeatable): only commits changing these files/folders (all changed files of those commits are listed).

Commit the notebook
--------------------------------

If the exported notebook is tracked in the repository, commit it with:

.. code-block:: console

   (.venv) $ labnotebook commit my_project.html

The commit is made as ``labnotebook <labnotebook@localhost>`` (only the notebook file is committed, anything else you staged is left untouched), so it does not appear in the notebook at the next export. Use ``-m`` to change the commit message.

To export and commit in one step: ``labnotebook export -o my_project.html -f --commit``.

To get a PDF, open the notebook in a browser and print it (Save as PDF): navigation elements are hidden and the changed files lists are expanded.

Notebook customization
--------------------------------

There are several customization that can be applied to the notebook:

* you can provide your personal css file by setting its path (relative to the git root) in the `.labnotebookrc` file in *LAB_CSS* variable. Leave it empty to use the default style.

* you can decide to show commits from last to first (default) or from first to last (changing *REVERSE_HISTORY* variable in `.labnotebookrc` to True).

* you can change name and author of the notebook in `.labnotebookrc`, it will be passed to file when exporting the notebook.

* you can exclude commits from the notebook by author name or email, listing them in the *IGNORE_AUTHORS* variable (eg. IGNORE_AUTHORS: ['labnotebook@localhost', 'ci-bot']). By default it contains the identity used by ``labnotebook commit``.

* you can exclude commits whose title matches a regular expression with the *IGNORE_MESSAGES* variable (eg. IGNORE_MESSAGES: ['^wip', '^fixup!']).

Link to analysis files
^^^^^^^^^^^^^^^^^^^^^^^^

When exporting the notebook, it automatically creates a list of analysis files for each commit with direct links to them (relative to the folder of the exported notebook). By default, it takes all the .html files changed/added in that commit that still exist. Links open the current version of the file: if the file was changed in a later commit, it is marked as such.

If you want to add different extensions, you can update the `.labnotebookrc` file by adding/removing extensions in the ANALYSIS_EXT variable. Each extension should be separated by a comma, as it is considered a list (eg. "ANALYSIS_EXT": ['.html', '.txt']): just type the extension, not wildcards or other special characters.

Moreover, changing values inside "ANALYSIS_IGNORE" list, you can exclude some files/folders to be recognized as analysis files. Each value is a regular expression searched anywhere in the file path (relative to the git root), eg. ``ANALYSIS_IGNORE: ['^old_reports/', '(^|/)draft_', '\.tmp\.html$']``. Keep in mind that:

* a pattern matches anywhere: ``old`` also matches ``golden.html``; use ``^old/`` for a top level folder or ``(^|/)old/`` for a folder at any level;
* ``.`` matches any character: write ``\.html$``, not ``.html``;
* wildcards are not regular expressions: ``*.html`` is invalid (export stops with an error message).

Images changed in a commit (extensions in *IMAGE_EXT*, default png, jpg, jpeg, gif, svg, webp) are shown as thumbnails, unless they were changed in a later commit (the notebook would show the newer version). *ANALYSIS_IGNORE* applies to them too.

Set *SHOW_ANALYSIS_FILES* to False to hide the analysis files list.

If you want to disable all links (and thumbnails), pass the `no-link` flag to the export command.

Link to the remote repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If *REMOTE_URL* is set in `.labnotebookrc` (`init` fills it from the `origin` remote, eg. https://github.com/user/repo), each commit sha links to the commit page and analysis files changed in a later commit also link to their version at that commit (GitHub/GitLab style URLs).

