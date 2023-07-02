set terminal pngcairo enhanced font "Helvetica,12"
set pointsize 2

set output "sens_nsrv_jain.png"
set key bottom right
set xlabel "# microservices / chain"
set ylabel "Jain index"

p \
"sens_nsrv_chainGA.data" u ($1):($2) t "GA" w lp lc 1 pt 4, \
"sens_nsrv_chainGA.data" u ($1):($2):($3) notitle w errorbars lc 1 pt 4, \
"sens_nsrv_chainVNS.data" u ($1):($2) t "VNS" w lp lc 2 pt 6, \
"sens_nsrv_chainVNS.data" u ($1):($2):($3) notitle w errorbars lc 2 pt 6, \
"sens_nsrv_chainMBFD.data" u ($1):($2) t "MBFD" w lp lc 3 pt 8, \
"sens_nsrv_chainMBFD.data" u ($1):($2):($3) notitle w errorbars lc 3 pt 8, \


set output "sens_nsrv_nhops.png"
set xlabel "# microservices / chain"
set ylabel "Normalized # hops"
set yrange [0:]

p \
"sens_nsrv_chainGA.data" u ($1):($8/($1-1)) t "GA" w lp lc 1 pt 4, \
"sens_nsrv_chainGA.data" u ($1):($8/($1-1)):($9/($1-1)) notitle w errorbars lc 1 pt 4, \
"sens_nsrv_chainVNS.data" u ($1):($8/($1-1)) t "VNS" w lp lc 2 pt 6, \
"sens_nsrv_chainVNS.data" u ($1):($8/($1-1)):($9/($1-1)) notitle w errorbars lc 2 pt 6, \
"sens_nsrv_chainMBFD.data" u ($1):($8/($1-1)) t "MBFD" w lp lc 3 pt 8, \
"sens_nsrv_chainMBFD.data" u ($1):($8/($1-1)):($9/($1-1)) notitle w errorbars lc 3 pt 8, \


set output "sens_nserv_tresp.png"
set key top right
set xlabel "# microservices / chain"
set ylabel "Response time [ms]"
p [][0:100] \
"sens_nsrv_chainGA.data" u ($1):($4) t "GA" w lp lc 1 pt 4, \
"sens_nsrv_chainGA.data" u ($1):($4):($5) notitle w errorbars lc 1 pt 4, \
"sens_nsrv_chainVNS.data" u ($1):($4) t "VNS" w lp lc 2 pt 6, \
"sens_nsrv_chainVNS.data" u ($1):($4):($5) notitle w errorbars lc 2 pt 6, \
"sens_nsrv_chainMBFD.data" u ($1):($4) t "MBFD" w lp lc 3 pt 8, \
"sens_nsrv_chainMBFD.data" u ($1):($4):($5) notitle w errorbars lc 3 pt 8, \

set output "sens_rho_jain.png"
set key bottom right
set xlabel "{/Symbol r}"
set ylabel "Jain index"

p \
"sens_rhoGA.data" u ($1):($2) t "GA" w lp lc 1 pt 4, \
"sens_rhoGA.data" u ($1):($2):($3) notitle w errorbars lc 1 pt 4, \
"sens_rhoVNS.data" u ($1):($2) t "VNS" w lp lc 2 pt 6, \
"sens_rhoVNS.data" u ($1):($2):($3) notitle w errorbars lc 2 pt 6, \
"sens_rhoMBFD.data" u ($1):($2) t "MBFD" w lp lc 3 pt 8, \
"sens_rhoMBFD.data" u ($1):($2):($3) notitle w errorbars lc 3 pt 8, \


set output "sens_rho_nhops.png"
set xlabel "{/Symbol r}"
set ylabel "Normalized # hops"
set yrange [0:]

p \
"sens_rhoGA.data" u ($1):($8/4) t "GA" w lp lc 1 pt 4, \
"sens_rhoGA.data" u ($1):($8/4):($9/4) notitle w errorbars lc 1 pt 4, \
"sens_rhoVNS.data" u ($1):($8/4) t "VNS" w lp lc 2 pt 6, \
"sens_rhoVNS.data" u ($1):($8/4):($9/4) notitle w errorbars lc 2 pt 6, \
"sens_rhoMBFD.data" u ($1):($8/4) t "MBFD" w lp lc 3 pt 8, \
"sens_rhoMBFD.data" u ($1):($8/4):($9/4) notitle w errorbars lc 3 pt 8, \

set output "sens_rho_tresp.png"
set key top right
set xlabel "{/Symbol r}"
set ylabel "Response time [ms]"
p [][0:100] \
"sens_rhoGA.data" u ($1):($4) t "GA" w lp lc 1 pt 4, \
"sens_rhoGA.data" u ($1):($4):($5) notitle w errorbars lc 1 pt 4, \
"sens_rhoVNS.data" u ($1):($4) t "VNS" w lp lc 2 pt 6, \
"sens_rhoVNS.data" u ($1):($4):($5) notitle w errorbars lc 2 pt 6, \
"sens_rhoMBFD.data" u ($1):($4) t "MBFD" w lp lc 3 pt 8, \
"sens_rhoMBFD.data" u ($1):($4):($5) notitle w errorbars lc 3 pt 8, \


set output "sens_nfog_tresp.png"
set key top right
set xlabel "{# fog}"
set ylabel "Response time [ms]"
p [][0:100] \
"sens_nfogGA.data" u ($1):($4) t "GA" w lp lc 1 pt 4, \
"sens_nfogGA.data" u ($1):($4):($5) notitle w errorbars lc 1 pt 4, \
"sens_nfogVNS.data" u ($1):($4) t "VNS" w lp lc 2 pt 6, \
"sens_nfogVNS.data" u ($1):($4):($5) notitle w errorbars lc 2 pt 6, \
"sens_nfogMBFD.data" u ($1):($4) t "MBFD" w lp lc 3 pt 8, \
"sens_nfogMBFD.data" u ($1):($4):($5) notitle w errorbars lc 3 pt 8, \


set output "sens_nfog_exetime.png"
set key top left
set xlabel "# fog"
set ylabel "Execution time [s]"
p \
"sens_nfogGA.data" u ($1):($10) t "GA" w lp lc 1 pt 4, \
"sens_nfogGA.data" u ($1):($10):($11) notitle w errorbars lc 1 pt 4, \
"sens_nfogVNS.data" u ($1):($10) t "VNS" w lp lc 2 pt 6, \
"sens_nfogVNS.data" u ($1):($10):($11) notitle w errorbars lc 2 pt 6, \
"sens_nfogMBFD.data" u ($1):($10) t "MBFD" w lp lc 3 pt 8, \
"sens_nfogMBFD.data" u ($1):($10):($11) notitle w errorbars lc 3 pt 8, \

