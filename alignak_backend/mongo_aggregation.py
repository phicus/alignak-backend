import re
import json
from bson.objectid import ObjectId
from datetime import datetime


class MongoAggregation:

    def __init__(self, sort=None, pagination=None):
        self.unique_keys = ['type']
        self.search_dict = {
            'type': 'all'
        }
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
        self.__join_tables()
        self.__get_pipeline(realm)
        self.__sort_and_paginate(sort, pagination)

        return self.pipeline

    def __is_int(value):
        try:
            num = int(value)
        except ValueError:
            return False
        return True

    def __join_tables(self):
        self.pipeline = []
        self.pipeline.append({
            '$lookup': {
                'from': 'hostgroup',
                'localField': '_id',
                'foreignField': 'hosts',
                'as': 'hostgroup'
            }
        })
        self.pipeline.append({
            '$unwind': {
                'path': '$hostgroup',
                'preserveNullAndEmptyArrays': True
            }
        })
        self.pipeline.append({
            '$lookup': {
                'from': 'realm',
                'localField': '_realm',
                'foreignField': '_id',
                'as': 'realm'
            }
        })
        self.pipeline.append({
            '$unwind': {
                'path': '$realm',
                'preserveNullAndEmptyArrays': True
            }
        })
        self.pipeline.append({
            '$lookup': {
                'from': 'service',
                'localField': '_id',
                'foreignField': 'host',
                'as': 'services'
            }
        })
        self.pipeline.append({
            '$unwind': {
                'path': '$services',
                'preserveNullAndEmptyArrays': True
            }
        })
        # Todo check if return correct values
        self.pipeline.append({
            '$lookup': {
                'from': 'servicegroup',
                'localField': '_id',
                'foreignField': 'services',
                'as': 'servicegroup'
            }
        })
        self.pipeline.append({
            '$unwind': {
                'path': '$servicegroup',
                'preserveNullAndEmptyArrays': True
            }
        })
        # Todo check if really needs in all cases
        self.pipeline.append({
            '$lookup': {
                'from': 'user',
                'localField': '_id',
                'foreignField': 'users',
                'as': 'contacts'
            }
        })
        self.pipeline.append({
            '$unwind': {
                'path': '$contacts',
                'preserveNullAndEmptyArrays': True
            }
        })
        # Todo check if really needs in all cases
        self.pipeline.append({
            '$lookup': {
                'from': 'usergroup',
                'localField': '_id',
                'foreignField': 'usergroups',
                'as': 'contactgroups'
            }
        })
        self.pipeline.append({
            '$unwind': {
                'path': '$contactgroups',
                'preserveNullAndEmptyArrays': True
            }
        })
        # Todo check if really needs in all cases
        self.pipeline.append({
            '$lookup': {
                'from': 'user',
                'localField': '_id',
                'foreignField': 'services.users',
                'as': 'services_contacts'
            }
        })
        self.pipeline.append({
            '$unwind': {
                'path': '$services_contacts',
                'preserveNullAndEmptyArrays': True
            }
        })
        # Todo check if really needs in all cases
        self.pipeline.append({
            '$lookup': {
                'from': 'usergroup',
                'localField': '_id',
                'foreignField': 'services.usergroups',
                'as': 'services_contactgroups'
            }
        })
        self.pipeline.append({
            '$unwind': {
                'path': '$services_contactgroups',
                'preserveNullAndEmptyArrays': True
            }
        })
        self.pipeline.append({
            '$addFields': {
                'customs': {
                    '$objectToArray': '$customs'
                }
            }
        })
        self.pipeline.append({
            '$addFields': {
                'services_customs': {
                    '$objectToArray': '$services.customs'
                }
            }
        })

    def __get_pipeline(self, realm):
        # Second filter by user realm if defined, and remove templates and dummys
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

        # Thirt define scope of search: all, host or service and remove it from search_dict
        search_type = self.search_dict.get('type', 'all')
        self.search_dict.pop('type', None)

        # Fourth for every token in search_dict append specific search
        for token in self.search_dict:
            for value in self.search_dict[token]:
                get_token_function = "_MongoAggregation__get_token_{}".format(token)
                get_token = getattr(self, get_token_function, None)
                if get_token is not None:
                    response = get_token(value, search_type)
                    if response is not None:
                        self.pipeline.append({"$match": response})

        return self.pipeline

    def __sort_and_paginate(self, sort=None, pagination=None):
        if sort is not None:
            self.order, self.field = re.match("([-]?)(\\w+)", sort).groups()

        self.pipeline.append({
            '$sort': {
                self.field: -1 if self.order == '-' else 1,
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
            '$group': {
                '_id': None,
                'count': {'$sum': 1},
                'results': {'$push': '$$ROOT'}
            }
        })
        self.pipeline.append({
            '$project': {
                '_id': 0,
                'count': 1,
                'results': {'$slice': ['$results', self.pagination['offset'], self.pagination['limit']]}
            }
        })
        self.pipeline.append({
            '$addFields': {
                'pagination': {
                    'offset':  self.pagination['offset'],
                    'limit': self.pagination['limit'],
                    # 'prev': None if offset <= 0 or offset - limit < 0 else offset - limit,
                    # 'next': offset + limit if offset <=
                },
                'sort': {
                    'field': self.field,
                    'order': 'DESC' if self.order == '-' else 'ASC'
                },
            }
        })

    def __get_token_is(self, value, search_type):
        value = value.upper()
        if search_type == 'host':
            token_is = {
                "UP": {"ls_state_id": 0},
                "PENDING": {"ls_state": "PENDING"},
                "ACK": {"ls_acknowledged": True},
                "DOWNTIME": {"ls_downtimed": True},
                "SOFT": {"ls_state_type": "SOFT"},
            }
        elif search_type == 'service':
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
            if search_type == 'host':
                response = {"ls_state": int(value)}
            elif search_type == 'service':
                response = {"services.ls_state": int(value)}
            else:
                response = {"$or": [{"ls_state": int(value)}, {"services.ls_state": int(value)}]}
        else:
            response = None

        # print('get_token_is ==> {}'.format(response))
        return response

    def __get_token_isnot(self, value, search_type):
        value = value.upper()
        if search_type == 'host':
            token_isnot = {
                "UP": {"ls_state_id": {"$ne": 0}},
                "PENDING": {"ls_state": {"$ne": "PENDING"}},
                "ACK": {"ls_acknowledged": False},
                "DOWNTIME": {"ls_downtimed": False},
                "SOFT": {"ls_state_type": {"$ne": "SOFT"}},
            }
        elif search_type == 'service':
            token_isnot = {
                "OK": {
                    "$or": [
                        {"services": None},
                        {"services.ls_state_id": {"$ne": 0}}
                    ]
                },
                "PENDING": {
                    "$or": [
                        {"services": None},
                        {"services.ls_state": {"$ne": "PENDING"}},
                    ]
                },
                "ACK": {
                    "$or": [
                        {"services": None},
                        {"services.ls_acknowledged": False},
                    ]
                },
                "DOWNTIME": {
                    "$or": [
                        {"services": None},
                        {"services.ls_downtimed": False},
                    ]
                },
                "SOFT": {
                    "$or": [
                        {"services": None},
                        {"services.ls_state_type": {"$ne": "SOFT"}},
                    ]
                },
            }
        else:
            token_isnot = {
                "UP": {
                    "$and": [
                        {
                            "$or": [
                                {"services": None},
                                {"services.ls_state_id": {"$ne": 0}}
                            ]
                        },
                        {"ls_state_id": {"$ne": 0}}
                    ]
                },
                "OK": {
                    "$and": [
                        {
                            "$or": [
                                {"services": None},
                                {"services.ls_state_id": {"$ne": 0}}
                            ]
                        },
                        {"ls_state_id": {"$ne": 0}}
                    ]
                },
                "PENDING": {
                    "$and": [
                        {
                            "$or": [
                                {"services": None},
                                {"services.ls_state": {"$ne": "PENDING"}},
                            ]
                        },
                        {"ls_state": {"$ne": "PENDING"}}
                    ]
                },
                "ACK": {  # Host.ls_acknowledged = false / Host.services.ls_acknowledged = true
                    "$and": [
                        {
                            "$or": [
                                {"services": None},
                                {"services.ls_acknowledged": False},
                            ]
                        },
                        {"ls_acknowledged": False}
                    ]
                },
                "DOWNTIME": {
                    "$and": [
                        {
                            "$or": [
                                {"services": None},
                                {"services.ls_downtimed": False},
                            ]
                        },
                        {"ls_downtimed": False}
                    ]
                },
                "SOFT": {
                    "$or": [
                        {
                            "$or": [
                                {"services": None},
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
            if search_type == 'host':
                response = {"ls_state_id": {"$ne": int(value)}}
            elif search_type == 'service':
                response = {"services.ls_state_id": {"$ne": int(value)}}
            else:
                response = {
                    "$or": [{"ls_state_id": {"$ne": int(value)}}, {"services.ls_state_id": {"$ne": int(value)}}]}
        else:
            response = None

        # print('get_token_isnot ==> {}'.format(response))
        return response

    def __get_token_bi(self, value, search_type):
        operator, value = re.match("([=><]{0,2})(\\d)", value).groups()

        if search_type == 'host':
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
        elif search_type == 'service':
            if operator == '' or operator == '=' or operator == '==':
                response = {"services.business_impact": int(value)}
            elif operator == '>':
                response = {"services.business_impact": {"$gt": int(value)}}
            elif operator == '>=' or operator == '=>':
                response = {"services.business_impact": {"$gte": int(value)}}
            elif operator == '<':
                response = {"services.business_impact": {"$lt": int(value)}}
            elif operator == '<=' or operator == '=<':
                response = {"services.business_impact": {"$lte": int(value)}}
            else:
                response = None
        else:
            if operator == '' or operator == '=' or operator == '==':
                response = {"$or": [{"business_impact": int(value)}, {"services.business_impact": int(value)}]}
            elif operator == '>':
                response = {"$or": [{"business_impact": {"$gt": int(value)}},
                                    {"services.business_impact": {"$gt": int(value)}}]}
            elif operator == '>=' or operator == '=>':
                response = {"$or": [{"business_impact": {"$gte": int(value)}},
                                    {"services.business_impact": {"$gte": int(value)}}]}
            elif operator == '<':
                response = {"$or": [{"business_impact": {"$lt": int(value)}},
                                    {"services.business_impact": {"$lt": int(value)}}]}
            elif operator == '<=' or operator == '=<':
                response = {"$or": [{"business_impact": {"$lte": int(value)}},
                                    {"services.business_impact": {"$lte": int(value)}}]}
            else:
                response = None

        # print('get_token_bi ==> {}'.format(response))
        return response

    def __get_token_bp(self, value, search_type):
        return self.__get_token_bi(value, search_type)

    def __get_token_name(self, value, search_type):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        if search_type == 'host':
            return {
                "$or": [
                    {"alias": regx},
                    {"display_name": regx},
                    {"name": regx},
                ]
            }
        elif search_type == 'service':
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

    def __get_token_host(self, value, search_type):
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

    def __get_token_h(self, value, search_type):
        return self.__get_token_host(vaue, search_type)

    def __get_token_service(self, value, search_type):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"services.name": regx},
                {"services.alias": regx},
            ]
        }

    def __get_token_s(self, value, search_type):
        return self.__get_token_service(value, search_type)

    def __get_token_contact(self, value, search_type):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"contacts.name": regx},
                {"contacts.alias": regx},
            ]
        }

    def __get_token_c(self, value, search_type):
        return self.__get_token_contact(value, search_type)

    def __get_token_hostgroup(self, value, search_type):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"hostgroup.name": regx},
                {"hostgroup.alias": regx},
            ]
        }

    def __get_token_hgroup(self, value, search_type):
        return self.__get_token_hostgroup(value, search_type)

    def __get_token_hg(self, value, search_type):
        return self.__get_token_hostgroup(value, search_type)

    def __get_token_servicegroup(self, value, search_type):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"servicegroup.name": regx},
                {"servicegroup.alias": regx},
            ]
        }

    def __get_token_sgroup(self, value, search_type):
        return self.__get_token_servicegroup(value, search_type)

    def __get_token_sg(self, value, search_type):
        return self.__get_token_servicegroup(value, search_type)

    def __get_token_contactgroup(self, value, search_type):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        if search_type == 'host':
            return {
                "$or": [
                    {"contactgroups.name": regx},
                    {"contactgroups.alias": regx},
                ]
            }
        elif search_type == 'service':
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

    def __get_token_cgroup(self, value, search_type):
        return self.__get_token_contactgroup(value, search_type)

    def __get_token_cg(self, value, search_type):
        return self.__get_token_contactgroup(value, search_type)

    def __get_token_realm(self, value, search_type):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        if search_type == 'host':
            return {
                "$or": [
                    {"realm.name": regx},
                    {"realm.alias": regx},
                ]
            }
        elif search_type == 'service':
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

    def __get_token_htag(self, value, search_type):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"tags": regx},
            ]
        }

    def __get_token_stag(self, value, search_type):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"services.tags": regx},
            ]
        }

    def __get_token_ctag(self, value, search_type):
        if value == "" or value == "all":
            return None
        regx = re.compile(value, re.IGNORECASE)
        if search_type == 'host':
            return {
                "$or": [
                    {"contacts.tags": regx},
                ]
            }
        elif search_type == 'service':
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

    def __get_token_duration(self, value, search_type):
        seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        mongo_comparation_operators = {
            ">": "$gt", ">=": "$gte", "=>": "$gte",
            "<": "$lt", "<=": "$lte", "=<": "$lte",
            "=": "$eq", "==": "$eq",
        }
        operator, value = re.match("([=><]{0,2})(\\d)", value).groups()
        if value == "":
            return None

        duration = time.time() - (int(value[0:-1]) * seconds_per_unit[value[-1]])
        if search_type == 'host':
            return {
                "$or": [
                    {"ls_last_state_changed": {mongo_comparation_operators[operator]: duration}},
                ]
            }
        elif search_type == 'service':
            return {
                "$or": [
                    {"services.ls_last_state_changed": {mongo_comparation_operators[operator]: duration}},
                ]
            }
        else:
            return {
                "$or": [
                    {"ls_last_state_changed": {mongo_comparation_operators[operator]: duration}},
                    {"services.ls_last_state_changed": {mongo_comparation_operators[operator]: duration}},
                ]
            }

    def __get_token_tech(self, value, search_type):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_TECH'},
                {"customs.v": regx},
            ]
        }

    def __get_token_perf(self, value, search_type):
        mongo_comparation_operators = {
            ">": "$gt", ">=": "$gte", "=>": "$gte",
            "<": "$lt", "<=": "$lte", "=<": "$lte",
            "=": "$eq", "==": "$eq",
        }
        perf, operator, value = re.match("([\\w_]+)([=><]{0,2})(\\d)", value).groups()
        if value == "":
            return None
        if search_type == 'host':
            return {
                "$or": [
                    {"ls_perf_data": {mongo_comparation_operators[operator]: value}},
                ]
            }
        elif search_type == 'service':
            return {
                "$or": [
                    {"services.ls_perf_data": {mongo_comparation_operators[operator]: value}},
                ]
            }
        else:
            return {
                "$or": [
                    {"ls_perf_data": {mongo_comparation_operators[operator]: value}},
                    {"services.ls_perf_data": {mongo_comparation_operators[operator]: value}},
                ]
            }

    def __get_token_reg(self, value, search_type):
        # if i.__class__.my_type == 'service':
        #     l2 = i.host.cpe_registration_tags.split(',')
        # elif i.__class__.my_type == 'host':
        #     l2 = i.cpe_registration_tags.split(',')
        # else:
        #     l2 = []
        return None

    def __get_token_regstate(self, value, search_type):
        # if i.__class__.my_type == 'service':
        #     l2 = i.host.cpe_registration_state
        # elif i.__class__.my_type == 'host':
        #     l2 = i.cpe_registration_state
        # else:
        #     l2 = ''
        return None

    def __get_token_location(self, value, search_type):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_LOCATION'},
                {"customs.v": regx},
            ]
        }

    def __get_token_loc(self, value, search_type):
        return self.__get_token_location(value, search_type)

    def __get_token_vendor(self, value, search_type):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_VENDOR'},
                {"customs.v": regx},
            ]
        }

    def __get_token_model(self, value, search_type):
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

    def __get_token_city(self, value, search_type):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_CUSTOMER_CITY'},
                {"customs.v": regx},
            ]
        }

    def __get_token_isaccess(self, value, search_type):
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

    def __get_token_his(self, value, search_type):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"ls_state_id": int(value)},
                {"ls_state": value.upper()},
            ]
        }

    def __get_token_ack(self, value, search_type):
        if value in ("false", "no"):
            return get_token_isnot("ack", search_type)
        elif value in ("true", "yes"):
            return get_token_is("ack", search_type)
        else:
            return get_token_is("ack", search_type)

    def __get_token_downtime(self, value, search_type):
        if value in ("false", "no"):
            return get_token_isnot("downtime", search_type)
        elif value in ("true", "yes"):
            return get_token_is("downtime", search_type)
        else:
            return get_token_is("downtime", search_type)

    def __get_token_critical(self, value, search_type):
        if value in ("false", "no"):
            return get_token_isnot("critical", search_type)
        elif value in ("true", "yes"):
            return get_token_is("critical", search_type)
        else:
            return get_token_is("critical", search_type)

    def __get_token_crit(self, value, search_type):
        return self.__get_token_critical(value, search_type)

    def __get_token_cri(self, value, search_type):
        return self.__get_token_critical(value, search_type)

    def __get_token_strings(self, value, search_type):
        if value == "":
            return None
        regx = re.compile(value, re.IGNORECASE)
        if search_type == 'host':
            return {
                "$or": [
                    {"address": regx},
                    {"alias": regx},
                    {"customs.v": regx},
                    {"display_name": regx},
                    {"hostgroup.name": regx},
                    {"ls_output": regx},
                    {"ls_state": regx},
                    {"name": regx},
                    {"notes": regx},
                    {"realm.name": regx},
                ]
            }
        elif search_type == 'service':
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
                    {"hostgroup.name": regx},
                    {"ls_output": regx},
                    {"ls_state": regx},
                    {"name": regx},
                    {"notes": regx},
                    {"realm.name": regx},
                    {"services.name": regx},
                    {"services.alias": regx},
                    {"services_customs.v": regx},
                ]
            }