# FPIBG
# Fast parallel index-based GPU-driven particle collision detection
## Particle Collison Detection Performance Reports


`FPIBGDATA\perfdataPQB\PQBReport.csv`

`FPIBGDATA\perfdataPCD\PCDReport.csv`

`FPIBGDATA\perfdataCFB\CFBReport.csv`

perfApp will caluate the following parameters:

`file` -> directory and file name of the *.tst file

`numparticles` ->  the number of particles processed

`numcollisions` -> the number of collsions prosesse.

`avgfps`  -> the average frames per second

`avgcpums`  -> the average cpu time per frame in seconds.

`avgcms`  -> the average compute shader time per frame in seconds.

`avggms`  -> the average graphics pipeline time per frame in seconds.

`minfps`  -> the minimum frames per second.

`mincpums`  -> the minimum cpu time per frame in seconds

`mincms`  -> the minimum compute time per frame in seconds

`mingms`  -> the minimum graphics pipline time per frame in seconds

`maxfps`  -> the maximum frames per second.

`maxcpums`  -> the maximum cpu time per frame in seconds

`maxcms`  -> the maximum compute time per frame in seconds

`maxgms`  -> the maximum graphics pipline time per frame in seconds

`minspf`  -> the minimum total time to process each frame is the maxfps divided by 1.

`maxspf` ->  the maximum total time to process each frame is the minfps divided by 1.

`avgspf` ->  the average total time to process each frame is the total fps divided by the number of entries.

`maxmrr` ->  the maximum machine rendering rate is 1.0/minspf;

`minmrr` ->  the maximum machine rendering rate is 1.0/minspf. This measure is used for comparison.

`avgmrr` -> the minimum machine rendering rate is 1.0/maxspf.

`maxarr` ->  the maximum application rendering rate is maxmrr/maxspf.

`minarr` ->  the minimum application rendering rate is minmrr/minspf also just called application rendering rate (arr).

`avgarr` -> the average application rendering rate is avgmrr/avgspf.

If there are errors the error will be reported in the log file 

`FPIBG\vulkan\run\PerfReport\PerfReport.log`

