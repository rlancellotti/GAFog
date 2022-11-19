import argparse
from pygnuplot import gnuplot


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help="input file. Default sens_nsrv_chainGA.data")
    args   = parser.parse_args()
    # A data file can be specified or the default is opened 
    fname  = 'sample/' + (args.file or "sens_nsrv_chainGA.data")
    
    with open(fname) as g:

        #TODO: implement the comparison between the 3 algorithm (?)

        g = gnuplot.Gnuplot(output=f'\"{fname.replace(".data","")}-1.png\"', term='pngcairo font "helvetica,12"')
        
        # If the file has the data about the experiments on rho
        if 'rho' in fname:
            g.cmd(  'set key bottom right',
                    'set xlabel "{/Symbol r}"',
                    'set ylabel "Jain index"',
                    'set ytics nomirror',
                    'set y2label "# of hops"',
                    'set y2tics nomirror')
            g.plot(f'\"{fname}\" u ($1):($2) axes x1y1 t "Jain index" w lp lc 1 pt 4, \"{fname}\" u ($1):($2):($3) axes x1y1 notitle w errorbars lc 1 pt 4, \"{fname}\" u ($1):($8/4) axes x1y2 t "Normalized # hops" w lp lc 2 pt 5, \"{fname}\" u ($1):($8/4):($9/4) axes x1y2 notitle w errorbars lc 2 pt 5')

            g.unset('y2label', 'y2tics')
            g.set(output=f'\"{fname.replace(".data","")}-2.png\"')
            g.cmd(  'set ytics mirror',
                    'set key top left',
                    'set xlabel "{/Symbol r}"',
                    'set ylabel "Response time [ms]"')
            g.plot(f'[][0:] \"{fname}\" u ($1):($4-$6-$7):($4+$6+$7) notitle w filledcurve fillstyle solid 0.2 noborder linecolor 1, \"{fname}\" u ($1):($4-$6):($4+$6) t "Std. deviation" w filledcurve fillstyle solid 0.4 noborder linecolor 1, \"{fname}\" u ($1):($4) t "Avg response time" w lp lc 1 pt 4, \"{fname}\" u ($1):($4):($5) notitle w errorbars lc 1 pt 4')

        # If the file has the data about the experiments on the number of service
        elif 'nsrv_chain' in fname:
            g.cmd(  'set key bottom right',
                    'set xlabel "# microservices / chain"',
                    'set ylabel "Jain index"',
                    'set ytics nomirror',
                    'set y2label "# of hops"',
                    'set y2tics nomirror',
                    'set y2range [0:]',
                    'set pointsize 2')
            g.plot(f'\"{fname}\" u ($1):($2) axes x1y1 t "Jain index" w lp lc 1 pt 4, \"{fname}\" u ($1):($2):($3) axes x1y1 notitle w errorbars lc 1 pt 4, \"{fname}\" u ($1):($8/($1-1)) axes x1y2 t "Normalized # hops" w lp lc 2 pt 5, \"{fname}\" u ($1):($8/($1-1)):($9/($1-1)) axes x1y2 notitle w errorbars lc 2 pt 5, ')

            g.unset('y2label', 'y2tics')
            g.set(output=f'\"{fname.replace(".data","")}-2.png\"')
            g.cmd(  'set ytics mirror',
                    'set key top right',
                    'set xlabel "# microservices / chain"',
                    'set ylabel "Response time [ms]"')
            g.plot(f'[][0:] \"{fname}\" u ($1):($4-$6-$7):($4+$6+$7) notitle w filledcurve fillstyle solid 0.2 noborder linecolor 1, \"{fname}\" u ($1):($4-$6):($4+$6) t "Std. deviation" w filledcurve fillstyle solid 0.4 noborder linecolor 1, \"{fname}\" u ($1):($4) t "Avg response time" w lp lc 1 pt 4, \"{fname}\" u ($1):($4):($5) notitle w errorbars lc 1 pt 4')

        # If the file has the data about the experiments on the number of fog nodes   
        elif 'nfog' in fname:
            g.cmd(  'set key bottom left', 
                    'set xlabel "# fog"',
                    'set ylabel "Response time [ms]"',
                    'set ytics nomirror',
                    'set y2label "Execution time [s]"',
                    'set y2tics nomirror',
                    'set y2range [0:]')
            g.plot(f'[] [0:] \"{fname}\" u ($1):($4-$6-$7):($4+$6+$7) axes x1y1 notitle w filledcurve fillstyle solid 0.2 noborder linecolor 1, \"{fname}\" u ($1):($4-$6):($4+$6) axes x1y1 t "Std. deviation" w filledcurve fillstyle solid 0.4 noborder linecolor 1, \"{fname}\" u ($1):($4) axes x1y1 t "Avg response time" w lp lc 1 pt 4, \"{fname}\" u ($1):($4):($5) axes x1y1 notitle w errorbars lc 1 pt 4, \"{fname}\" u ($1):($10) axes x1y2 t "Execution time" w lp lc 2 pt 5, \"{fname}\" u ($1):($10):($11) axes x1y2 notitle w errorbars lc 2 pt 5')
            

            g.unset('y2label', 'y2tics')
            g.set(output=f'\"{fname.replace(".data","")}-2.png\"')
            g.cmd(  'set ytics mirror',
                    'set key top left',
                    'set xlabel "# fog"',
                    'set ylabel "Execution  time [s]"')
            g.plot(f'\"{fname}\" u ($1):($10) t "Execution time" w lp lc 1 pt 4, \"{fname}\" u ($1):($10):($11) notitle w errorbars lc 1 pt 4',)