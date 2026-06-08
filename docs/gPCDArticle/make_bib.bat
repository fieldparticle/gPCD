REM You may need to change the location of the Acrobat Reader
REM You can also comment out the DEL to keep all files
@echo off
cd J:\sandboxR9\ConfPaper\rpt
DEL *.log *.aux  *.blg *.bak *.sav *.dvi *.bbl *.blg *.log
ECHO UF THESIS BATCH FILE
ECHO PDFLATEX 1
pdflatex -interaction=batchmode main
ECHO BIBTEX
bibtex main >> bibtex.log
ECHO PDFLATEX 2
pdflatex -interaction=batchmode main
ECHO PDFLATEX 3
pdflatex -interaction=batchmode main

exit 0