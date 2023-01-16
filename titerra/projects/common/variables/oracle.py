# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Classes for the oracle batch criteria. See :ref:`ln-bc-oracle` for usage
documentation.

"""

# Core packages
import typing as tp
import re
import itertools
import pathlib

# 3rd party packages
import implements
from sierra.plugins.platform.argos.variables.population_size import PopulationSize
from sierra.core.experiment import xml
from sierra.core import types

# Project packages
import titerra.variables.batch_criteria as bc


@implements.implements(bc.IConcreteBatchCriteria)
@implements.implements(bc.IPMQueryableBatchCriteria)
class Oracle(bc.UnivarBatchCriteria):
    """
    A univariate range specifiying the types of oracular information to
    disseminate to the swarm during simulation. This class is a base class which
    should (almost) never be used on its own. Instead, the ``factory()``
    function should be used to dynamically create derived classes expressing the
    user's desired types to disseminate.

    Attributes:
        tuples: List of tuples of types of oracular information to enable for a
                specific.  simulation. Each tuple is (oracle name,
                list(tuple(oracle feature name, oracle feature value))).

        population: Swarm size to set for the swarm (can be ``None``).

    """
    kInfoTypes = {'entities': ['caches', 'blocks']}

    def __init__(self, cli_arg: str,
                 main_config: types.YAMLDict,
                 batch_input_root: pathlib.Path,
                 tuples: tp.List[tuple],
                 population: int) -> None:
        bc.UnivarBatchCriteria.__init__(self,
                                        cli_arg,
                                        main_config,
                                        batch_input_root)

        self.tuples = tuples
        self.population = population
        self.attr_changes = []  # type: tp.List

    def gen_attr_changelist(self) -> tp.List[xml.AttrChange]:
        if not self.attr_changes:
            # Swarm size is optional. It can be (1) controlled via this
            # variable, (2) controlled by another variable in a bivariate batch
            # criteria, (3) not controlled at all. For (2), (3), the swarm size
            # can be None.
            for oracle, features in self.tuples:
                s = xml.AttrChangeSet()
                for t in features:
                    s.add(xml.AttrChange(".//oracle_manager/{0}".format(str(oracle)),
                                         "{0}".format(t[0]),
                                         "{0}".format(t[1])))
                self.attr_changes.append(s)

            if self.population is not None:
                size_chgs = PopulationSize(self.cli_arg,
                                           self.main_config,
                                           self.batch_input_root,
                                           [self.population]).gen_attr_changelist()[0]
                for exp_chgs in self.attr_changes:
                    exp_chgs |= size_chgs

        return self.attr_changes

    def gen_exp_names(self, cmdopts: types.Cmdopts) -> tp.List[str]:
        changes = self.gen_attr_changelist()
        return ['exp' + str(x) for x in range(0, len(changes))]

    def graph_xticks(self,
                     cmdopts: types.Cmdopts,
                     exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[float]:
        if exp_names is None:
            exp_names = self.gen_exp_names(cmdopts)

        return list(map(float, range(0, len(exp_names))))

    def graph_xticklabels(self,
                          cmdopts: types.Cmdopts,
                          exp_names: tp.Optional[tp.List[str]] = None) -> tp.List[str]:
        raise NotImplementedError

    def graph_xlabel(self, cmdopts: types.Cmdopts) -> str:
        return "Oracular Information Type"

    def pm_query(self, pm: str) -> bool:
        return pm in ['raw']

    def inter_exp_graphs_exclude_exp0(self) -> bool:
        return False


class Parser():
    """
    Enforces the cmdline definition of the :class:`Oracle` batch criteria defined in
    :ref:`ln-bc-oracle`.
    """

    def __call__(self, criteria_str: str) -> dict:
        """
        Returns:
            Dictionary with keys:
                oracle_type: entities|tasking
                oracle_name: entities_oracle|tasking_oracle
                population: Size of swarm to use (optional)

        """
        ret = {
            'oracle_name': str(),
            'oracle_type': str(),
            'population': None
        }

        # Parse oracle name
        if 'entities' in criteria_str:
            ret['oracle_type'] = 'entities'
            ret['oracle_name'] = 'entities_oracle'
        elif 'tasking' in criteria_str:
            ret['oracle_type'] = 'tasking'
            ret['oracle_name'] = 'tasking_oracle'

        # Parse swarm size
        res = re.search(r"\.Z[0-9]+", criteria_str)
        if res is not None:
            ret['population'] = int(res.group(0)[2:])
        return ret


def factory(cli_arg: str,
            main_config: tp.Dict[str, str],
            cmdopts: types.Cmdopts,
            **kwargs):
    """
    Factory to create ``Oracle`` derived classes from the command line definition.

    """
    attr = Parser()(cli_arg)

    def gen_tuples():

        if 'entities' in attr['oracle_name']:
            tuples = []
            for val in list(itertools.product([False, True], repeat=len(Oracle.kInfoTypes['entities']))):
                tuples.append((attr['oracle_name'],
                               [(Oracle.kInfoTypes['entities'][i], str(val[i]).lower())
                                for i in range(0, len(Oracle.kInfoTypes['entities']))]
                               ))

            return tuples

        return None

    def __init__(self) -> None:
        Oracle.__init__(self,
                        cli_arg,
                        main_config,
                        cmdopts['batch_input_root'],
                        gen_tuples(),
                        attr.get('population', None))

    return type(cli_arg,
                (Oracle,),
                {"__init__": __init__})


__api__ = [
    'Oracle'
]
