
import argparse
from os import terminal_size
from pygnuplot import gnuplot



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help="input file. Default sens_nsrv_chainGA.data")
    args   = parser.parse_args()
    # A data file can be specified or it is opened the default
    fname  = 'sample/' + (args.file or "sens_nsrv_chainGA.data")
    
    with open(fname) as f:
        # TODO: Is possible use only one gnuplot without getting errors everywhere?
        g, f = gnuplot.Gnuplot(), gnuplot.Gnuplot()
        
        # If the file has the data about the experiments on rho
        if 'rho' in fname:
            g.cmd('set key bottom right')
            g.cmd('set xlabel "{/Symbol r}"')
            g.cmd('set ylabel "Jain index"')
            g.cmd('set ytics nomirror')
            g.cmd('set y2label "# of hops"')
            g.cmd('set y2tics nomirror')
            g.cmd(f'p \"{fname}\" u ($1):($2) axes x1y1 t "Jain index" w lp lc 1 pt 4, \"{fname}\" u ($1):($2):($3) axes x1y1 notitle w errorbars lc 1 pt 4, \"{fname}\" u ($1):($8/4) axes x1y2 t "Normalized # hops" w lp lc 2 pt 5, \"{fname}\" u ($1):($8/4):($9/4) axes x1y2 notitle w errorbars lc 2 pt 5')


            f.unset('y2label', 'y2tics')
            f.cmd('set ytics mirror')
            f.cmd('set key top left')
            f.cmd('set xlabel "{/Symbol r}"')
            f.cmd('set ylabel "Response time [ms]"')
            f.cmd(f'p [][0:] \"{fname}\" u ($1):($4-$6-$7):($4+$6+$7) notitle w filledcurve fillstyle solid 0.2 noborder linecolor 1, \"{fname}\" u ($1):($4-$6):($4+$6) t "Std. deviation" w filledcurve fillstyle solid 0.4 noborder linecolor 1, \"{fname}\" u ($1):($4) t "Avg response time" w lp lc 1 pt 4, \"{fname}\" u ($1):($4):($5) notitle w errorbars lc 1 pt 4')

        # If the file has the data about the experiments on the number of service
        elif 'nsrv_chain' in fname:
            g.cmd('set key bottom right')
            g.cmd('set xlabel "# microservices / chain"')
            g.cmd('set ylabel "Jain index"')
            g.cmd('set ytics nomirror')
            g.cmd('set y2label "# of hops"')
            g.cmd('set y2tics nomirror')
            g.cmd('set y2range [0:]')
            g.cmd('set pointsize 2')
            g.cmd(f'p \"{fname}\" u ($1):($2) axes x1y1 t "Jain index" w lp lc 1 pt 4, \"{fname}\" u ($1):($2):($3) axes x1y1 notitle w errorbars lc 1 pt 4, \"{fname}\" u ($1):($8/($1-1)) axes x1y2 t "Normalized # hops" w lp lc 2 pt 5, \"{fname}\" u ($1):($8/($1-1)):($9/($1-1)) axes x1y2 notitle w errorbars lc 2 pt 5, ')

            f.unset('y2label', 'y2tics')
            f.cmd('set ytics mirror')
            f.cmd('set key top right')
            f.cmd('set xlabel "# microservices / chain"')
            f.cmd('set ylabel "Response time [ms]"')
            f.cmd(f'p [][0:] \"{fname}\" u ($1):($4-$6-$7):($4+$6+$7) notitle w filledcurve fillstyle solid 0.2 noborder linecolor 1, \"{fname}\" u ($1):($4-$6):($4+$6) t "Std. deviation" w filledcurve fillstyle solid 0.4 noborder linecolor 1, \"{fname}\" u ($1):($4) t "Avg response time" w lp lc 1 pt 4, \"{fname}\" u ($1):($4):($5) notitle w errorbars lc 1 pt 4')

        # If the file has the data about the experiments on the number of fog nodes   
        elif 'nfog' in fname:
            g.cmd('set key bottom left')
            g.cmd('set xlabel "# fog"')
            g.cmd('set ylabel "Response time [ms]"')
            g.cmd('set ytics nomirror')
            g.cmd('set y2label "Execution time [s]"')
            g.cmd('set y2tics nomirror')
            g.cmd('set y2range [0:]')
            g.cmd(f'p [] [0:] \"{fname}\" u ($1):($4-$6-$7):($4+$6+$7) axes x1y1 notitle w filledcurve fillstyle solid 0.2 noborder linecolor 1, \"{fname}\" u ($1):($4-$6):($4+$6) axes x1y1 t "Std. deviation" w filledcurve fillstyle solid 0.4 noborder linecolor 1, \"{fname}\" u ($1):($4) axes x1y1 t "Avg response time" w lp lc 1 pt 4, \"{fname}\" u ($1):($4):($5) axes x1y1 notitle w errorbars lc 1 pt 4, \"{fname}\" u ($1):($10) axes x1y2 t "Execution time" w lp lc 2 pt 5, \"{fname}\" u ($1):($10):($11) axes x1y2 notitle w errorbars lc 2 pt 5')

            f.unset('y2label', 'y2tics')
            f.cmd('set ytics mirror')
            f.cmd('set key top left')
            f.cmd('set xlabel "# fog')
            f.cmd('set ylabel "Execution  time [s]"')
            f.cmd(f'p \"{fname}\" u ($1):($10) t "Execution time" w lp lc 1 pt 4, \"{fname}\" u ($1):($10):($11) notitle w errorbars lc 1 pt 4')
        

        


        

