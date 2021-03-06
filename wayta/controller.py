# coding: utf-8

INDEXES_DOC_TYPE = {
    'wayta_institutions': 'institution',
    'wayta_countries': 'country',
}


class DataBroker(object):

    def __init__(self, es):
        self.es = es

    def _parse_data_countries(self, data, q):
        response = {
            'head': {
                'match': None,
            },
            'choices': []
        }

        if len(data['hits']['hits']) == 0:
            response['head']['match'] = False
            return response

        if data['hits']['hits'][0]['_source']['form'].lower() == q.lower():
            response['head']['match'] = 'exact'
            response['choices'].append(
                {
                    'value': data['hits']['hits'][0]['_source']['name'],
                    'score': data['hits']['hits'][0]['_score'],
                    'iso3166': data['hits']['hits'][0]['_source']['iso-3166']
                }
            )

            return response

        # Loading just the high scored choice
        choices = {}
        for hit in data['hits']['hits']:

            choices.setdefault(hit['_source']['name'], {
                'country': hit['_source']['name'],
                'score': float(hit['_score']),
                'iso3166': hit['_source']['iso-3166']
            })

        best_choices = []
        for choice, values in choices.items():
            best_choice = {
                'value': choice,
                'country': values['country'],
                'score': values['score'],
                'iso3166': values['iso3166']
            }

            best_choices.append(best_choice)

        response['choices'] = sorted(
            best_choices, key=lambda k: k['score'], reverse=True
        )

        if len(response['choices']) == 1:
            response['head']['match'] = 'by_similarity'
        else:
            response['head']['match'] = 'multiple'

        return response

    def _parse_data_institutions(self, data, q):

        response = {
            'head': {
                'match': None,
            },
            'choices': []
        }

        if len(data['hits']['hits']) == 0:
            response['head']['match'] = False
            return response

        if data['hits']['hits'][0]['_source']['form'].lower() == q.lower():
            response['head']['match'] = 'exact'
            response['choices'].append(
                {
                    'value': data['hits']['hits'][0]['_source'].get('name', ''),
                    'country':data['hits']['hits'][0]['_source'].get('country', ''),
                    'state':data['hits']['hits'][0]['_source'].get('state', ''),
                    'city':data['hits']['hits'][0]['_source'].get('city', ''),
                    'iso3166':data['hits']['hits'][0]['_source'].get('iso-3166', ''),
                    'score': data['hits']['hits'][0]['_score']
                }
            )

            return response

        # Loading just the high scored choice
        choices = {}
        for hit in data['hits']['hits']:
            choices.setdefault(hit['_source']['name'], {
                'country': hit['_source'].get('country', ''),
                'state': hit['_source'].get('state', ''),
                'city': hit['_source'].get('city', ''),
                'iso3166': hit['_source'].get('iso-3166', ''),
                'score': float(hit['_score'])
            })

        best_choices = []
        for choice, values in choices.items():
            best_choice = {
                'value': choice,
                'country': values['country'],
                'state': values['state'],
                'city': values['city'],
                'iso3166': values['iso3166'],
                'score': values['score']
            }

            best_choices.append(best_choice)

        response['choices'] = sorted(
            best_choices, key=lambda k: k['score'], reverse=True
        )

        if len(response['choices']) == 1:
            response['head']['match'] = 'by_similarity'
        else:
            response['head']['match'] = 'multiple'

        return response

    def similar_countries(self, index, q):

        if not index in INDEXES_DOC_TYPE:
            raise TypeError('Invalid index name: %s' % index)

        data = {}

        if q:
            data['form'] = q

        qbody = {
            'query': {
                'fuzzy_like_this_field': {
                    'form': {
                        'like_text': q,
                        'fuzziness': 2,
                        'max_query_terms': 100
                    }
                }
            }
        }

        parsed_data = self._parse_data_countries(
            self.es.search(
                index=index,
                doc_type=INDEXES_DOC_TYPE[index],
                body=qbody
            ),
            q
        )

        return parsed_data

    def similar_institutions(self, index, q, country=None):

        if not index in INDEXES_DOC_TYPE:
            raise TypeError('Invalid index name: %s' % index)

        data = {}

        if q:
            data['form'] = q

        qbody = {
            "query": {
                "bool":{
                    "should": [
                        {
                            "fuzzy_like_this_field": {
                                "form": {
                                    "like_text": q,
                                    "fuzziness": 2,
                                    "max_query_terms": 100
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
        }

        if country:
            qbody['query']['bool']['minimum_should_match'] = 2
            qbody['query']['bool']['should'].append([
                {
                    "fuzzy_like_this_field": {
                        "country": {
                            "like_text": country,
                            "fuzziness": 2,
                            "max_query_terms": 100
                        }
                    }
                }
            ])

        parsed_data = self._parse_data_institutions(
            self.es.search(
                index=index,
                doc_type=INDEXES_DOC_TYPE[index],
                body=qbody
            ),
            q
        )

        return parsed_data
