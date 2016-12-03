import pytest

from anotamela.annotators import (
        DbsnpWebAnnotator,
        DbsnpEntrezAnnotator,
        ClinvarRsAnnotator
    )


test_params = [
        (DbsnpWebAnnotator, {
            'ids_to_annotate': ('rs268 rs123'),
            'keys_to_check': ('snp_id orgStr supported_assm is_clinical '
                              'assembly org')
        }),
        (DbsnpEntrezAnnotator, {
            'ids_to_annotate': ('rs268'),
            'keys_to_check': ('hgvs alleles type links fxn '
                              'clinical_significance synonyms frequency')
        }),
        (ClinvarRsAnnotator, {
            'ids_to_annotate': ('rs268 rs199473059'),
            'keys_to_check': ('alt gene rsid rcv type cytogenic hgvs '
                              'variant_id hg19 ref chrom hg38 allele_id')
        })
    ]

@pytest.mark.parametrize('annotator_class,params', test_params)

def test_generic_annotator(annotator_class, params):
    ids_to_annotate = params['ids_to_annotate'].split()
    annotator = annotator_class(cache='mock_cache')
    info_dict = annotator.annotate(ids_to_annotate)

    for id_ in ids_to_annotate:
        assert info_dict[id_]
        for key in params['keys_to_check'].split():
            print(id_, key)
            assert info_dict[id_][key]

