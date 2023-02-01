# je_editor

---

## Simple editor for edit code

### Features

* auto save (after first save)
* open last edit file
* run program
* execute shell script
* choose font and font size
* choose encoding
* choose language
* choose editor style
* use content file to choose you own style

---

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/825a90622a224207be4abe869775b50a)](https://www.codacy.com/gh/JE-Chen/je_editor/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=JE-Chen/je_editor&amp;utm_campaign=Badge_Grade)

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/JE-Chen/je_editor/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/JE-Chen/je_editor/tree/main)

[![JE_Editor GitHub Actions Dev](https://github.com/JE-Chen/je_editor/actions/workflows/je-editor-github-actions_dev.yml/badge.svg?branch=dev)](https://github.com/JE-Chen/je_editor/actions/workflows/je-editor-github-actions_dev.yml)

[![JE_Editor GitHub Actions Stable](https://github.com/JE-Chen/je_editor/actions/workflows/je-editor-github-actions_stable.yml/badge.svg?branch=main)](https://github.com/JE-Chen/je_editor/actions/workflows/je-editor-github-actions_stable.yml)

### Document

[![Documentation Status](https://readthedocs.org/projects/je-editor/badge/?version=latest)](https://je-editor.readthedocs.io/en/latest/?badge=latest)

---

## Requires

```
python 3.7 or later
```

## install

* please check your tkinter version
    * make sure tkinter is version 8.5 or later
  ```python
  # check tkinter version
  import tkinter
  tkinter._test()
  ```

* on Windows not need install any package
    * if fail to start tkinter
        * python version 3.7 and later will include new tk


* on macOS not need install any package
    * if fail to start tkinter
        * xcode-select --install
            * download python-tk
                * brew install python-tk
        * or download new python version, new python version include new Tcl/Tk

```
If you are using macOS 10.6 or later, 
the Apple-supplied Tcl/Tk 8.5 has serious bugs that can cause application crashes.
```

* on linux ubuntu use

```commandline 
sudo apt-get install python3-tk
```

* on fedora use

```commandline
sudo dnf python3-tk
```

* editor main window

![Main window image](/github_image/main_window_image.png)

---

* toolbar function
    * Run
        * Run program and get result
    * Run on shell
        * Run on command line and get result
    * Stop
        * Stop current running program
    * File
        * Save File
            * Save current edit file
        * Open File
            * Open file to edit
    * Text
        * Font
            * Choose editor font
        * Font Size
            * Choose font size
    * Encoding
        * Choose file encoding
    * Language
        * Java
            * need java on system path - default
        * Python3
            * need python3 on system path - default

---

* Test on
    * windows 10 ~ 11
    * osx 10.5 ~ 11 big sur
    * ubuntu 20.0.4
    * raspberry pi 3B+

| All test in test dir
