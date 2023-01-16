# Copyright 2018 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT

"""Measures for raw swarm performance in foraging tasks, according to whatever
their configured measure in univariate and bivariate batched experiments.

"""
# Core packages
import pathlib
import logging
import typing as tp

# 3rd party packages
import pandas as pd
from sierra.core.graphs.summary_line_graph import SummaryLineGraph
from sierra.core.graphs.heatmap import Heatmap
import sierra.core.utils
import sierra.core.config
import sierra.core.stat_kernels
from sierra.core import types

# Project packages
import titerra.projects.common.perf_measures.common as pmcommon
import titerra.variables.batch_criteria as bc


class BaseSteadyStateRaw:
    kLeaf = 'PM-ss-raw'

    @staticmethod
    def df_kernel(collated: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:

        dfs = {}
        for exp in collated.keys():
            dfs[exp] = pd.DataFrame(columns=collated[exp].columns,
                                    index=[0])  # Steady state

            for col in collated[exp].columns:
                dfs[exp][col] = collated[exp].loc[collated[exp].index[-1], col]

        return dfs


class SteadyStateRawUnivar(BaseSteadyStateRaw):
    """
    Generates a :class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`
    from the raw performance count of the swarm configuration across a
    univariate batched set of experiments within the same scenario from collated
    CSV data.

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 perf_csv: str,
                 perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col
        self.logger = logging.getLogger(__name__)

    def from_batch(self,
                   criteria: bc.IConcreteBatchCriteria,
                   title: str,
                   ylabel: str) -> None:
        self.logger.info("From %s", self.cmdopts["batch_stat_collate_root"])

        img_opath = pathlib.Path(self.cmdopts["batch_graph_collate_root"],
                                 self.kLeaf + sierra.core.config.kImageExt)

        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts,
                                             criteria,
                                             self.kLeaf,
                                             pm_dfs,
                                             False)

        SummaryLineGraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=img_opath,
                         model_root=self.cmdopts['batch_model_root'],
                         title=title,
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel=ylabel,
                         xticks=criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class SteadyStateRawBivar(BaseSteadyStateRaw):
    """Generates a :class:`sierra.core.graphs.heatmap.Heatmap` from the raw
    performance count of the swarm configuration across a bivariate batched set
    of experiments within the same scenario from collated CSV data.

    """

    def __init__(self, cmdopts: types.Cmdopts, perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col
        self.logger = logging.getLogger(__name__)

    def from_batch(self, criteria: bc.IConcreteBatchCriteria, title: str) -> None:
        self.logger.info("From %s", self.cmdopts["batch_stat_collate_root"])

        img_opath = pathlib.Path(self.cmdopts["batch_graph_collate_root"],
                                 self.kLeaf + sierra.core.config.kImageExt)

        dfs = pmcommon.gather_collated_sim_dfs(
            self.cmdopts, criteria, self.perf_leaf, self.perf_col)
        pm_dfs = self.df_kernel(dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(
            self.cmdopts, criteria, self.kLeaf, pm_dfs, False)

        stat_opath = pathlib.Path(self.cmdopts["batch_stat_collate_root"],
                                  self.kLeaf + sierra.core.config.kStats['mean'].exts['mean'])
        img_opath = pathlib.Path(self.cmdopts["batch_graph_collate_root"],
                                 self.kLeaf + sierra.core.config.kImageExt)

        Heatmap(input_fpath=stat_opath,
                output_fpath=img_opath,
                title=title,
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()


__api__ = [
    'BaseSteadyStateRaw',
    'SteadyStateRawUnivar',
    'SteadyStateRawBivar'
]
