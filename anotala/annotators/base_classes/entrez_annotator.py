import logging

import Bio
from Bio import Entrez
from tqdm import tqdm

from anotala.annotators.base_classes import WebAnnotatorWithCache
from anotala.helpers import set_email_for_entrez, grouped


logger = logging.getLogger(__name__)


class EntrezAnnotator(WebAnnotatorWithCache):
    """
    Base class for annotators that use one of Entrez services. Classes that
    inherit from this one should have:

        - class variable SOURCE_NAME, the name that will be used to create
          the database table.

        - class variable ENTREZ_SERVICE: (epost|esummary|efetch),
          lets you choose between epost, efetch and esummary services.

        - class variable ENTREZ_PARAMS like:
          {'db': 'clinvar', 'rettype': 'clinvarset'}
          These params will be passed as kwargs to the SERVICE you choose.

        - a static or class method _annotations_by_id(ids, raw_response) that
          takes the raw response with info for many ids and yields tuples of
          (id, data) for each of the queried IDs, thus splitting the many-IDs
          response *per ID*.

        - optionally, a static or class method _parse_id(id_) method that
          will transform the IDs in any way prior to the query. This is useful,
          for instance, to remove 'rs' from rs IDs.

        - optionally, a USE_ENTREZ_READER class variable to indicate that the
          response from Entrez should be handled by Entrez.read(). This works
          for some but not all DBs.

        - as any WebAnnotatorWithCache, a _parse_annotation static or classmethod
    """
    def _batch_query(self, ids):
        """
        Use Entrez query service to fetch a list of IDs in batches, in the
        database defined in self.ENTREZ_PARAMS['db']. Yields dictionaries with
        the annotations of each batch.

        If self.USE_ENTREZ_READER is set, the raw response will be handled by
        Entrez.read() method, instead of returned as is.
        """
        if hasattr(self, '_parse_id'):
            ids = [self._parse_id(id_) for id_ in ids]

        if not Entrez.email:
            set_email_for_entrez()

        #
        # NOTE: The proxies for Biopython's Entrez are commented out because
        # when set (socks5://localhost:9050) they break the UniprotAnnotator,
        # which uses Bio.ExPASy.get_sprot_raw().
        #
        # I tried to fix this by unsetting the ENV variable after the
        # annotation (code commented below), but the Uniprot annotation still
        # breaks.
        #
        #  if self.proxies:
            #  original_http_proxy_value = os.environ.get('http_proxy')
            #  # Biopython's Entrez service uses proxies when they're set as
            #  # an env variable 'http_proxy'. See:
            #  # http://biopython.org/DIST/docs/tutorial/Tutorial.html#htoc126
            #  os.environ['http_proxy'] = self.proxies['http']

        total = len(ids)
        logger.info('Fetch {} entries from Entrez "{}" in batches of {}'
                    .format(total, self.ENTREZ_PARAMS['db'],
                            min(self.batch_size, total)))

        for ids_group, handle in self._query_method(list(ids)):
            if hasattr(self, 'USE_ENTREZ_READER'):
                response = Entrez.read(handle)
            else:
                response = handle.read()
            handle.close()
            batch_annotations = self._annotations_by_id(ids_group, response)
            yield dict(batch_annotations)

        #
        # See the comment above ^. This code doesn't fix the problem.
        #
        #  # Restoring os.environ['http_proxy'] is important because
        #  # it can break other Entrez interfaces, like ExPASy.get_sprot_raw():
        #  if self.proxies:
            #  if original_http_proxy_value:
                #  os.environ['http_proxy'] = original_http_proxy_value
            #  else:
                #  del(os.environ['http_proxy'])

    @property
    def _query_method(self):
        query_methods = {
            'epost': self._epost_query,
            'esummary': self._esummary_query,
            'efetch': self._efetch_query,
        }
        return query_methods[self.ENTREZ_SERVICE]

    @property
    def batch_size(self):
        if hasattr(self, 'BATCH_SIZE'):
            return self.BATCH_SIZE

        batch_sizes = {
            'epost': 1000,
            'esummary': 200,
            'efetch': 50,
        }
        return batch_sizes[self.ENTREZ_SERVICE]

    def _efetch_query(self, ids):
        n_batchs = len(ids)//self.batch_size
        for ids_group in tqdm(grouped(ids, self.batch_size), total=n_batchs):
            handle = Entrez.efetch(id=','.join(ids_group),
                                   **self.ENTREZ_PARAMS)
            yield ids_group, handle


    def _esummary_query(self, ids):
        n_batchs = len(ids)//self.batch_size
        for ids_group in tqdm(grouped(ids, self.batch_size), total=n_batchs):
            handle = Entrez.esummary(db=self.ENTREZ_PARAMS['db'],
                                     id=','.join(ids_group))
            yield ids_group, handle

    def _epost_query(self, ids):
        # Entrez POST queries are a two step process. You first POST your query
        # and get a WebEnv identifier and a QueryKey.
        logger.info('Create a serverside Job and get its ID')
        handle = Entrez.epost(db=self.ENTREZ_PARAMS['db'], id=','.join(ids))
        job_data = Entrez.read(handle)

        # Then you do a second query using the job data, and you get the
        # results in batches. More info:
        # http://biopython.org/DIST/docs/tutorial/Tutorial.html#sec:entrez-webenv
        logger.info('Get the results from the job in batches')
        for offset in tqdm(list(range(0, len(ids), self.batch_size))):
            fetch_handle = Entrez.efetch(
                    db=self.ENTREZ_PARAMS['db'],
                    retmode=self.ENTREZ_PARAMS['retmode'],
                    webenv=job_data['WebEnv'], query_key=job_data['QueryKey'],
                    retstart=offset, retmax=self.batch_size
                )

            yield ids[offset:offset+self.batch_size], fetch_handle

    @classmethod
    def _parse_element(cls, element):
        parse_functions = {
            Bio.Entrez.Parser.ListElement: cls._parse_listelement,
            list: cls._parse_listelement,
            Bio.Entrez.Parser.StringElement: cls._parse_stringelement,
            Bio.Entrez.Parser.DictionaryElement: cls._parse_dictelement,
            dict: cls._parse_dictelement,
            Bio.Entrez.Parser.StructureElement: cls._parse_dictelement,
        }

        if type(element) in parse_functions:
            return parse_functions[type(element)](element)
        else:
            return element

    @classmethod
    def _parse_listelement(cls, listelement):
        return [cls._parse_element(e) for e in listelement]

    @classmethod
    def _parse_dictelement(cls, dictelement):
        return {key: cls._parse_element(e) for key, e in dictelement.items()}

    @staticmethod
    def _parse_stringelement(stringelement):
        if hasattr(stringelement, 'attributes'):
            return {**stringelement.attributes, 'value': str(stringelement)}
        else:
            return str(stringelement)

    @classmethod
    def _parse_record(cls, record):
        return {key: cls._parse_element(val) for key, val in record.items()}

    @staticmethod
    def _annotations_by_id(ids, raw_response):
        raise NotImplementedError

