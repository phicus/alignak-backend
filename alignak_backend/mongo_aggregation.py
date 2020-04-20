from alignak_backend.app import app
from bson import json_util
from bson.objectid import ObjectId
from datetime import datetime
import re
import json
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
        self.mongo = app.data.driver.db
        self.m_host = self.mongo["host"]
        self.m_service = self.mongo['service']
        self.m_user = self.mongo['user']
        self.m_usergroup = self.mongo['usergroup']
        # todo to implement and send to MongoAggregationTokens class -> Remove static methods and add to constructor?
        # self.m_realm = self.mongo['realm']
        # self.realms = self.m_realm.find({}, {'name': 1})

        self.unique_keys = ['type']
        self.search_dict = {
            'type': 'all'
        }
        self.valid_search_types = ['all', 'host', 'service']
        self.search = ""
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
        self.bad_tokens = []

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
            "bad_tokens": []
        }

    def get_user(self, user):
        u = self.m_user.find_one({'name': user}, {'_id': 1})
        # print("    get_user: {}".format(u))  # todo change to logger info
        return u

    def get_usergroups(self, user):
        u = self.get_user(user).get('_id')
        usergroups = list(self.m_usergroup.find({'users': ObjectId(u)}, {'_id': 1}))
        # print("    get_usergroups: {}".format(usergroups))  # todo change to logger info
        return [ObjectId(token.get('_id')) for token in usergroups]

    def get_realms(self, name):
        realms = self.m_realms.find({'name', re.compile(name, re.IGNORECASE)}, {'_id': 1})
        return [ObjectId(realm.get('_id')) for realm in realms]

    def get_tokens(self, search=""):
        self.search_dict = {
            'type': 'all'
        }
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

    def get_hosts(self, search="", user=None, sort=None, pagination=None, debug=False):
        elapsed_services = None
        services_aggregation = None
        services = []
        service_host_ids = None
        self.pipeline = []
        self.search = search
        self.get_tokens(search)
        self.__get_search_type()

        if self.search_type != 'host':
            start_services = datetime.now()
            services_aggregation = self.__get_pipeline(search_type='service',
                                                       user=user,
                                                       sort=sort,
                                                       pagination=pagination)
            app.logger.debug('\n\n\n\n==> Search: "{}" ==> Aggregation {}: {}\n\n\n\n'.format(search, 'service',
                                                                                             services_aggregation))
            services = list(self.m_service.aggregate(services_aggregation))
            app.logger.debug('\n\n\n\n==> Results: "{}"\n\n\n\n'.format(services))
            elapsed_services = datetime.now() - start_services
            service_host_ids = [ObjectId(h) for h in
                                set([service.get('host') for service in services])]

        start_hosts = datetime.now()
        hosts_aggregation = self.__get_pipeline(search_type='host',
                                                user=user,
                                                sort=sort,
                                                pagination=pagination,
                                                service_host_ids=service_host_ids)
        app.logger.debug('\n\n\n\n==> Search: "{}" ==> Aggregation {}: {}\n\n\n\n'.format(search, 'host',
                                                                                         hosts_aggregation))
        hosts = list(self.m_host.aggregate(hosts_aggregation))
        app.logger.debug('\n\n\n\n==> Results: "{}"\n\n\n\n'.format(hosts))
        elapsed_hosts = datetime.now() - start_hosts

        start_count = datetime.now()
        if self.search_type == 'service':
            count_aggregation = self.__get_pipeline(search_type='service',
                                                    user=user,
                                                    sort=sort,
                                                    pagination=pagination,
                                                    count=True)
        else:
            count_aggregation = self.__get_pipeline(search_type='host',
                                                    user=user,
                                                    sort=sort,
                                                    pagination=pagination,
                                                    service_host_ids=service_host_ids,
                                                    count=True)
        count = list(self.m_host.aggregate(count_aggregation))
        elapsed_count = datetime.now() - start_count

        if self.search_type != 'host' and len(services) > 0:
            for s in services:
                host = next(h for h in hosts if h.get('_id') == s.get('host'))
                if host.get('services', None) is None:
                    host['services'] = []
                host.get('services').append(s)
                # host['services'] = s
                # hosts.append(host)
                # for h in hosts:
                #     if h.get('_id') == s.get('host'):
                #         if h.get('services', None) is None:
                #             h['services'] = []
                #         h.get('services').append(s)

        result = {
            "count": count[0].get('count', 0) if len(count) > 0 else 0,
            "results": hosts,
            "pagination": {
                "offset": self.pagination.get('offset'),
                "limit": self.pagination.get('limit'),
            },
            "sort": {
                "field": self.field,
                "order": "ASC" if self.order == 1 else "DESC"
            },
            "hosts": self.m_host.find({"name": {"$ne": "_dummy"}, "_is_template": False}).count(),
            "services": self.m_service.count(),
            "bad_tokens": self.bad_tokens,
        }

        if debug:
            result['debug'] = {
                "aggregations": {
                    "services": services_aggregation,
                    "hosts": hosts_aggregation,
                    "count": count_aggregation,
                },
                'search': search,
                'search_dict': self.search_dict,
                "execution_times": {
                    "services": "{}".format(elapsed_services),
                    "hosts": "{}".format(elapsed_hosts),
                    "count": "{}".format(elapsed_count),
                    # "total": "{}".format(elapsed_services + elapsed_hosts + elapsed_count)
                }
            }

        return result

    def __get_search_type(self):
        search_type = self.search_dict.get('type', 'all')
        if search_type in self.valid_search_types:
            self.search_type = search_type
        self.search_dict.pop('type', None)

    def __get_pipeline(self,
                       search_type='host',
                       user=None,
                       sort=None,
                       pagination=None,
                       count=False,
                       service_host_ids=None):
        self.pipeline = []
        self.bad_tokens = []

        # First filter by usergroup if defined, and remove templates and dummys
        if user is not None:
            usergroups = self.get_usergroups(user)
            if len(usergroups) > 0:
                self.pipeline.append({"$match": {
                    "usergroups": {"$in": usergroups},
                }})

        # todo to deprecated
        self.pipeline.append({"$match": {  # todo to deprecated
            "name": {"$ne": "_dummy"},  # todo to deprecated
            "_is_template": False  # todo to deprecated
        }})

        # Second for every token in search_dict append specific search
        matchs = []
        for token in self.search_dict:
            for value in self.search_dict[token]:
                get_token_function = "get_token_{}".format(token)
                get_token = getattr(MongoAggregationTokens, get_token_function, None)
                if get_token is not None:
                    response = get_token(value, search_type)
                    if response is not None:
                        matchs.append(response)
                else:
                    self.bad_tokens.append(token)
        if service_host_ids is not None and len(service_host_ids) > 0:
            if len(matchs) > 0:
                self.pipeline.append({"$match": {'$or': [{"_id": {"$in": service_host_ids}}, {'$and': matchs}]}})
            else:
                self.pipeline.append({"$match": {'$or': [{"_id": {"$in": service_host_ids}}]}})
        elif len(matchs) > 0:
            self.pipeline.append({"$match": {'$and': matchs}})

        # Third, sort, paginate and project fields that we need
        self.__sort(sort)

        # Fourth if count attribute is set, we add the count elsewhere we paginate and project fields needded
        if count:
            self.pipeline.append({
                "$count": "count"
            })
        else:
            self.__paginate(pagination)
            self.__project(search_type)

        return self.pipeline

    def __project(self, search_type='host'):
        if search_type == 'host':
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
                }
            })
        else:
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
                    "host": 1,
                }
            })

    def __sort(self, sort=None):
        if sort is not None:
            order, field = re.match("([-]?)(\\w+)", sort).groups()
            if order is not None and field is not None and field not in [
                "business_impact",
                "services.business_impact",
                "ls_state_id",
                "services.ls_state_id"
            ]:
                self.field = field
                self.order = order

        self.pipeline.append({
            '$sort': {
                'business_impact': -1,
                'ls_state_id': -1,
                self.field: -1 if self.order == '-' else 1,
            }
        })

    def __paginate(self, pagination=None):
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
