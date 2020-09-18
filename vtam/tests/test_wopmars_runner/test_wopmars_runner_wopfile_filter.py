import os
import pathlib
import sys
import unittest
import yaml

from vtam.utils.ArgParser import ArgParser
from vtam.utils.PathManager import PathManager
from vtam.utils.WopmarsRunner import WopmarsRunner


class TestWorpmarsRunnerFilter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.package_path = PathManager.get_package_path()

        foopaths = {}
        foopaths['foofile'] = os.path.relpath(__file__, PathManager.get_package_path())
        foopaths['foodir'] = os.path.relpath(os.path.dirname(__file__), PathManager.get_package_path())
        foopaths['sorteddir'] = os.path.relpath(os.path.join(PathManager.get_test_path(), 'output'),
            PathManager.get_package_path())
        foopaths['blastdb'] = os.path.relpath(os.path.join(PathManager.get_test_path(), 'test_files', 'blastdb'),
            PathManager.get_package_path())
        foopaths['sortedinfo_tsv'] = os.path.relpath(os.path.join(cls.package_path, "doc/data/sortedinfo_mfzr.tsv"),
            PathManager.get_package_path())
        foopaths['optimize_lfn_variant_specific'] = os.path.relpath(os.path.join(cls.package_path, "vtam/tests/test_files_dryad.f40v5_small/run1_mfzr_zfzr/optimize_lfn_variant_specific.tsv"),
            PathManager.get_package_path())
        cls.foopaths = foopaths

        cls.minseqlength_value_32 = 32
        cls.minseqlength_value_40 = 40
        cls.lfn_variant_replicate_cutoff = 0.002

    def setUp(self):

        self.tempdir = PathManager.instance().get_tempdir()
        pathlib.Path(self.tempdir).mkdir(parents=True, exist_ok=True)

    def test_wopmars_runner_filter(self):

        cmd = 'filter --sortedinfo {sortedinfo_tsv} --sorteddir {foodir} --asvtable asvtableoutput.tsv'.format(**self.foopaths)

        cwd = os.getcwd()
        os.chdir(self.package_path)
        args = ArgParser.get_main_arg_parser().parse_args(cmd.split(" "))
        os.chdir(cwd)

        wopmars_runner = WopmarsRunner(command='filter', cli_args_dic=vars(args))
        wopfile_path, wopfile_content = wopmars_runner.create_wopfile()

        with open(os.path.join(os.path.dirname(__file__), "wopfile_filter.yml")) as fin:
            wopfile_content_bak = fin.read()

        if not sys.platform.startswith("win"):
            self.assertTrue(wopfile_content == wopfile_content_bak.strip())
        self.assertTrue('lfn_variant_cutoff' in yaml.load(wopfile_content, Loader=yaml.SafeLoader)['rule FilterLFN']['params'])

    def test_wopmars_runner_filter_lfn_variant_replicate(self):

        cmd = 'filter --sortedinfo {sortedinfo_tsv} --sorteddir {foodir} --asvtable asvtableoutput.tsv --lfn_variant_replicate'.format(
            **self.foopaths)

        cwd = os.getcwd()
        os.chdir(self.package_path)
        args = ArgParser.get_main_arg_parser().parse_args(cmd.split(" "))
        os.chdir(cwd)

        wopmars_runner = WopmarsRunner(command='filter', cli_args_dic=vars(args))
        wopfile_path, wopfile_content = wopmars_runner.create_wopfile()

        self.assertFalse('lfn_variant_cutoff' in yaml.load(wopfile_content, Loader=yaml.SafeLoader)['rule FilterLFN']['params'])
        self.assertTrue('lfn_variant_replicate_cutoff' in yaml.load(wopfile_content, Loader=yaml.SafeLoader)['rule FilterLFN']['params'])

    def test_wopmars_runner_filter_with_cutoff_specific(self):

        cmd = 'filter --sortedinfo {sortedinfo_tsv} --sorteddir {foodir} --asvtable asvtableoutput.tsv' \
                   ' --cutoff_specific {optimize_lfn_variant_specific}'.format(**self.foopaths)

        cwd = os.getcwd()
        os.chdir(self.package_path)
        args = ArgParser.get_main_arg_parser().parse_args(cmd.split(" "))
        os.chdir(cwd)

        wopmars_runner = WopmarsRunner(command='filter', cli_args_dic=vars(args))
        wopfile_path = os.path.relpath(os.path.join(PathManager.get_package_path(), "tests/output/wopfile"), PathManager.get_package_path())
        wopfile_path, wopfile_content = wopmars_runner.create_wopfile(path=wopfile_path)

        self.assertTrue(yaml.load(wopfile_content, Loader=yaml.SafeLoader)['rule FilterLFN']['params']['lfn_variant_specific_cutoff'] == self.foopaths['optimize_lfn_variant_specific'])
