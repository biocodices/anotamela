import pandas as pd

from anotamela.annotators.base_classes import AnnotatorWithCache
from anotamela.annotators import OmimGeneAnnotator


class OmimVariantAnnotator(AnnotatorWithCache):
    """
    Provider of OMIM annotations for gene variants (e.g. 605557.0001).
    Responses are cached.

        > omim_variant_annotator = OmimVariantAnnotator()
        > omim_variant_annotator.annotate('605557.0001')
        # => { '605557.0001': ... }

    The base sleep time between requests is 60s because OMIM is quite strict
    against crawlers. However, you can lower this value at your own risk:

        > omim_variant_annotator.SLEEP_TIME = 30

    SLEEP_TIME is used as a base value that will be randomized each time.
    The user agent of each request is also randomized.
    """
    SOURCE_NAME = 'omim_variants'
    ANNOTATIONS_ARE_JSON = True

    # These attributes will be used for the OmimGeneAnnotator:
    BATCH_SIZE = 1
    SLEEP_TIME = 60
    PROXIES = {}

    def _batch_query(self, ids):
        """
        This annotator uses OmimGeneAnnotator to get all the variants in a
        given gene, and then extract the variants that were requested.
        The gene annotation step is necessary because OMIM variant info is in
        that variant's gene entry, which has to be parsed completely before we
        can extract the variant bit. In the process, the OmimGeneAnnotator
        will cache the gene data, so annotating many variants from a single
        gene will be a fast process.
        """
        # OMIM variant IDs are like 605557.0001, where 605557 is a gene ID
        gene_ids = {id_.split('.')[0] for id_ in ids}
        # Annotate the genes where the variants are located
        gene_dataframes = self.omim_gene_annotator.annotate(gene_ids)
        df = pd.concat(gene_dataframes.values())

        # Check each variant has a single row in the dataframe:
        df = df.set_index('variant_id', drop=False)
        assert len(df.index) == len(set(df.index))

        # From all the gene variants, only keep the ones that were queried
        found_ids = df.index & ids
        annotations = df.loc[found_ids].to_dict('index')
        yield annotations

    @property
    def omim_gene_annotator(self):
        if not hasattr(self, '_omim_gene_annotator'):
            self._omim_gene_annotator = OmimGeneAnnotator(cache=self.cache)
            self._omim_gene_annotator.BATCH_SIZE = self.BATCH_SIZE
            self._omim_gene_annotator.SLEEP_TIME = self.SLEEP_TIME
            self._omim_gene_annotator.PROXIES = self.PROXIES

        return self._omim_gene_annotator

