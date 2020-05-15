import pandas
import sqlalchemy
from wopmars.models.ToolWrapper import ToolWrapper

from vtam.models.Biosample import Biosample
from vtam.models.Marker import Marker
from vtam.models.Run import Run
from vtam.utils.AsvTableRunner import AsvTableRunner
from vtam.utils.SampleInformationFile import SampleInformationFile
from vtam.models.FilterCodonStop import FilterCodonStop


class MakeAsvTable(ToolWrapper):
    __mapper_args__ = {
        "polymorphic_identity": "vtam.wrapper.MakeAsvTable"}

    # Input file
    __input_file_readinfo = "readinfo"
    # Input table
    __input_table_marker = "Marker"
    __input_table_run = "Run"
    __input_table_biosample = "Biosample"
    __input_table_filter_chimera_borderline = "FilterChimeraBorderline"
    __input_table_filter_codon_stop = "FilterCodonStop"
    __input_table_variant = "Variant"
    __input_table_tax_assign = "TaxAssign"

    # Output table
    __output_table_asv = "ASVTable"

    def specify_input_file(self):
        return[
            MakeAsvTable.__input_file_readinfo,
        ]

    def specify_input_table(self):
        return [
            MakeAsvTable.__input_table_marker,
            MakeAsvTable.__input_table_run,
            MakeAsvTable.__input_table_biosample,
            MakeAsvTable.__input_table_variant,
            MakeAsvTable.__input_table_filter_chimera_borderline,
            MakeAsvTable.__input_table_filter_codon_stop,
        ]

    def specify_output_file(self):
        return[
            MakeAsvTable.__output_table_asv,

        ]

    def specify_params(self):
        return {
            "foo": "int",
        }

    def run(self):
        session = self.session
        engine = session._session().get_bind()

        ################################################################################################################
        #
        # 1. Wrapper inputs, outputs and parameters
        #
        ################################################################################################################

        # Input file
        fasta_info_tsv = self.input_file(MakeAsvTable.__input_file_readinfo)

        # Output file
        asv_table_tsv_path = self.output_file(MakeAsvTable.__output_table_asv)

        ################################################################################################################
        #
        # 1. Read readinfo to get run_id, marker_id, biosample_id, replicate for current analysis
        #  Compute variant_read_count_input_df and other dfs for the asv_table_runner
        #
        ################################################################################################################

        sample_info_tsv_obj = SampleInformationFile(tsv_path=fasta_info_tsv)

        variant_read_count_df = sample_info_tsv_obj.get_variant_read_count_df(FilterCodonStop, engine=engine)

        ################################################################################################################
        #
        # Compute variant_to_chimera_borderline_df
        #
        ################################################################################################################

        asv_table_runner = AsvTableRunner(engine, variant_read_count_df)
        asv_df_final = asv_table_runner.run()

        asv_df_final.to_csv(asv_table_tsv_path, sep='\t', index=False, header=True)
