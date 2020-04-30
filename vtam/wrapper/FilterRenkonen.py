from vtam import Logger
from vtam.utils.FilterRenkonenRunner import FilterRenkonenRunner
from vtam.utils.SampleInformationUtils import FastaInformationTSV
from vtam.utils.VariantReadCountLikeTable import VariantReadCountLikeTable
from vtam.utils.VTAMexception import VTAMexception
from wopmars.models.ToolWrapper import ToolWrapper

import pandas
import sys


class FilterRenkonen(ToolWrapper):
    __mapper_args__ = {
        "polymorphic_identity": "vtam.wrapper.FilterRenkonen"
    }

    # Input file
    __input_file_readinfo = "readinfo"
    # Input table
    __input_table_marker = "Marker"
    __input_table_run = "Run"
    __input_table_biosample = "Biosample"
    __input_table_chimera = "FilterChimera"
    # Output table
    __output_table_filter_renkonen = "FilterRenkonen"

    def specify_input_file(self):
        return [
            FilterRenkonen.__input_file_readinfo,

        ]

    def specify_input_table(self):
        return [
            FilterRenkonen.__input_table_marker,
            FilterRenkonen.__input_table_run,
            FilterRenkonen.__input_table_biosample,
            FilterRenkonen.__input_table_chimera,
        ]

    def specify_output_table(self):
        return [
            FilterRenkonen.__output_table_filter_renkonen,
        ]

    def specify_params(self):
        return {
            "renkonen_distance_quantile": "float",
        }

    def run(self):
        session = self.session
        engine = session._session().get_bind()

        ################################################################################################################
        #
        # Wrapper inputs, outputs and parameters
        #
        ################################################################################################################
        #
        # Input file output
        fasta_info_tsv = self.input_file(FilterRenkonen.__input_file_readinfo)
        #
        # Input table models
        marker_model = self.input_table(FilterRenkonen.__input_table_marker)
        run_model = self.input_table(FilterRenkonen.__input_table_run)
        biosample_model = self.input_table(FilterRenkonen.__input_table_biosample)
        input_filter_chimera_model = self.input_table(FilterRenkonen.__input_table_chimera)
        #
        # Options
        # PoolMarkers parameters
        renkonen_distance_quantile = float(self.option("renkonen_distance_quantile"))
        #
        # Output table models
        output_filter_renkonen_model = self.output_table(FilterRenkonen.__output_table_filter_renkonen)

        ################################################################################################################
        #
        # 1. Read readinfo to get run_id, marker_id, biosample_id, replicate for current analysis
        #
        ################################################################################################################

        fasta_info_tsv = FastaInformationTSV(engine=engine, fasta_info_tsv=fasta_info_tsv)

        ################################################################################################################
        #
        # 2. Delete marker/run/biosample/replicate from variant_read_count_model
        #
        ################################################################################################################

        variant_read_count_like_utils = VariantReadCountLikeTable(variant_read_count_like_model=output_filter_renkonen_model, engine=engine)
        variant_read_count_like_utils.delete_from_db(sample_record_list=fasta_info_tsv.sample_record_list)

        ################################################################################################################
        #
        # variant_read_count_input_df
        #
        ################################################################################################################

        variant_read_count_df = fasta_info_tsv.get_variant_read_count_df(
            variant_read_count_like_model=input_filter_chimera_model, filter_id=None)

        ################################################################################################################
        #
        # Run per run_id, marker_id
        #
        ################################################################################################################

        filter_output_df = pandas.DataFrame()
        run_marker_df = variant_read_count_df[['run_id', 'marker_id']].drop_duplicates()

        for row in run_marker_df.itertuples():
            run_id = row.run_id
            marker_id = row.marker_id

            variant_read_count_per_run_marker_df = variant_read_count_df.loc[
                (variant_read_count_df.run_id == run_id) & (variant_read_count_df.marker_id == marker_id)]

            if variant_read_count_per_run_marker_df.replicate.unique().shape[0] > 1:  # if more than one replicate
                filter_renkonen_runner_obj = FilterRenkonenRunner(variant_read_count_per_run_marker_df)
                filter_output_i_df = filter_renkonen_runner_obj.get_filter_output_df(renkonen_distance_quantile)
                # filter_output_df = f12_filter_delete_renkonen(variant_read_count_df, renkonen_distance_quantile)
            else:  # Just one replicate
                filter_output_i_df = variant_read_count_df.copy()
                filter_output_i_df['filter_delete'] = False

            filter_output_df = pandas.concat([filter_output_df, filter_output_i_df], axis=0)

        ################################################################################################################
        #
        # Write to DB
        #
        ################################################################################################################

        record_list = VariantReadCountLikeTable.filter_delete_df_to_dict(filter_output_df)
        with engine.connect() as conn:

            # Insert new instances
            conn.execute(output_filter_renkonen_model.__table__.insert(), record_list)

        ################################################################################################################
        #
        # Touch output tables, to update modification date
        #
        ################################################################################################################

        for output_table_i in self.specify_output_table():
            declarative_meta_i = self.output_table(output_table_i)
            obj = session.query(declarative_meta_i).order_by(declarative_meta_i.id.desc()).first()
            session.query(declarative_meta_i).filter_by(id=obj.id).update({'id': obj.id})
            session.commit()

        ##########################################################
        #
        # Exit vtam if all variants deleted
        #
        ################################################################################################################

        if filter_output_df.filter_delete.sum() == filter_output_df.shape[0]:
            Logger.instance().warning(VTAMexception("This filter has deleted all the variants: {}. "
                                                    "The analysis will stop here.".format(self.__class__.__name__)))
            sys.exit(0)
