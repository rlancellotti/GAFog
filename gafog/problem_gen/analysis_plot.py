import argparse
import json
import os
import sqlite3

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from .analysis_db import get_experiments_by_scenario, get_table_column_names

DEFAULT_PLOT_DIR = 'experiment_analysis/plots/'

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', help=f'Database to retrieve data from. Default "experiment_analysis/experiments.db"', type=str)
    parser.add_argument('-s', '--scenario', help='Configuration file containing only the fixed scenario parameters for the retrieval', required=True, type=str)
    parser.add_argument('-p', '--plot-dir', help=f'Identifies the directory where to store plots (default: {DEFAULT_PLOT_DIR})', default=DEFAULT_PLOT_DIR, type=str)
    parser.add_argument('-c', '--sensitivity-col', help='The name of the column to analyze', required=True, type=str)
    parser.add_argument('-f', '--figsize', help='Size of the figures to generate (order: x,y)', type=float, nargs=2, default=(8,6))

    args = parser.parse_args()

    fig_size = args.figsize

    plot_dir = args.plot_dir
    if plot_dir[-1] != '/':
        plot_dir += '/'

    if not os.path.isdir(plot_dir):
        os.makedirs(plot_dir)

    sensitivity_col = args.sensitivity_col

    experiment_db = args.database
    if experiment_db is None:
        experiment_db = 'experiment_analysis/experiments.db'

    connection = sqlite3.Connection(experiment_db)

    scenario = json.loads(open(args.scenario, 'r').read())

    experiment_df = pd.DataFrame(data=get_experiments_by_scenario(connection=connection, scenario_config=scenario),
                                 columns=get_table_column_names(connection=connection, tablename='experiment')
                                 ).drop(columns=['id'])

    convergence_cols = [col for col in experiment_df.columns if col.endswith('convgen') and not col.startswith('sigma')]

    problem_sizes = experiment_df['nfog'].drop_duplicates().sort_values()

    for col in convergence_cols:
        fig = plt.figure(figsize=fig_size)

        var_col = 'sigma_'+col

        errorbar_plots = list()

        for prob_size in problem_sizes:

            size_mask = experiment_df['nfog'] == prob_size

            fix_size_scenario_df = experiment_df[size_mask].drop_duplicates(subset=[sensitivity_col], keep='first')

            stdev_bars = fix_size_scenario_df[[var_col, sensitivity_col]].sort_values(by=[sensitivity_col])[var_col]

            ax = plt.errorbar(x=fix_size_scenario_df[sensitivity_col], 
                              y=fix_size_scenario_df[col], 
                              yerr=stdev_bars,
                              capsize=5
                              )
            plt.scatter(x=fix_size_scenario_df[sensitivity_col], 
                        y=fix_size_scenario_df[col],
                        marker='o'
                        )
            errorbar_plots.append(ax)

        fig.gca().set_xlabel(sensitivity_col)
        fig.gca().set_ylabel(col)
        fig.gca().set_ylim(bottom=0)
        fig.legend(errorbar_plots, problem_sizes)
        fig.savefig(plot_dir+sensitivity_col+'_'+col)


    solution_metrics_names = ['obj_fun', 'power_consumption', 'response_time']
    solution_metrics = [(metric, 'sigma_'+metric) for metric in solution_metrics_names] + [('tresp_avg', 'tresp_std')]

    for prob_size in problem_sizes:
        size_mask = experiment_df['nfog'] == prob_size
        fix_size_scenario_df = experiment_df[size_mask].drop_duplicates(subset=[sensitivity_col], keep='first')
        for metric, metric_std in solution_metrics:
            fig = plt.figure(figsize=fig_size)
            sns.barplot(data=fix_size_scenario_df, x=sensitivity_col, y=metric, hue=sensitivity_col, errorbar=None, palette='tab10', legend=False)
            plt.errorbar(x=range(fix_size_scenario_df[sensitivity_col].drop_duplicates().shape[0]),
                            y=fix_size_scenario_df[metric],
                            yerr=fix_size_scenario_df[metric_std],
                            fmt='none',
                            c='k'
                            )
            fig.savefig(plot_dir+sensitivity_col+'_solution_'+metric+'_nfog_'+str(prob_size))

