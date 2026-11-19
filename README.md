<h1 align="center">Labnotebook 📔🖥</h1>

This project aims to help bioinformaticians in creating the so called "Laboratory notebook" automatically, thanks to git workflow manager.
Read the [documentation](https://pylabnotebook.readthedocs.io/en/latest/).

**IMPORTANT**: this tool is based on git and its application, in particular, through git history it will create an html notebook divided by date and commit.

<h3 style="margin-bottom:3px;">Features</h3>
<ul>
  <li>Automatically create a laboratory notebook</li>
  <li>Customizable CSS file</li>
  <li>Direct link to analysis files (expecially for user who creates .html reports. e.g. markdown or jupyter notebook html)</li>
  <li>Export to html, with date sidebar, search box, git tags as milestones and image thumbnails (print it to get a PDF)</li>
  <li>Commit the notebook without adding it to the notebook itself (<code>labnotebook commit</code> / <code>export --commit</code>)</li>
  <li>Filter the history: by date, branch, path, author or commit message</li>
  <li>Links to commits and file versions on GitHub/GitLab</li>
</ul>

<h3>Installation</h3>
To install the package, run:

```
pip install pylabnotebook
```

This will install the pylabnotebook package; you can then run <code>labnotebook</code> function from within the terminal (detailed explanation below).

For a complete guide, check the official [user guide](https://pylabnotebook.readthedocs.io/en/latest/user_guide.html).

<h3>Issue reporting and suggestions</h3>
If you find any issue or you want to suggest some edit, please feel free to open an issue or a pull request.
