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

Export a notebook
--------------------------------

To export the notebook as a single .html file, from any folder of the project type:

.. code-block:: console

   (.venv) $ labnotebook export -o my_project.html

It will create a my_project.html file with the notebook (the path is relative to the current folder). You can then share the notebook with peers.

Commit the notebook
--------------------------------

If the exported notebook is tracked in the repository, commit it with:

.. code-block:: console

   (.venv) $ labnotebook commit my_project.html

The commit is made as ``labnotebook <labnotebook@localhost>`` (only the notebook file is committed, anything else you staged is left untouched), so it does not appear in the notebook at the next export. Use ``-m`` to change the commit message.

Notebook customization
--------------------------------

There are several customization that can be applied to the notebook:

* you can provide your personal css file by setting its path (relative to the git root) in the `.labnotebookrc` file in *LAB_CSS* variable. Leave it empty to use the default style.

* you can decide to show commits from last to first (default) or from first to last (changing *REVERSE_HISTORY* variable in `.labnotebookrc` to True).

* you can change name and author of the notebook in `.labnotebookrc`, it will be passed to file when exporting the notebook.

* you can exclude commits from the notebook by author name or email, listing them in the *IGNORE_AUTHORS* variable (eg. IGNORE_AUTHORS: ['labnotebook@localhost', 'ci-bot']). By default it contains the identity used by ``labnotebook commit``.

Link to analysis files
^^^^^^^^^^^^^^^^^^^^^^^^

When exporting the notebook, it automatically creates a list of analysis files for each commit with direct links to them (relative to the folder of the exported notebook). By default, it takes all the .html files changed/added in that commit that still exist. Links open the current version of the file: if the file was changed in a later commit, it is marked as such.

If you want to add different extensions, you can update the `.labnotebookrc` file by adding/removing extensions in the ANALYSIS_EXT variable. Each extension should be separated by a comma, as it is considered a list (eg. "ANALYSIS_EXT": ['.html', '.txt']): just type the extension, not wildcards or other special characters.

Moreover, changing values inside "ANALYSIS_IGNORE" list, you can exclude some files/folders to be recognized as analysis files. As in a .gitignore file, it uses wildcards: a pattern matches the whole path, any file/folder name or any folder (eg. ANALYSIS_IGNORE: ['draft_*', 'old_reports/', '*.tmp.html']).

If you want to disable all links, pass the `no-link` flag to the export command.

