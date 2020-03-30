import re
import json
from bson.objectid import ObjectId
from datetime import datetime

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
        self.mongo_comparation_operators = {
            ">": "$gt", ">=": "$gte", "=>": "$gte",
            "<": "$lt", "<=": "$lte", "=<": "$lte",
            "=": "$eq", "==": "$eq",
        }
        self.seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
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
        self.pipeline = []

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

    def __is_int(self, value):
        try:
            num = int(value)
        except ValueError:
            return False
        return True

    def __join_tables(self):
        self.pipeline = []

        if "hostgroup" in self.search_dict.keys() \
                or "hgroup" in self.search_dict.keys() \
                or "hg" in self.search_dict.keys():
            self.pipeline.append({
                '$lookup': {
                    'from': 'hostgroup',
                    'localField': '_id',
                    'foreignField': 'hosts',
                    'as': 'hostgroup',
                }
            })
            # self.pipeline.append({
            #     '$unwind': {
            #         'path': '$hostgroup',
            #         'preserveNullAndEmptyArrays': True
            #     }
            # })

        if "realm" in self.search_dict.keys():
            self.pipeline.append({
                '$lookup': {
                    'from': 'realm',
                    'localField': '_realm',
                    'foreignField': '_id',
                    'as': 'realm',
                }
            })
            # self.pipeline.append({
            #     '$unwind': {
            #         'path': '$realm',
            #         'preserveNullAndEmptyArrays': True
            #     }
            # })

        if self.search_type != 'host':
            self.pipeline.append({
                '$lookup': {
                    'from': 'service',
                    'localField': '_id',
                    'foreignField': 'host',
                    'as': 'services',
                }
            })
            self.pipeline.append({
                '$unwind': {
                    'path': '$services',
                    'preserveNullAndEmptyArrays': False
                }
            })

            if "servicegroup" in self.search_dict.keys() \
                    or "sgroup" in self.search_dict.keys() \
                    or "sg" in self.search_dict.keys():
                self.pipeline.append({
                    '$lookup': {
                        'from': 'servicegroup',
                        'localField': '_id',
                        'foreignField': 'services',
                        'as': 'servicegroup',
                    }
                })
                # self.pipeline.append({
                #     '$unwind': {
                #         'path': '$servicegroup',
                #         'preserveNullAndEmptyArrays': True
                #     }
                # })

        if "contact" in self.search_dict.keys() \
                or "ctag" in self.search_dict.keys():
            self.pipeline.append({
                '$lookup': {
                    'from': 'user',
                    'localField': '_id',
                    'foreignField': 'users',
                    'as': 'contacts',
                }
            })
            # self.pipeline.append({
            #     '$unwind': {
            #         'path': '$contacts',
            #         'preserveNullAndEmptyArrays': True
            #     }
            # })

        if "usergroup" in self.search_dict.keys() \
                or "ugroup" in self.search_dict.keys() \
                or "ug" in self.search_dict.keys():
            self.pipeline.append({
                '$lookup': {
                    'from': 'usergroup',
                    'localField': '_id',
                    'foreignField': 'usergroups',
                    'as': 'contactgroups',
                }
            })
            # self.pipeline.append({
            #     '$unwind': {
            #         'path': '$contactgroups',
            #         'preserveNullAndEmptyArrays': True
            #     }
            # })

        if self.search_type != 'host':
            if "contact" in self.search_dict.keys() \
                    or "ctag" in self.search_dict.keys():
                self.pipeline.append({
                    '$lookup': {
                        'from': 'user',
                        'localField': '_id',
                        'foreignField': 'services.users',
                        'as': 'services_contacts',
                    }
                })
                # self.pipeline.append({
                #     '$unwind': {
                #         'path': '$services_contacts',
                #         'preserveNullAndEmptyArrays': True
                #     }
                # })

            # Todo check if really needs in all cases
            if "usergroup" in self.search_dict.keys() \
                    or "ugroup" in self.search_dict.keys() \
                    or "ug" in self.search_dict.keys():
                self.pipeline.append({
                    '$lookup': {
                        'from': 'usergroup',
                        'localField': '_id',
                        'foreignField': 'services.usergroups',
                        'as': 'services_contactgroups',
                    }
                })
                # self.pipeline.append({
                #     '$unwind': {
                #         'path': '$services_contactgroups',
                #         'preserveNullAndEmptyArrays': True
                #     }
                # })

        if "tech" in self.search_dict.keys() \
                or "location" in self.search_dict.keys() \
                or "loc" in self.search_dict.keys() \
                or "vendor" in self.search_dict.keys() \
                or "model" in self.search_dict.keys() \
                or "city" in self.search_dict.keys() \
                or "isaccess" in self.search_dict.keys() \
                or ("strings" in self.search_dict.keys() and len(self.search_dict.get('strings', [])) > 0):
            self.pipeline.append({
                '$addFields': {
                    'customs': {
                        '$objectToArray': '$customs'
                    }
                }
            })
            if self.search_type != 'host':
                self.pipeline.append({
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
                get_token_function = "_MongoAggregation__get_token_{}".format(token)
                get_token = getattr(self, get_token_function, None)
                if get_token is not None:
                    response = get_token(value)
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

    # Get Token functions, all must be with the name formula __get_token_is_<search_token>

    def __get_token_is(self, value):
        value = value.upper()
        if self.search_type == 'host':
            token_is = {
                "UP": {"ls_state_id": 0},
                "PENDING": {"ls_state": "PENDING"},
                "ACK": {"ls_acknowledged": True},
                "DOWNTIME": {"ls_downtimed": True},
                "SOFT": {"ls_state_type": "SOFT"},
            }
        elif self.search_type == 'service':
            token_is = {
                "OK": {"services.ls_state_id": 0},
                "PENDING": {"services.ls_state": "PENDING"},
                "ACK": {"services.ls_acknowledged": True},
                "DOWNTIME": {"services.ls_downtimed": True},
                "SOFT": {"services.ls_state_type": "SOFT"},
            }
        else:
            token_is = {
                "UP": {"ls_state_id": 0},
                "OK": {"services.ls_state_id": 0},
                "PENDING": {"$or": [{"ls_state": "PENDING"}, {"services.ls_state": "PENDING"}]},
                "ACK": {"$or": [{"ls_acknowledged": True}, {"services.ls_acknowledged": True}]},
                "DOWNTIME": {"$or": [{"ls_downtimed": True}, {"services.ls_downtimed": True}]},
                "SOFT": {"$or": [{"ls_state_type": "SOFT"}, {"services.ls_state_type": "SOFT"}]},
            }

        if type(value) == str and value in token_is:
            response = token_is[value]
        elif self.__is_int(value):
            if self.search_type == 'host':
                response = {"ls_state": int(value)}
            elif self.search_type == 'service':
                response = {"services.ls_state": int(value)}
            else:
                response = {"$or": [{"ls_state": int(value)}, {"services.ls_state": int(value)}]}
        else:
            response = None

        # print('get_token_is ==> {}'.format(response))
        return response

    def __get_token_isnot(self, value):
        value = value.upper()
        if self.search_type == 'host':
            token_isnot = {
                "UP": {"ls_state_id": {"$ne": 0}},
                "PENDING": {"ls_state": {"$ne": "PENDING"}},
                "ACK": {"ls_acknowledged": False},
                "DOWNTIME": {"ls_downtimed": False},
                "SOFT": {"ls_state_type": {"$ne": "SOFT"}},
            }
        elif self.search_type == 'service':
            token_isnot = {
                "OK": {
                    "$and": [
                        {"services": {"$ne": None}},
                        {"services.ls_state_id": {"$ne": 0}}
                    ]
                },
                "PENDING": {
                    "$and": [
                        {"services": {"$ne": None}},
                        {"services.ls_state": {"$ne": "PENDING"}},
                    ]
                },
                "ACK": {
                    "$and": [
                        {"services": {"$ne": None}},
                        {"services.ls_acknowledged": False},
                    ]
                },
                "DOWNTIME": {
                    "$and": [
                        {"services": {"$ne": None}},
                        {"services.ls_downtimed": False},
                    ]
                },
                "SOFT": {
                    "$and": [
                        {"services": {"$ne": None}},
                        {"services.ls_state_type": {"$ne": "SOFT"}},
                    ]
                },
            }
        else:
            token_isnot = {
                "UP": {
                    "$or": [
                        {
                            "$and": [
                                {"services": {"$ne": None}},
                                {"services.ls_state_id": {"$ne": 0}}
                            ]
                        },
                        {"ls_state_id": {"$ne": 0}}
                    ]
                },
                "OK": {
                    "$or": [
                        {
                            "$and": [
                                {"services": {"$ne": None}},
                                {"services.ls_state_id": {"$ne": 0}}
                            ]
                        },
                        {"ls_state_id": {"$ne": 0}}
                    ]
                },
                "PENDING": {
                    "$or": [
                        {
                            "$and": [
                                {"services": {"$ne": None}},
                                {"services.ls_state": {"$ne": "PENDING"}},
                            ]
                        },
                        {"ls_state": {"$ne": "PENDING"}}
                    ]
                },
                "ACK": {  # Host.ls_acknowledged = false / Host.services.ls_acknowledged = true
                    "$or": [
                        {
                            "$and": [
                                {"services": {"$ne": None}},
                                {"services.ls_acknowledged": False},
                            ]
                        },
                        {"ls_acknowledged": False}
                    ]
                },
                "DOWNTIME": {
                    "$or": [
                        {
                            "$and": [
                                {"services": {"$ne": None}},
                                {"services.ls_downtimed": False},
                            ]
                        },
                        {"ls_downtimed": False}
                    ]
                },
                "SOFT": {
                    "$or": [
                        {
                            "$and": [
                                {"services": {"$ne": None}},
                                {"services.ls_state_type": {"$ne": "SOFT"}},
                            ]
                        },
                        {"ls_state_type": {"$ne": "SOFT"}}
                    ]
                },
            }

        if type(value) == str and value in token_isnot:
            response = token_isnot[value]
        elif self.__is_int(value):
            if self.search_type == 'host':
                response = {"ls_state_id": {"$ne": int(value)}}
            elif self.search_type == 'service':
                response = {"services.ls_state_id": {"$ne": int(value)}}
            else:
                response = {
                    "$or": [{"ls_state_id": {"$ne": int(value)}}, {"services.ls_state_id": {"$ne": int(value)}}]}
        else:
            response = None

        # print('get_token_isnot ==> {}'.format(response))
        return response

    def __get_token_bi(self, value):
        operator, value = re.match("([=><]{0,2})(\\d)", value).groups()

        if self.search_type == 'host':
            if operator == '' or operator == '=' or operator == '==':
                response = {"business_impact": int(value)}
            elif operator == '>':
                response = {"business_impact": {"$gt": int(value)}}
            elif operator == '>=' or operator == '=>':
                response = {"business_impact": {"$gte": int(value)}}
            elif operator == '<':
                response = {"business_impact": {"$lt": int(value)}}
            elif operator == '<=' or operator == '=<':
                response = {"business_impact": {"$lte": int(value)}}
            else:
                response = None
        elif self.search_type == 'service':
            if operator == '' or operator == '=' or operator == '==':
                response = {
                                "$or": [
                                    {"services": None},
                                    {"services.business_impact": int(value)},
                                ]
                            }
            elif operator == '>':
                response = {
                                "$or": [
                                    {"services": None},
                                    {"services.business_impact": {"$gt": int(value)}},
                                ]
                            }
            elif operator == '>=' or operator == '=>':
                response = {
                                "$or": [
                                    {"services": None},
                                    {"services.business_impact": {"$gte": int(value)}},
                                ]
                            }
            elif operator == '<':
                response = {
                                "$or": [
                                    {"services": None},
                                    {"services.business_impact": {"$lt": int(value)}},
                                ]
                            }
            elif operator == '<=' or operator == '=<':
                response = {
                    "$or": [
                        {"services": None},
                        {"services.business_impact": {"$lte": int(value)}},
                    ]
                }
            else:
                response = None
        else:
            if operator == '' or operator == '=' or operator == '==':
                response = {
                    "$or": [
                        {"business_impact": int(value)},
                        {
                            "$or": [
                                {"services": None},
                                {"services.business_impact": int(value)},
                            ]
                        }
                    ]
                }
            elif operator == '>':
                response = {
                    "$or": [
                        {"business_impact": {"$gt": int(value)}},
                        {
                            "$or": [
                                {"services": None},
                                {"services.business_impact": {"$gt": int(value)}},
                            ]
                        }
                    ]
                }
            elif operator == '>=' or operator == '=>':
                response = {
                    "$or": [
                        {"business_impact": {"$gte": int(value)}},
                        {
                            "$or": [
                                {"services": None},
                                {"services.business_impact": {"$gte": int(value)}},
                            ]
                        }
                    ]
                }
            elif operator == '<':
                response = {
                    "$or": [
                        {"business_impact": {"$lt": int(value)}},
                        {
                            "$or": [
                                {"services": None},
                                {"services.business_impact": {"$lt": int(value)}},
                            ]
                        }
                    ]
                }
            elif operator == '<=' or operator == '=<':
                response = {
                    "$or": [
                        {"business_impact": {"$lte": int(value)}},
                        {
                            "$or": [
                                {"services": None},
                                {"services.business_impact": {"$lte": int(value)}},
                            ]
                        }
                    ]
                }
            else:
                response = None

        # print('get_token_bi ==> {}'.format(response))
        return response

    def __get_token_bp(self, value):
        return self.__get_token_bi(value)

    def __get_token_name(self, value):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        if self.search_type == 'host':
            return {
                "$or": [
                    {"alias": regx},
                    {"display_name": regx},
                    {"name": regx},
                ]
            }
        elif self.search_type == 'service':
            return {
                "$or": [
                    {"services.name": regx},
                    {"services.alias": regx},
                ]
            }
        else:
            return {
                "$or": [
                    {"alias": regx},
                    {"display_name": regx},
                    {"name": regx},
                    {"services.name": regx},
                    {"services.alias": regx},
                ]
            }

    def __get_token_host(self, value):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"alias": regx},
                {"display_name": regx},
                {"name": regx},
            ]
        }

    def __get_token_h(self, value):
        return self.__get_token_host(value)

    def __get_token_service(self, value):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"services.name": regx},
                {"services.alias": regx},
            ]
        }

    def __get_token_s(self, value):
        return self.__get_token_service(value)

    def __get_token_contact(self, value):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"contacts.name": regx},
                {"contacts.alias": regx},
            ]
        }

    def __get_token_c(self, value):
        return self.__get_token_contact(value)

    def __get_token_hostgroup(self, value):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"hostgroup.name": regx},
                {"hostgroup.alias": regx},
            ]
        }

    def __get_token_hgroup(self, value):
        return self.__get_token_hostgroup(value)

    def __get_token_hg(self, value):
        return self.__get_token_hostgroup(value)

    def __get_token_servicegroup(self, value):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"servicegroup.name": regx},
                {"servicegroup.alias": regx},
            ]
        }

    def __get_token_sgroup(self, value):
        return self.__get_token_servicegroup(value)

    def __get_token_sg(self, value):
        return self.__get_token_servicegroup(value)

    def __get_token_contactgroup(self, value):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        if self.search_type == 'host':
            return {
                "$or": [
                    {"contactgroups.name": regx},
                    {"contactgroups.alias": regx},
                ]
            }
        elif self.search_type == 'service':
            return {
                "$or": [
                    {"services_contactgroups.name": regx},
                    {"services_contactgroups.alias": regx},
                ]
            }
        else:
            return {
                "$or": [
                    {"contactgroups.name": regx},
                    {"contactgroups.alias": regx},
                    {"services_contactgroups.name": regx},
                    {"services_contactgroups.alias": regx},
                ]
            }

    def __get_token_cgroup(self, value):
        return self.__get_token_contactgroup(value)

    def __get_token_cg(self, value):
        return self.__get_token_contactgroup(value)

    def __get_token_realm(self, value):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        if self.search_type == 'host':
            return {
                "$or": [
                    {"realm.name": regx},
                    {"realm.alias": regx},
                ]
            }
        elif self.search_type == 'service':
            return {
                "$or": [
                    {"services.realm.name": regx},
                    {"services.realm.alias": regx},
                ]
            }
        else:
            return {
                "$or": [
                    {"realm.name": regx},
                    {"realm.alias": regx},
                    {"services.realm.name": regx},
                    {"services.realm.alias": regx},
                ]
            }

    def __get_token_htag(self, value):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"tags": regx},
            ]
        }

    def __get_token_stag(self, value):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"services.tags": regx},
            ]
        }

    def __get_token_ctag(self, value):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        if self.search_type == 'host':
            return {
                "$or": [
                    {"contacts.tags": regx},
                ]
            }
        elif self.search_type == 'service':
            return {
                "$or": [
                    {"services_contacts.tags": regx},
                ]
            }
        else:
            return {
                "$or": [
                    {"contacts.tags": regx},
                    {"services_contacts.tags": regx},
                ]
            }

    def __get_token_duration(self, value):
        operator, value = re.match("([=><]{0,2})(\\d)", value).groups()
        if value == "":
            return None
        duration = time.time() - (int(value[0:-1]) * self.seconds_per_unit[value[-1]])
        if self.search_type == 'host':
            return {
                "$or": [
                    {"ls_last_state_changed": {self.mongo_comparation_operators[operator]: duration}},
                ]
            }
        elif self.search_type == 'service':
            return {
                "$or": [
                    {"services.ls_last_state_changed": {self.mongo_comparation_operators[operator]: duration}},
                ]
            }
        else:
            return {
                "$or": [
                    {"ls_last_state_changed": {self.mongo_comparation_operators[operator]: duration}},
                    {"services.ls_last_state_changed": {self.mongo_comparation_operators[operator]: duration}},
                ]
            }

    def __get_token_tech(self, value):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_TECH'},
                {"customs.v": regx},
            ]
        }

    def __get_token_perf(self, value):
        perf, operator, value = re.match("([\\w_]+)([=><]{0,2})(\\d)", value).groups()
        if value == "":
            return None
        if self.search_type == 'host':
            return {
                "$or": [
                    {"ls_perf_data": {self.mongo_comparation_operators[operator]: value}},
                ]
            }
        elif self.search_type == 'service':
            return {
                "$or": [
                    {"services.ls_perf_data": {self.mongo_comparation_operators[operator]: value}},
                ]
            }
        else:
            return {
                "$or": [
                    {"ls_perf_data": {self.mongo_comparation_operators[operator]: value}},
                    {"services.ls_perf_data": {self.mongo_comparation_operators[operator]: value}},
                ]
            }

    def __get_token_reg(self, value):
        # if i.__class__.my_type == 'service':
        #     l2 = i.host.cpe_registration_tags.split(',')
        # elif i.__class__.my_type == 'host':
        #     l2 = i.cpe_registration_tags.split(',')
        # else:
        #     l2 = []
        return None

    def __get_token_regstate(self, value):
        # if i.__class__.my_type == 'service':
        #     l2 = i.host.cpe_registration_state
        # elif i.__class__.my_type == 'host':
        #     l2 = i.cpe_registration_state
        # else:
        #     l2 = ''
        return None

    def __get_token_location(self, value):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_LOCATION'},
                {"customs.v": regx},
            ]
        }

    def __get_token_loc(self, value):
        return self.__get_token_location(value)

    def __get_token_vendor(self, value):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_VENDOR'},
                {"customs.v": regx},
            ]
        }

    def __get_token_model(self, value):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {
                    "$or": [
                        {"customs.k": '_MODEL'},
                        {"customs.k": '_CPE_MODEL'},
                    ]
                },
                {"customs.v": regx},
            ]
        }

    def __get_token_city(self, value):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_CUSTOMER_CITY'},
                {"customs.v": regx},
            ]
        }

    def __get_token_isaccess(self, value):
        if value in ('yes', '1'):
            value = '1'
        elif value in ('no', '0'):
            value = '0'
        else:
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_ACCESS'},
                {"customs.v": regx},
            ]
        }

    def __get_token_his(self, value):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"ls_state_id": int(value)},
                {"ls_state": value.upper()},
            ]
        }

    def __get_token_ack(self, value):
        if value in ("false", "no"):
            return get_token_isnot("ack")
        elif value in ("true", "yes"):
            return get_token_is("ack")
        else:
            return get_token_is("ack")

    def __get_token_downtime(self, value):
        if value in ("false", "no"):
            return get_token_isnot("downtime")
        elif value in ("true", "yes"):
            return get_token_is("downtime")
        else:
            return get_token_is("downtime")

    def __get_token_critical(self, value):
        if value in ("false", "no"):
            return get_token_isnot("critical")
        elif value in ("true", "yes"):
            return get_token_is("critical")
        else:
            return get_token_is("critical")

    def __get_token_crit(self, value):
        return self.__get_token_critical(value)

    def __get_token_cri(self, value):
        return self.__get_token_critical(value)

    def __get_token_strings(self, value):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        if self.search_type == 'host':
            return {
                "$or": [
                    {"address": regx},
                    {"alias": regx},
                    {"customs.v": regx},
                    {"display_name": regx},
                    # {"hostgroup.name": regx},
                    {"ls_output": regx},
                    {"ls_state": regx},
                    {"name": regx},
                    {"notes": regx},
                    # {"realm.name": regx},
                ]
            }
        elif self.search_type == 'service':
            return {
                "$or": [
                    {"services.name": regx},
                    {"services.alias": regx},
                    {"services_customs.v": regx},
                ]
            }
        else:
            return {
                "$or": [
                    {"address": regx},
                    {"alias": regx},
                    {"customs.v": regx},
                    {"display_name": regx},
                    # {"hostgroup.name": regx},
                    {"ls_output": regx},
                    {"ls_state": regx},
                    {"name": regx},
                    {"notes": regx},
                    # {"realm.name": regx},
                    {"services.name": regx},
                    {"services.alias": regx},
                    {"services_customs.v": regx},
                ]
            }
