import argparse
import multiprocessing
import os

import pandas

from vtam.utils.Logger import Logger
from vtam.utils.OptionManager import OptionManager
from vtam.utils.VTAMexception import VTAMexception


class ArgParserChecker(object):
    """Methods to check arguments"""

    @classmethod
    def check_parser_filter_arg_sampleselect(cls, path):

        """Checks if file exists and is not empty

        :param path: Path to the sampleselect TSV file
        :return: void
        """

        path = cls.check_file_exists_and_is_nonempty(path)

        df = pandas.read_csv(path, sep="\t", header=0)
        df.columns = map(str.lower, df.columns) # df columns to lower
        if not 'run' in df.columns and not 'marker' in df.columns:
            raise argparse.ArgumentTypeError("The TSV file {} does not contain columns with 'Run' and 'Marker' columns!".format(path))
        else:
            return path

    @staticmethod
    def check_real_between_0_and_100(value):
        fvalue = float(value)
        if fvalue < 0 or fvalue > 100:
            raise argparse.ArgumentTypeError("%s is an invalid real value between 0 and 100" % value)
        return fvalue

    @staticmethod
    def check_real_positive(value):
        fvalue = float(value)
        if fvalue <= 0:
            raise argparse.ArgumentTypeError("%s is an invalid positive real value" % value)
        return fvalue

    @staticmethod
    def check_parser_taxassign_arg_variants(variant_tsv_path, error_message=None):
        """Check if the vtam taxassign --variants argument is a TSV file with a header and sequence column name in the last column

        :param error_message: Optional message to help debug the problem
        :return: void
        """
        try:
            assert os.stat(variant_tsv_path).st_size > 0
            variant_df = pandas.read_csv(variant_tsv_path, sep="\t", header=0)
            assert (variant_df.columns[-1] == 'sequence')
        except AssertionError as err:
            raise Logger.instance().error(VTAMexception("{}: {}".format(err, error_message)))
        except FileNotFoundError as err:
            raise Logger.instance().error(VTAMexception("{}: {}".format(err, error_message)))
        return variant_tsv_path

    @staticmethod
    def check_parser_poolmarkers_arg_runmarker(path, error_message=None):

        """Checks if file exists and is not empty

        :param error_message: Optional message to help debug the problem
        :return: void
        """

        try:
            assert os.stat(path).st_size > 0
            run_marker_df = pandas.read_csv(path, sep="\t", header=0)
            assert ('marker_name' in run_marker_df.columns and 'run_name' in run_marker_df.columns)
            assert run_marker_df.shape[0] > 0
        except AssertionError as err:
            raise Logger.instance().error(VTAMexception("{}: {}".format(err, error_message)))
        except FileNotFoundError as err:
            raise Logger.instance().error(VTAMexception("{}: {}".format(err, error_message)))
        return path

    @staticmethod
    def check_file_exists_and_is_nonempty(path):

        """Checks if file exists and is not empty

        :param path: Valid non-empty file path
        :return: void

        """
        if not os.path.isfile(path):
            raise argparse.ArgumentTypeError("The file {} does not exist!".format(path))
        elif not os.stat(path).st_size > 0:
            raise argparse.ArgumentTypeError("The file {} is empty!".format(path))
        else:
            return path  # return the path

    @staticmethod
    def check_dir_exists_and_is_nonempty(path):
        """Checks if directory exists and is not empty

        :param path: Valid non-empty directory path
        :return: void
        """
        if not os.path.isdir(path):
            raise argparse.ArgumentTypeError("The directory {} does not exist!".format(path))
        elif not len(os.listdir(path)) > 0:
            raise argparse.ArgumentTypeError("The directory {} is empty!".format(path))
        else:
            return path

    # @staticmethod
    # def check_blast_db_argument(blast_db):
    #     """Verifies --blast_db argument. Must be exactly two arguments.
    #
    #     - First argument: REQUIRED. Blast DB directory
    #
    #     :param error_message: Optional message to help debug the problem
    #     :param abspath: If True, returns abspath
    #     :return: void
    #     """
    #
    #     ArgParserChecker.check_dir_exists_and_is_nonempty(blast_db)
    #     OptionManager.instance()['blast_db'] = blast_db
    #
    #     one_file_exists = {'nhr': 0, 'nin': 0, 'nog': 0, 'nsd': 0, 'nsi': 0, 'nsq': 0}
    #     for fname in os.listdir(OptionManager.instance()['blast_db']):
    #         if fname.endswith('.nhr'):
    #             one_file_exists['nhr'] = 1
    #         elif fname.endswith('.nin'):
    #             one_file_exists['nin'] = 1
    #         elif fname.endswith('.nog'):
    #             one_file_exists['nog'] = 1
    #         elif fname.endswith('.nsd'):
    #             one_file_exists['nsd'] = 1
    #         elif fname.endswith('.nsi'):
    #             one_file_exists['nsi'] = 1
    #         elif fname.endswith('.nsq'):
    #             one_file_exists['nsq'] = 1
    #     if not sum(one_file_exists.values()) == 6:
    #         raise Logger.instance().error(VTAMexception("Verify the Blast DB directory for files with 'nt' file name"
    #                                                 " and 'nhr', 'nin', 'nog', 'nsd', 'nsi' and 'nsq' file types."))
    #     return blast_db


class ArgParser:

    args_db = {'dest': 'db', 'action': 'store', 'default': 'db.sqlite', 'required': False,
               'help': "Database in SQLITE format"}
    args_log_file = {'dest': 'log_file', 'action': 'store', 'help': "Write log to file.", 'required': False}
    args_log_verbosity = {'dest': 'log_verbosity', 'action': 'count', 'default': 0, 'required': False,
                          'help': "Set verbosity level, eg. None (Error level) -v (Info level)."}

    parser_vtam_main = None

    @classmethod
    def get_main_arg_parser(cls):
        """

        :return:
        """
        # create the top-level parser
        parser_vtam_main = argparse.ArgumentParser(add_help=False)
        parser_vtam_main.add_argument('--params', action='store', default=None, help="YML file with parameter values",
                                 required=False, type=ArgParserChecker.check_file_exists_and_is_nonempty)
        parser_vtam_main.add_argument('--log', **cls.args_log_file)
        parser_vtam_main.add_argument('--threads', action='store',
                                     help="Number of threads",
                                     required=False,
                                     default=multiprocessing.cpu_count())
        parser_vtam_main.add_argument('-v', **cls.args_log_verbosity)
        subparsers = parser_vtam_main.add_subparsers()

        # parser_vtam_wopmars = subparsers.add_parser('filter', add_help=True)
        # parser_vtam_wopmars.add_argument('--db', **cls.args_db)
        # parser_vtam_wopmars.add_argument('--dry-run', '-n', dest='dryrun', action='store_true', required=False,
        #                          help="Only display what would have been done.")
        # parser_vtam_wopmars.add_argument('-F', '--forceall', dest='forceall', action='store_true',
        #                          help="Force argument of WopMars", required=False)
        # parser_vtam_wopmars.add_argument('-t', '--targetrule', dest='targetrule', action='store', default=None,
        #                          help="Execute the workflow to the given target RULE: SampleInformation, ...",
        #                          required=False)
        # parser_vtam_wopmars.add_argument('-f', '--sourcerule', dest='sourcerule', action='store', default=None,
        #                          help="Execute the workflow from the given RULE.", required=False)

        ################################################################################################################
        #
        # create the parser for the "merge" command
        #
        ################################################################################################################

        cls.create_merge(subparsers=subparsers, parent_parser=parser_vtam_main)

        ################################################################################################################
        #
        # create the parser for the "sortreads" command
        #
        ################################################################################################################

        cls.create_sortreads(subparsers=subparsers, parent_parser=parser_vtam_main)

        ################################################################################################################
        #
        # create the parser for the "filter" command
        #
        ################################################################################################################

        cls.create_filter(subparsers=subparsers, parent_parser=parser_vtam_main)

        ################################################################################################################
        #
        # create the parser for the "optimize" command
        #
        ################################################################################################################

        cls.create_optimize(subparsers=subparsers, parent_parser=parser_vtam_main)

        ################################################################################################################
        #
        # create the parser for the "poolmarkers" command
        #
        ################################################################################################################

        cls.create_poolmarkers(subparsers=subparsers)

        ################################################################################################################
        #
        # create the parser for the "taxassign" command
        #
        ################################################################################################################

        cls.create_taxassign(subparsers=subparsers)

        ################################################################################################################
        #
        # create the parser for the "taxonomy" command
        #
        ################################################################################################################

        cls.create_taxonomy(subparsers=subparsers)

        ################################################################################################################
        #
        # create the parser for the "coi_db" command
        #
        ################################################################################################################

        cls.create_coiblastdb(subparsers=subparsers)

        return parser_vtam_main

    @classmethod
    def create_merge(cls, subparsers, parent_parser):

        parser_vtam_merge = subparsers.add_parser('merge', add_help=True, formatter_class=argparse.RawTextHelpFormatter,
                                                  parents=[parent_parser])
        parser_vtam_merge.add_argument('--fastqinfo', action='store', help="TSV file with FASTQ sample information",
                                       required=True,
                                       type=ArgParserChecker.check_file_exists_and_is_nonempty)
        parser_vtam_merge\
            .add_argument('--fastainfo', action='store', help="REQUIRED: Output TSV file for FASTA sample information",
                          required=True)
        parser_vtam_merge.add_argument('--fastqdir', action='store', help="Directory with FASTQ files", required=True,
                                       type=ArgParserChecker.check_dir_exists_and_is_nonempty)
        parser_vtam_merge.add_argument('--fastadir', action='store', help="Directory with FASTA files", required=True)
        parser_vtam_merge.set_defaults(command='merge')  # This attribute will trigger the good command

    @classmethod
    def create_sortreads(cls, subparsers, parent_parser):

        parser_vtam_sortreads = subparsers.add_parser('sortreads', add_help=True, formatter_class=argparse.RawTextHelpFormatter,
                                                  parents=[parent_parser])
        parser_vtam_sortreads\
            .add_argument('--fastainfo', action='store', help="REQUIRED: TSV file with FASTA information",
                          required=True, type=ArgParserChecker.check_file_exists_and_is_nonempty)
        parser_vtam_sortreads.add_argument('--fastadir', action='store', help="REQUIRED: Directory with FASTA files",
                                        required=True,
                                        type=ArgParserChecker.check_dir_exists_and_is_nonempty)
        parser_vtam_sortreads.add_argument('--outdir', action='store',
                                   help="REQUIRED: Output directory for trimmed and demultiplexed files", default="out",
                                     required=True)
        parser_vtam_sortreads.set_defaults(command='sortreads')  # This attribute will trigger the good command

    @classmethod
    def create_filter(cls, subparsers, parent_parser):

        parser_vtam_filter = subparsers.add_parser('filter', add_help=True, parents=[parent_parser])

        parser_vtam_filter\
            .add_argument('--fastainfo', action='store', help="REQUIRED: TSV file with FASTA sample information",
                          required=True, type=ArgParserChecker.check_file_exists_and_is_nonempty)
        parser_vtam_filter.add_argument('--fastadir', action='store', help="REQUIRED: Directory with FASTA files",
                                        required=True,
                                        type=ArgParserChecker.check_dir_exists_and_is_nonempty)
        # parser_vtam_filter\
        #     .add_argument('--sampleselect', action='store',
        #                   help="""REQUIRED: TSV file with sample selection and at least the two columns Run
        #                              and Marker.
        #                              Additionally, the columns Biosample and Replicate can be given
        #                                 Example:
        #                                 Run	Marker
        #                                 prerun	MFZR
        #                                 prerun	ZFZR""",
        #                   required=True, type=ArgParserChecker.check_parser_filter_arg_sampleselect)
        parser_vtam_filter.add_argument('--outdir', action='store', help="REQUIRED: Directory for output", default="out",
                                     required=True)
        parser_vtam_filter.add_argument('--threshold_specific', default=None, action='store', required=False,
                                 help="TSV file with variant (col1: variant; col2: threshold) or variant-replicate "
                                  "(col1: variant; col2: replicate; col3: threshold)specific thresholds. Header expected.",
                                 type=ArgParserChecker.check_file_exists_and_is_nonempty)

        ################################################################################################################
        #
        # Wopmars args
        #
        ################################################################################################################

        parser_vtam_filter.add_argument('--db', **cls.args_db)
        parser_vtam_filter.add_argument('--dry-run', '-n', dest='dryrun', action='store_true', required=False,
                                 help="Only display what would have been done.")
        parser_vtam_filter.add_argument('-F', '--forceall', dest='forceall', action='store_true',
                                 help="Force argument of WopMars", required=False)
        parser_vtam_filter.add_argument('-t', '--targetrule', dest='targetrule', action='store', default=None,
                                 help="Execute the workflow to the given target RULE: SampleInformation, ...",
                                 required=False)
        parser_vtam_filter.add_argument('-f', '--sourcerule', dest='sourcerule', action='store', default=None,
                                 help="Execute the workflow from the given RULE.", required=False)

        parser_vtam_filter.set_defaults(command='filter')  # This attribute will trigger the good command

    @classmethod
    def create_optimize(cls, subparsers, parent_parser):

        parser_vtam_optimize = subparsers.add_parser('optimize', add_help=True,  parents=[parent_parser])
        parser_vtam_optimize\
            .add_argument('--fastainfo', action='store', help="REQUIRED: TSV file with FASTA sample information",
                          required=True, type=ArgParserChecker.check_file_exists_and_is_nonempty)
        parser_vtam_optimize.add_argument('--fastadir', action='store', help="REQUIRED: Directory with FASTA files",
                                          required=True,
                                          type=ArgParserChecker.check_file_exists_and_is_nonempty)
        parser_vtam_optimize.add_argument('--outdir', action='store', help="Directory for output", default="out",
                                          required=True)
        parser_vtam_optimize.add_argument('--variant_known', action='store', help="TSV file with known variants",
                                          required=True)

        ################################################################################################################
        #
        # Wopmars args
        #
        ################################################################################################################

        parser_vtam_optimize.add_argument('--db', **cls.args_db)
        parser_vtam_optimize.add_argument('--dry-run', '-n', dest='dryrun', action='store_true', required=False,
                                 help="Only display what would have been done.")
        parser_vtam_optimize.add_argument('-F', '--forceall', dest='forceall', action='store_true',
                                 help="Force argument of WopMars", required=False)
        parser_vtam_optimize.add_argument('-t', '--targetrule', dest='targetrule', action='store', default=None,
                                 help="Execute the workflow to the given target RULE: SampleInformation, ...",
                                 required=False)
        parser_vtam_optimize.add_argument('-f', '--sourcerule', dest='sourcerule', action='store', default=None,
                                 help="Execute the workflow from the given RULE.", required=False)

        parser_vtam_optimize.set_defaults(command='optimize')  # This attribute will trigger the good command

    @classmethod
    def create_poolmarkers(cls, subparsers):

        parser_vtam_pool_markers = subparsers.add_parser('poolmarkers', add_help=True, formatter_class=argparse.RawTextHelpFormatter)
        parser_vtam_pool_markers.add_argument('--db', action='store', required=True, help="SQLITE file with DB")
        parser_vtam_pool_markers.add_argument('--runmarker', action='store', default=None,
                                     help="""Input TSV file with two columns and headers 'run_name' and 'marker_name'.
                                        Example:
                                        run_name	marker_name
                                        prerun	MFZR
                                        prerun	ZFZR""",
                                     required=True, type=lambda x: ArgParserChecker.check_parser_poolmarkers_arg_runmarker(x,
                                                                                                                           error_message="""Verify the '--pooledmarkers' argument: 
                                      It is an input TSV file with two columns and headers 'run_name' and 'marker_name'.
                                        Default: Uses all runs and markers in the DB
                                        Example:
                                        run_name	marker_name
                                        prerun	MFZR
                                        prerun	ZFZR"""))
        parser_vtam_pool_markers.add_argument('--pooledmarkers', action='store', help="REQUIRED: Output TSV file with pooled markers",
                                       required=True)

        parser_vtam_pool_markers.set_defaults(command='poolmarkers')  # This attribute will trigger the good command

    @classmethod
    def create_taxassign(cls, subparsers):

        parser_vtam_taxassign = subparsers.add_parser('taxassign', add_help=True, formatter_class=argparse.RawTextHelpFormatter)

        parser_vtam_taxassign\
            .add_argument('--variants', action='store', help="REQUIRED: TSV file with variant sequences and sequence header in the last column.",
                          required=True, type=lambda x: ArgParserChecker
                          .check_parser_taxassign_arg_variants(x,
                                                               error_message="""The --variants TSV file requires a header with a 'sequence' label and the sequences in the last column"""))
        parser_vtam_taxassign\
            .add_argument('--variant_taxa', action='store', help="REQUIRED: TSV file where the taxon assignation has beeen added.",
                          required=True)
        parser_vtam_taxassign.add_argument('--mode', dest='mode', default="unassigned", action='store', required=False,
                                           choices=['unassigned', 'reset'],
                                 help="The default 'unassigned' mode will only assign 'unassigned' variants."
                                      "The alternative 'reset' mode will erase the TaxAssign table and reassigned all "
                                      "input variants.")
        parser_vtam_taxassign.add_argument('--db', **cls.args_db)
        parser_vtam_taxassign.add_argument('--log', **cls.args_log_file)
        parser_vtam_taxassign.add_argument('-v', **cls.args_log_verbosity)
        parser_vtam_taxassign.add_argument('--threads', action='store',
                                     help="Number of threads",
                                     required=False,
                                     default=multiprocessing.cpu_count())
        parser_vtam_taxassign.add_argument('--blastdbdir', action='store',
                                           help="REQUIRED: Blast DB directory (Full or custom one) with DB files.",
                                           required=True, type=ArgParserChecker.check_dir_exists_and_is_nonempty)
        parser_vtam_taxassign.add_argument('--blastdbname', action='store',
                                     help="REQUIRED: Blast DB name. It corresponds to file name (without suffix)"
                                          "of blast DB files.",
                                     required=True)
        parser_vtam_taxassign.add_argument('--taxonomy', dest='taxonomy', action='store',
                                           help="""REQUIRED: SQLITE DB with taxonomy information.

        This database is create with the command: vtam taxonomy. For instance

        vtam taxonomy -o taxonomy.sqlite to create a database in the current directory.""",
                                           required=True,
                                           type=ArgParserChecker.check_file_exists_and_is_nonempty)
        parser_vtam_taxassign.add_argument('--ltg_rule_threshold', default=97, type=ArgParserChecker.check_real_between_0_and_100,
                                           required=False,
                                           help="Identity threshold to use either 'include_prop' parameter "
                                                "(blast identity>=ltg_rule_threshold) or use 'min_number_of_taxa' "
                                                "parameter  (blast identity<ltg_rule_threshold)")
        parser_vtam_taxassign.add_argument('--include_prop', action='store', default=90, type=ArgParserChecker.check_real_between_0_and_100,
                                           required=False,
                                           help="Determine the Lowest Taxonomic Group "
                                                "(LTG) that contains at least the include_prop percentage of the hits.")
        parser_vtam_taxassign.add_argument('--min_number_of_taxa', default=3, type=ArgParserChecker.check_real_positive,
                                           required=False,
                                           help="Determine the Lowest Taxonomic Group (LTG) "
                                                "only if selected hits contain at least --min_number_of_taxa different taxa")

        parser_vtam_taxassign.set_defaults(command='taxassign')  # This attribute will trigger the good command

    @classmethod
    def create_taxonomy(cls, subparsers):

        parser_vtam_taxonomy = subparsers.add_parser('taxonomy', add_help=True)
        parser_vtam_taxonomy.add_argument('-o', '--output', dest='output', action='store', help="Path to TSV taxonomy file",
                            required=True)
        parser_vtam_taxonomy.add_argument('--precomputed', dest='precomputed', action='store_true', default=False,
                            help="Will download precomputed taxonomy database, which is likely not the most recent one.",
                            required=False)
        parser_vtam_taxonomy.set_defaults(command='taxonomy')  # This attribute will trigger the good command

    @classmethod
    def create_coiblastdb(cls, subparsers):

        parser_vtam_coi_blast_db = subparsers.add_parser('coi_blast_db', add_help=True)
        parser_vtam_coi_blast_db.add_argument('--coi_blast_db', dest='coi_blast_db', action='store', help="Path COI Blast DB",
                            required=True)
        parser_vtam_coi_blast_db.set_defaults(command='coi_blast_db')  # This attribute will trigger the good command
