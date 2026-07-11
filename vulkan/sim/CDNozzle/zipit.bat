del *.log
del *.bbl
del *.blg
del *.pdf
del *.gz
del *.cut
del *.out
del *.aux
del *.dvi
del *.xcp
del *.spv
"C:\Program Files\7-Zip\7z.exe" a -tzip ../MainDocument(TEX).zip @rawtexfiles.lst

pause