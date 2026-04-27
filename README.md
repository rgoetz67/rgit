# RGit

RGit is a tool to work with git repositories in a subversion like fashion.

It yet does not support branches  (creating and switching between them).
However, it will use the branch a local working copy is currently using.

In order to map objects in the repository RGit creates some local cache file in .rgc/
This will be create once a local repository is opened for the first time and are updated on later operations. Depending on the size of the repo is may take a moment.

## Installation

### Linux

* Download the source
* Enter the rgit directory
* Start ./rgit.sh
  * On the first start it will  create the required virtual environment
* Put a symlink somewhere on $PATH, e.g.:
  cd ~/bin
  ln -s PATH_RGIT/rgit.sh rgit

### Windows

* Download the source
* Enter the rgit directory
* start setup.bat
* You start RGit by the rgit.bat script.
  * You may put shortcuts to the appropriate places