# README

A half-baked solution to the "transposed marking" idea.

## Known Issues

* Does not search for auxiliary content (such as images that are not embedded in the notebooks). 
* Not a robust regex for recognizing exercise start/end cells; could be broken. 
* MathJax browser plug-in does not always recognize/format LaTeX code. 

## Requirements

* [`PyGithub`](https://github.com/PyGithub/PyGithub)
* [`nbformat`](https://github.com/jupyter/nbformat)
* [`nbconvert`](https://github.com/jupyter/nbconvert)
* `IPython` 
* `pandas`
* `numpy`