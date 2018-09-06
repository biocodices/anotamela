import os
import json
import pytest

from anotamela.recipes.annotate_vcf_rsids_with_clinvar import (
    annotate_rsids_with_clinvar,
    annotate_vcf_rsids_with_clinvar
)


@pytest.fixture
def vcf_path():
    return pytest.helpers.file('1_sample.vcf')


def test_annotate_vcf_rsids_with_clinvar(vcf_path, dict_cache):
    result = annotate_vcf_rsids_with_clinvar(
        vcf_path,
        cache=dict_cache
    )
    assert result[0]['dbsnp_id'] == 'rs268'

    out_fn = '/tmp/__anotamela_test_annotate_vcf_rsids_with_clinvar.json'
    try:
        result = annotate_vcf_rsids_with_clinvar(
            vcf_path,
            output_json_path=out_fn,
            cache=dict_cache
        )
        assert result == out_fn
        with open(out_fn) as f:
            annotations = json.load(f)
        assert annotations[0]['dbsnp_id'] == 'rs268'
    finally:
        os.remove(out_fn)


def test_annotate_rsids_with_clinvar(dict_cache):
    ids_to_annotate = [
        'rs268',  # SNP
        'rs1799990',  # Haplotype
    ]
    result = annotate_rsids_with_clinvar(ids_to_annotate,
                                         cache=dict_cache,
                                         grouped_by_rsid=True)

    # SNP:
    assert result['rs268'][0]['dbsnp_id'] == 'rs268'

    # Haplotype:
    #  assert result['rs1799990'][0]['dbsnp_ids'] == ['rs1799990', 'rs74315403']

    # Grouping by rs
    result = annotate_rsids_with_clinvar(['rs268', 'rsNonExistent'],
                                         cache=dict_cache,
                                         grouped_by_rsid=True)
    assert result['rs268'][0]['dbsnp_id'] == 'rs268'
    assert result['rsNonExistent'] == []


#  def test_annotate_position_tags_with_clinvar(dict_cache):
    #  ids_to_annotate = [
        #  'rs268',  # SNP
        #  'rs1799990',  # Haplotype
    #  ]
    #  result = annotate_rsids_with_clinvar(ids_to_annotate,
                                         #  cache=dict_cache,
                                         #  grouped_by_rsid=True)

    #  # SNP:
    #  assert result['rs268'][0]['dbsnp_id'] == 'rs268'

    #  # Haplotype:
    #  #  assert result['rs1799990'][0]['dbsnp_ids'] == ['rs1799990', 'rs74315403']

    #  # Grouping by rs
    #  result = annotate_rsids_with_clinvar(['rs268', 'rsNonExistent'],
                                         #  cache=dict_cache,
                                         #  grouped_by_rsid=True)
    #  assert result['rs268'][0]['dbsnp_id'] == 'rs268'
    #  assert result['rsNonExistent'] == []
