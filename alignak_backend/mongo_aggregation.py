import re
import json
from bson.objectid import ObjectId
from datetime import datetime
from alignak_backend.mongo_aggregation_tokens import MongoAggregationTokens

# To Test it:
# from alignak_backend.mongo_aggregation import MongoAggregation
# from bson import json_util
# import json
# a = MongoAggregation()

# To get search tokens
# a.get_tokens("")
# a.get_tokens("isnot:UP isnot:OK isnot:PENDING isnot:ACK isnot:DOWNTIME isnot:SOFT")
# a.get_tokens("isnot:UP isnot:OK isnot:PENDING isnot:ACK isnot:DOWNTIME isnot:SOFT bi:>=2")

# To get aggregation
# json.dumps(a.get_aggregation(""), default=json_util.default)
# json.dumps(a.get_aggregation("isnot:UP isnot:OK isnot:PENDING isnot:ACK isnot:DOWNTIME isnot:SOFT"), default=json_util.default)
# json.dumps(a.get_aggregation("isnot:UP isnot:OK isnot:PENDING isnot:ACK isnot:DOWNTIME isnot:SOFT bi:>=2"), default=json_util.default)

# To get results count
# json.dumps(a.get_results(""), default=json_util.default)
# json.dumps(a.get_results("isnot:UP isnot:OK isnot:PENDING isnot:ACK isnot:DOWNTIME isnot:SOFT"), default=json_util.default)
# json.dumps(a.get_results("isnot:UP isnot:OK isnot:PENDING isnot:ACK isnot:DOWNTIME isnot:SOFT bi:>=2"), default=json_util.default)

# To query in mongo:
# mongo alignak-backend
# db.host.aggregate(<dump_result_without_quotes>, {allowDiskUse: true})


class MongoAggregation:

    def __init__(self, sort=None, pagination=None):
        self.unique_keys = ['type']
        self.search_dict = {
            'type': 'all'
        }
        self.valid_search_types = ['all', 'host', 'service']
        self.search_type = 'all'
        self.order = 1
        self.field = '_id'
        if sort is not None:
            self.order, self.field = re.match("([-]?)(\\w+)", sort).groups()
        self.pagination = {
            'offset': 0,
            'limit': 10
        }
        if pagination is not None:
            self.pagination = {
                'offset': int(pagination['offset']) or 0,
                'limit': int(pagination['limit']) or 10
            }
        self.pipeline = {
            hosts: [],
            services: []
        }

    def get_default_response(self):
        return {
            'count': 0,
            'results': [],
            'pagination': {
                'offset': int(self.pagination['offset']),
                'limit': int(self.pagination['limit'])
            },
            'sort': {
                'field': self.field,
                'order': 'DESC' if self.order == '-' else 'ASC'
            },
        }

    def get_tokens(self, search=""):
        search_tokens = search.lower().split(' ')
        for token in search_tokens:
            if ':' in token:
                key, value = tuple(token.split(':'))
                if key not in self.search_dict:
                    self.search_dict[key] = []

                if key in self.unique_keys:  # This keys can't be append, there must be only one value for them
                    self.search_dict[key] = value
                else:
                    self.search_dict[key].append(value)
            else:
                if 'strings' not in self.search_dict:
                    self.search_dict['strings'] = []
                if token != '':
                    self.search_dict['strings'].append(token)
        return self.search_dict

    def get_aggregation(self, search="", realm=None, sort=None, pagination=None):
        self.get_tokens(search)
        self.__get_search_type()
        self.__join_tables()
        self.__get_pipeline(realm)
        self.__sort_and_paginate(sort, pagination)

        return self.pipeline

    def get_results(self, search="", realm=None):
        self.get_tokens(search)
        self.__get_search_type()
        self.__join_tables()
        self.__get_pipeline(realm)
        self.pipeline.append({
            "$count": "results"
        })

        return self.pipeline

    def __join_tables(self):
        pipeline = []

        if "hostgroup" in self.search_dict.keys() \
                or "hgroup" in self.search_dict.keys() \
                or "hg" in self.search_dict.keys():
            pipeline.append({
                '$lookup': {
                    'from': 'hostgroup',
                    'localField': '_id',
                    'foreignField': 'hosts',
                    'as': 'hostgroup',
                }
            })
            pipeline.append({
                '$unwind': {
                    'path': '$hostgroup',
                    'preserveNullAndEmptyArrays': True
                }
            })

        if "realm" in self.search_dict.keys():
            pipeline.append({
                '$lookup': {
                    'from': 'realm',
                    'localField': '_realm',
                    'foreignField': '_id',
                    'as': 'realm',
                }
            })
            pipeline.append({
                '$unwind': {
                    'path': '$realm',
                    'preserveNullAndEmptyArrays': True
                }
            })

        if self.search_type != 'host':
            pipeline.append({
                '$lookup': {
                    'from': 'service',
                    'localField': '_id',
                    'foreignField': 'host',
                    'as': 'services',
                }
            })
            pipeline.append({
                '$unwind': {
                    'path': '$services',
                    'preserveNullAndEmptyArrays': False
                }
            })

            if "servicegroup" in self.search_dict.keys() \
                    or "sgroup" in self.search_dict.keys() \
                    or "sg" in self.search_dict.keys():
                pipeline.append({
                    '$lookup': {
                        'from': 'servicegroup',
                        'localField': '_id',
                        'foreignField': 'services',
                        'as': 'servicegroup',
                    }
                })
                pipeline.append({
                    '$unwind': {
                        'path': '$servicegroup',
                        'preserveNullAndEmptyArrays': True
                    }
                })

        # if "contact" in self.search_dict.keys() \
        #         or "ctag" in self.search_dict.keys():
        #     pipeline.append({
        #         '$lookup': {
        #             'from': 'user',
        #             'localField': '_id',
        #             'foreignField': 'users',
        #             'as': 'contacts',
        #         }
        #     })
        #     pipeline.append({
        #         '$unwind': {
        #             'path': '$contacts',
        #             'preserveNullAndEmptyArrays': True
        #         }
        #     })

        if "usergroup" in self.search_dict.keys() \
                or "ugroup" in self.search_dict.keys() \
                or "ug" in self.search_dict.keys():
            pipeline.append({
                '$lookup': {
                    'from': 'usergroup',
                    'localField': '_id',
                    'foreignField': 'usergroups',
                    'as': 'contactgroups',
                }
            })
            pipeline.append({
                '$unwind': {
                    'path': '$contactgroups',
                    'preserveNullAndEmptyArrays': True
                }
            })

        # if self.search_type != 'host':
        #     if "contact" in self.search_dict.keys() \
        #             or "ctag" in self.search_dict.keys():
        #         pipeline.append({
        #             '$lookup': {
        #                 'from': 'user',
        #                 'localField': '_id',
        #                 'foreignField': 'services.users',
        #                 'as': 'services_contacts',
        #             }
        #         })
        #         pipeline.append({
        #             '$unwind': {
        #                 'path': '$services_contacts',
        #                 'preserveNullAndEmptyArrays': True
        #             }
        #         })

            # Todo check if really needs in all cases
            if "usergroup" in self.search_dict.keys() \
                    or "ugroup" in self.search_dict.keys() \
                    or "ug" in self.search_dict.keys():
                pipeline.append({
                    '$lookup': {
                        'from': 'usergroup',
                        'localField': '_id',
                        'foreignField': 'services.usergroups',
                        'as': 'services_contactgroups',
                    }
                })
                pipeline.append({
                    '$unwind': {
                        'path': '$services_contactgroups',
                        'preserveNullAndEmptyArrays': True
                    }
                })

        if "tech" in self.search_dict.keys() \
                or "location" in self.search_dict.keys() \
                or "loc" in self.search_dict.keys() \
                or "vendor" in self.search_dict.keys() \
                or "model" in self.search_dict.keys() \
                or "city" in self.search_dict.keys() \
                or "isaccess" in self.search_dict.keys() \
                or ("strings" in self.search_dict.keys() and len(self.search_dict.get('strings', [])) > 0):
            pipeline.append({
                '$addFields': {
                    'customs': {
                        '$objectToArray': '$customs'
                    }
                }
            })
            if self.search_type != 'host':
                pipeline.append({
                    '$addFields': {
                        'services_customs': {
                            '$objectToArray': '$services.customs'
                        }
                    }
                })

    def __get_search_type(self):
        search_type = self.search_dict.get('type', 'all')
        if search_type in self.valid_search_types:
            self.search_type = search_type
        self.search_dict.pop('type', None)

    def __get_pipeline(self, realm):
        # First filter by user realm if defined, and remove templates and dummys
        if realm is not None:
            self.pipeline.append({"$match": {
                "_realm": ObjectId(realm),
                "name": {"$ne": "_dummy"},
                "_is_template": False
            }})
        else:
            self.pipeline.append({"$match": {
                "name": {"$ne": "_dummy"},
                "_is_template": False
            }})

        # Second for every token in search_dict append specific search
        for token in self.search_dict:
            for value in self.search_dict[token]:
                # get_token_function = "_MongoAggregation__get_token_{}".format(token)
                # get_token = getattr(self, get_token_function, None)
                get_token_function = "get_token_{}".format(token)
                get_token = getattr(MongoAggregationTokens, get_token_function, None)
                if get_token is not None:
                    response = get_token(value, self.search_type)
                    if response is not None:
                        self.pipeline.append({"$match": response})
                # todo add possible bad tokens and notify

        return self.pipeline

    def __sort_and_paginate(self, sort=None, pagination=None):
        if sort is not None and sort.field not in [
            "business_impact",
            "services.business_impact",
            "ls_state_id",
            "services.ls_state_id"
        ]:
            self.order, self.field = re.match("([-]?)(\\w+)", sort).groups()

        if self.search_type == 'host':
            self.pipeline.append({
                '$sort': {
                    self.field: -1 if self.order == '-' else 1,
                    'business_impact': -1,
                    'ls_state_id': -1,
                }
            })
        elif self.search_type == 'service':
            self.pipeline.append({
                '$sort': {
                    self.field: -1 if self.order == '-' else 1,
                    'services.business_impact': -1,
                    'services.ls_state_id': -1,
                }
            })
        else:
            self.pipeline.append({
                '$sort': {
                    self.field: -1 if self.order == '-' else 1,
                    'business_impact': -1,
                    'services.business_impact': -1,
                    'ls_state_id': -1,
                    'services.ls_state_id': -1,
                }
            })

        if pagination is not None:
            self.pagination = {
                'offset': int(pagination['offset']) or 0,
                'limit': int(pagination['limit']) or 10
            }

        self.pipeline.append({
            '$skip': self.pagination['offset']
        })
        self.pipeline.append({
            '$limit': self.pagination['limit']
        })

        self.pipeline.append({
            "$project": {
                "name": 1,
                "ls_acknowledged": 1,
                "active_checks_enabled": 1,
                "downtimed": 1,
                "event_handler_enabled": 1,
                "business_impact": 1,
                "ls_state_id": 1,
                "ls_state": 1,
                "ls_last_check": 1,
                "ls_next_check": 1,
                "ls_output": 1,
                "services._id": 1 if self.search_type != 'host' else 0,
                "services.name": 1 if self.search_type != 'host' else 0,
                "services.business_impact": 1 if self.search_type != 'host' else 0,
                "services.ls_acknowledged": 1 if self.search_type != 'host' else 0,
                "services.active_checks_enabled": 1 if self.search_type != 'host' else 0,
                "services.downtimed": 1 if self.search_type != 'host' else 0,
                "services.event_handler_enabled": 1 if self.search_type != 'host' else 0,
                "services.ls_state_id": 1 if self.search_type != 'host' else 0,
                "services.ls_state": 1 if self.search_type != 'host' else 0,
                "services.ls_last_check": 1 if self.search_type != 'host' else 0,
                "services.ls_next_check": 1 if self.search_type != 'host' else 0,
                "services.ls_output": 1 if self.search_type != 'host' else 0,
            }
        })


        # Todo to fix
        # if pagination is not None:
        #     self.pagination = {
        #         'offset': int(pagination['offset']) or 0,
        #         'limit': int(pagination['limit']) or 10
        #     }
        #
        # self.pipeline.append({
        #     '$group': {
        #         '_id': None,
        #         'count': {'$sum': 1},
        #         'results': {'$push': '$$ROOT'}
        #     }
        # })
        # self.pipeline.append({
        #     '$project': {
        #         '_id': 0,
        #         'count': 1,
        #         'results': {'$slice': ['$results', self.pagination['offset'], self.pagination['limit']]}
        #     }
        # })
        # self.pipeline.append({
        #     '$addFields': {
        #         'pagination': {
        #             'offset':  self.pagination['offset'],
        #             'limit': self.pagination['limit'],
        #             # 'prev': None if offset <= 0 or offset - limit < 0 else offset - limit,
        #             # 'next': offset + limit if offset <=
        #         },
        #         'sort': {
        #             'field': self.field,
        #             'order': 'DESC' if self.order == '-' else 'ASC'
        #         },
        #     }
        # })


