import sys

from vtam.utils.FilterChimeraRunner import FilterChimeraRunner
from vtam.utils.Logger import Logger
from vtam.utils.SampleInformationFile import SampleInformationFile
from vtam.utils.VTAMexception import VTAMexception
from vtam.utils.VariantReadCountLikeDF import VariantReadCountLikeDF
from wopmars.models.ToolWrapper import ToolWrapper


class FilterChimera(ToolWrapper):
    __mapper_args__ = {
        "polymorphic_identity": "vtam.wrapper.FilterChimera"
    }

    # Input file
    __input_file_readinfo = "readinfo"
    # Input table
    __input_table_marker = "Marker"
    __input_table_run = "Run"
    __input_table_biosample = "Biosample"
    __input_table_filter_pcr_error = "FilterPCRerror"
    __input_table_Variant = "Variant"
    # Output table
    __output_table_filter_chimera = "FilterChimera"
    __output_table_filter_chimera_borderline = "FilterChimeraBorderline"


    def specify_input_file(self):
        return[
            FilterChimera.__input_file_readinfo,

        ]

    def specify_input_table(self):
        return [
            FilterChimera.__input_table_marker,
            FilterChimera.__input_table_run,
            FilterChimera.__input_table_biosample,
            FilterChimera.__input_table_filter_pcr_error,
            FilterChimera.__input_table_Variant,
        ]


    def specify_output_table(self):
        return [
            FilterChimera.__output_table_filter_chimera,
            FilterChimera.__output_table_filter_chimera_borderline,
        ]

    def specify_params(self):
        return{
            "uchime3_denovo_abskew": "float",
        }

    def run(self):
        session = self.session
        engine = session._session().get_bind()

        ############################################################################################
        #
        # Wrapper inputs, outputs and parameters
        #
        ############################################################################################

        # Input file output
        fasta_info_tsv = self.input_file(FilterChimera.__input_file_readinfo)
        #
        # Input table models
        # Variant = self.input_table(FilterChimera.__input_table_Variant)
        input_filter_pcr_error_model = self.input_table(FilterChimera.__input_table_filter_pcr_error)
        #
        # Output table models
        output_filter_chimera_model = self.output_table(FilterChimera.__output_table_filter_chimera)
        output_filter_borderline_model = self.output_table(FilterChimera.__output_table_filter_chimera_borderline)
        #
        # Params
        uchime3_denovo_abskew = self.option("uchime3_denovo_abskew")

        ############################################################################################
        #
        # 1. Read readinfo to get run_id, marker_id, biosample_id, replicate for current analysis
        # 2. Delete marker/run/biosample/replicate from variant_read_count_model
        # 3. Get variant_read_count_df input
        #
        ############################################################################################

        sample_info_tsv_obj = SampleInformationFile(tsv_path=fasta_info_tsv)

        sample_info_tsv_obj.delete_from_db(engine=engine, variant_read_count_like_model=output_filter_chimera_model)

        sample_info_tsv_obj.delete_from_db(engine=engine, variant_read_count_like_model=output_filter_borderline_model)

        variant_read_count_df = sample_info_tsv_obj.get_variant_read_count_df(
            variant_read_count_like_model=input_filter_pcr_error_model, engine=engine, filter_id=None)

        ################################################################################################################
        #
        # 4. Run Filter
        #
        ################################################################################################################

        variant_df = sample_info_tsv_obj.get_variant_df(variant_read_count_like_model=input_filter_pcr_error_model, engine=engine)
        filter_chimera_runner = FilterChimeraRunner(variant_read_count_df=variant_read_count_df)
        filter_output_chimera_df, filter_borderline_output_df = filter_chimera_runner.get_variant_read_count_delete_df(
            variant_df=variant_df, uchime3_denovo_abskew=uchime3_denovo_abskew)

        ################################################################################################################
        #
        # 5. Write to DB
        # 6. Touch output tables, to update modification date
        # 7. Exit vtam if all variants delete
        #
        ################################################################################################################
        
        VariantReadCountLikeDF(filter_output_chimera_df).to_sql(
            engine=engine, variant_read_count_like_model=output_filter_chimera_model)

        VariantReadCountLikeDF(filter_borderline_output_df).to_sql(
            engine=engine, variant_read_count_like_model=output_filter_borderline_model)

        for output_table_i in self.specify_output_table():
            declarative_meta_i = self.output_table(output_table_i)
            obj = session.query(declarative_meta_i).order_by(declarative_meta_i.id.desc()).first()
            session.query(declarative_meta_i).filter_by(id=obj.id).update({'id': obj.id})
            session.commit()

        if filter_output_chimera_df.filter_delete.sum() == filter_output_chimera_df.shape[0]:
            Logger.instance().warning(VTAMexception("This filter has deleted all the variants: {}. "
                                                    "The analysis will stop here.".format(self.__class__.__name__)))
            sys.exit(0)
