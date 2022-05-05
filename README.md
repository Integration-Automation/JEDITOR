# je_editor

---

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
sudo sudo apt-get install python3-tk
```
* on fedora use
```commandline
sudo dnf python3-tk
```

---

[![CircleCI](https://circleci.com/gh/JE-Chen/je_editor/tree/main.svg?style=svg)](https://circleci.com/gh/JE-Chen/je_editor/tree/main)

[![Documentation Status](https://readthedocs.org/projects/je-editor/badge/?version=latest)](https://je-editor.readthedocs.io/en/latest/?badge=latest)

---

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
