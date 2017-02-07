import requests
import json
import time
import logging

from tqdm import tqdm

from anotamela.annotators.base_classes import AnnotatorWithCache
from anotamela.helpers import grouped


logger = logging.getLogger(__name__)


class EnsemblAnnotator(AnnotatorWithCache):
    """
    Annotates rsids with Ensembl! REST service via POST requests.

    Set EnsemblAnnotator.full_info = True to get phenotypes, genotypes and
    population info besides the basic variant annotations.
    """
    SOURCE_NAME = 'ensembl'
    ANNOTATIONS_ARE_JSON = True
    BATCH_SIZE = 25
    # In theory Ensembl POST requests can handle up to 1,000 variants,
    # but I get timeouts when I try to get the full info for as low as 100
    # variants at a time.
    SLEEP_TIME = 0

    api_version = 'GRCh37'
    full_info = False

    @classmethod
    def _batch_query(cls, ids):
        for group_of_ids in tqdm(grouped(ids, cls.BATCH_SIZE, as_list=True)):
            yield cls._post_query(group_of_ids)
            time.sleep(cls.SLEEP_TIME)

    @classmethod
    def _post_query(cls, ids):
        """
        Do a POST request to Ensembl REST api for a group of *ids*. Returns
        a dictionary with annotations per id. Requests should be done in
        batches of 1000 or less.
        """
        # No prefix needed for GRCh38
        url_prefix = 'grch37.' if cls.api_version == 'GRCh37' else ''
        url = ('http://{}rest.ensembl.org/variation/homo_sapiens/?'
               .format(url_prefix))

        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}

        params = {'phenotypes': '1',
                  'genotypes': '1',
                  'pops': '1',
                  'population_genotypes': '1'}
        for key, value in params.items():
            url += '{}={};'.format(key, value)

        payload = {'ids': list(ids)}

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.ok:
            return response.json()
        else:
            logger.warn('Ensembl Error: {}'.format(response.text))
            response.raise_for_status()

    @classmethod
    def _parse_annotation(cls, annotation):
        if not cls.full_info:
            keys_to_remove = [
                'populations',
                'population_genotypes',
                'genotypes'
            ]
            for key in keys_to_remove:
                del(annotation[key])

        maf = annotation.get('MAF')
        if maf:
            annotation['MAF'] = float(maf)

        return annotation

