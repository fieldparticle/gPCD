REM You may need to change the location of the Acrobat Reader
REM You can also comment out the DEL to keep all files
@echo off
cd J:\sandboxR9\ConfPaper\rpt
DEL *.log *.aux  *.blg *.bak *.sav *.dvi *.bbl *.blg *.log
ECHO UF THESIS BATCH FILE
ECHO LATEX 1
latex -interaction=batchmode main
ECHO LATEX 2
latex -interaction=batchmode main
ECHO BIBTEX
bibtex main >> make_xelatex_bib.log
ECHO LATEX 3
latex -interaction=batchmode main >> make_latex.log
ECHO LATEX 4
latex -interaction=batchmode main 
ECHO XELATEX 1
xelatex -interaction=nonstopmode main >> make_xelatex.log
ECHO XELATEX 2
xelatex main
REM start "c:\Program Files (x86)\Adobe\Reader 9.0\Reader\AcroRd32.exe" _main.pdf

exit 0