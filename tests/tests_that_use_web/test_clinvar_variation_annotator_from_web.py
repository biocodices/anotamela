from anotala import ClinvarVariationAnnotator

import pytest


@pytest.fixture
def annotator():
    return ClinvarVariationAnnotator(cache='dict')


def test_annotate(annotator):
    result = annotator.annotate_one('1550')

    assert result['name'] == 'NM_000237.2(LPL):c.953A>G (p.Asn318Ser)'

    # Extracted from the variation name:
    assert result['prot_change'] == 'p.Asn318Ser'
    assert result['cds_change'] == 'c.953A>G'
    assert result['transcript'] == 'NM_000237.2'
    assert result['gene'] == 'LPL'

    assert result['variation_id'] == '1550'
    assert '1550' in result['url']
    assert 'c.953A>G' in result['variation_name']
    assert result['variation_type'] == 'Simple'

    assert len(result['genes']) == 1
    gene = result['genes'][0]
    assert gene['symbol'] == 'LPL'
    assert gene['entrez_id'] == '4023'
    assert gene['full_name'] == 'lipoprotein lipase'
    assert gene['strand'] == '+'
    assert gene['hgnc_id'] == '6677'

    assert len(result['clinical_assertions']) == 2
    clin = result['clinical_assertions'][0]
    assert clin['clinical_significances'] == ['Pathogenic']
    assert clin['date_last_submitted'] == '2017-12-03'
    assert clin['method'] == 'clinical testing'
    assert clin['submitter_name'] == \
            'Genomic Research Center,Shahid Beheshti University of Medical Sciences'
    assert clin['phenotypes'] == [
        {'name': 'Hyperapobetalipoproteinemia',
         'omim_id': '144250',
         'incidental': False}
    ]

    assert result['clinical_summary'] == {'Pathogenic': 2}

    alleles = result['alleles']
    assert len(alleles) == 1
    allele = alleles[0]

    assert allele['ref_g37'] == 'A'
    assert allele['alt_g37'] == 'G'
    assert allele['chrom_g37'] == '8'
    assert allele['genomic_change_g37'] == 'g.19813529A>G'
    assert allele['coding_changes'] == ['NM_000237.2:c.953A>G']
    assert allele['protein_changes'] == ['NP_000228.1:p.Asn318Ser']
    assert allele['length_g37'] == 1
    assert allele['frequencies']['G']['ExAC'] == 0.01336
    assert allele['variant_type'] == 'single nucleotide variant'
    assert allele['consequences'][0]['function'] == 'missense variant'

    assert result['associated_phenotypes'] == ['Hyperapobetalipoproteinemia']

