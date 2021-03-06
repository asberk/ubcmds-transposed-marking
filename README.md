
# Table of Contents

1.  [README](#org27e9827)
    1.  [Introduction](#orgb44d7bd)
    2.  [Get up and running](#orgc011c6d)
    3.  [Known Issues](#org7706937)
    4.  [Requirements](#org1fe3825)
    5.  [Obligatory disclaimer](#orgded2d11)


<a id="org27e9827"></a>

# README

A half-baked solution to the "transposed marking" idea.


<a id="orgb44d7bd"></a>

## Introduction

Have you been having to mark a single exercise for all students? Has it bugged 
you that Classy is not set up for this? Well, do I ever have a half-baked 
partially functional solution for you!

This code fetches one file from each student, for the course you're TAing. From 
each file, it exctracts the cells corresponding to the exercise you're supposed 
to mark. It gathers them all in some HTML pages (By default, 15 
exercises/students per HTML page to manage the page's filesize). Then, you can 
simply open up the HTML page(s) and see all of the students' answers together
in one place.


<a id="orgc011c6d"></a>

## Get up and running

The script may be run from the command line. For example:

    python3 write_exercise_to_html.py --uname=asberk --course=571 --lab=4 --exercise==3 --throttle=.75  

For documentation, run:

    python3 write_exercise_to_html.py --help

    usage: write_exercise_to_html.py [-h] [--uname UNAME] [--course COURSE]
                                     [--lab LAB]
                                     [--exercise [EXERCISE [EXERCISE ...]]]
                                     [--fname FNAME] [--gidpath GIDPATH]
                                     [--section SECTION]
                                     [--studentsperpage STUDENTSPERPAGE]
                                     [--throttle THROTTLE] [--doSave DOSAVE]
    
    Slice exercises from student lab files for easier marking.
    
    optional arguments:
      -h, --help            show this help message and exit
      --uname UNAME         GitHub Enterprise username.
      --course COURSE       DSCI course number (e.g., pass 571 for DSCI 571)
      --lab LAB             The lab number (e.g., pass 4 as the argument if you
                            want to grade Lab 4).
      --exercise [EXERCISE [EXERCISE ...]]
                            The exercise number (e.g., pass 3 for Exercise 3; pass
                            3 4 5 for Exercises 3--5)
      --fname FNAME         A regex used to search for a file pattern.
      --gidpath GIDPATH     The list of the students GitHub IDs to use. Note: a
                            list with non-matching entries may cause the script to
                            break or hang.
      --section SECTION     Allows filtering by Lab Section (e.g., section L02).
                            Default: all sections.
      --studentsperpage STUDENTSPERPAGE
                            Each HTML page that's generated will contain
                            studentsperpage many answers. This is done to manage
                            filesize.
      --throttle THROTTLE   Min duration to wait (in seconds) between pulling lab
                            files.
      --doSave DOSAVE       Whether to save intermediate lab files as .pkl.bz2
                            objects.

Set `uname` to be your GitHub username on `github.ubc.ca`. Set `course`,
`exercise` and `lab` appropriately (*e.g.*, 
`--course=571 --lab=4 --exercise 3 4 5`).

You can also set the regex used to match the lab file in each student's 
repository by passing an argument to `fname`. By default, it is set to 
recognize files like `'*lab##*.ipynb'`. In particular, `fname` is set to 
recognize `ipynb` files only (*e.g.*, it would need to be modified if the 
submitted assignments are Rmd files). 

In order to use the `PyGithub` package, the script must be able to load your 
password. To do this, create a file `ghubcmds.pw` in the same directory as the 
script, which contains your password. By default, this repository's `.gitignore` 
is set to ignore `*.pw` files so that one is not accidentally committed to 
remote. The function `load_ghpw` will load `ghubcmds.pw` and attempt to use the
text therein as the password associated with your GitHub Enterprise username.

Finally, the script also requires a csv file (called `classy.csv`), which you
can download from the main [classy page](https://mds.cs.ubc.ca). This is simply a list of all the
students' GitHub (Enterprise) usernames.

The output of the script appears in a new folder:

-   `./DSCI{course_num}/Lab{lab_num}/{...}_page##.html`
-   `./DSCI{course_num}/Lab{lab_num}/style##.css`


<a id="org7706937"></a>

## Known Issues

-   Does not search for auxiliary content (such as images that are not embedded
    in the notebooks).
-   Not a robust regex for recognizing exercise start/end cells; could be broken.
-   MathJax browser plug-in does not always recognize/format LaTeX code.
-   High level: this still doesn't solve the issue of having to navigate classy 
    in order to input the grades. I tried doing this with Selenium, but something
    in Classy's javascript prevents this from being "simple". If you think you 
    know how to solve or work around this snag, I'd love to hear about it!
-   Find other issues? Create one and I'll do my best to be responsive to them. :-)


<a id="org1fe3825"></a>

## Requirements

-   [PyGithub](https://github.com/PyGithub/PyGithub)
-   [nbformat](https://github.com/jupyter/nbformat)
-   [nbconvert](https://github.com/jupyter/nbconvert)
-   `IPython`
-   `pandas`
-   `numpy`
-   `pickle`
-   `bz2`


<a id="orgded2d11"></a>

## Obligatory disclaimer

While I haven't had any problems so far, I suspect it **may** be possible for a 
lab submission to "break" how this module works. As such, use it at your own 
risk. This code is not responsible (nor am I) for any content that is 
missing or altered in the HTML output. 

