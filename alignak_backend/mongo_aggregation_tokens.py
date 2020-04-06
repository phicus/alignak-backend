import re


class MongoAggregationTokens:

    mongo_comparation_operators = {
        ">": "$gt", ">=": "$gte", "=>": "$gte",
        "<": "$lt", "<=": "$lte", "=<": "$lte",
        "=": "$eq", "==": "$eq",
    }
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}

    @staticmethod
    def __is_int(value):
        try:
            num = int(value)
        except ValueError:
            return False
        return True

    @staticmethod
    def __is_float(value):
        try:
            num = float(value)
        except ValueError:
            return False
        return True

    # Get Token functions, all must be with the name formula get_token_is_<search_token>

    @staticmethod
    def get_token_is(value, search_type):
        value = value.upper()
        token_is = {}
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
                "OK": {"ls_state_id": 0},
                "PENDING": {"ls_state": "PENDING"},
                "ACK": {"ls_acknowledged": True},
                "DOWNTIME": {"ls_downtimed": True},
                "SOFT": {"ls_state_type": "SOFT"},
            }

        if type(value) == str and value in token_is:
            response = token_is[value]
        elif MongoAggregationTokens.__is_int(value):
            response = {"ls_state": int(value)}
        else:
            response = None
        return response

    @staticmethod
    def get_token_isnot(value, search_type):
        value = value.upper()
        token_isnot = {}
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
                "OK": {"ls_state_id": {"$ne": 0}},
                "PENDING": {"ls_state": {"$ne": "PENDING"}},
                "ACK": {"ls_acknowledged": False},
                "DOWNTIME": {"ls_downtimed": False},
                "SOFT": {"ls_state_type": {"$ne": "SOFT"}},
            }
        
        if type(value) == str and value in token_isnot:
            response = token_isnot[value]
        elif MongoAggregationTokens.__is_int(value):
            response = {"ls_state_id": {"$ne": int(value)}}
        else:
            response = None
        return response

    @staticmethod
    def get_token_bi(value, search_type):
        operator, value = re.match("([=><]{0,2})(\\d)", value).groups()
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
        return response

    @staticmethod
    def get_token_bp(value, search_type):
        return MongoAggregationTokens.get_token_bi(value, search_type)

    @staticmethod
    def get_token_name(value, search_type):
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
                    {"alias": regx},
                    {"name": regx},
                ]
            }

    @staticmethod
    def get_token_host(value, search_type):
        if search_type == 'host':
            return MongoAggregationTokens.get_token_name(value, search_type)
        else:
            return None

    @staticmethod
    def get_token_h(value, search_type):
        return MongoAggregationTokens.get_token_host(value, search_type)

    @staticmethod
    def get_token_service(value, search_type):
        if search_type == 'service':
            return MongoAggregationTokens.get_token_name(value, search_type)
        else:
            return None

    @staticmethod
    def get_token_s(value, search_type):
        return MongoAggregationTokens.get_token_service(value, search_type)

    # todo to implemnt with contacts list query
    # @staticmethod
    # def get_token_contact(value, search_type):
    #     if value == "" or value == "all":
    #         return None
    #     regx = re.compile(value, re.IGNORECASE)
    #     return {
    #         "$or": [
    #             {"contacts.name": regx},
    #             {"contacts.alias": regx},
    #         ]
    #     }
    #
    # @staticmethod
    # def get_token_c(value, search_type):
    #     return MongoAggregationTokens.get_token_contact(value, search_type)

    @staticmethod
    def get_token_hostgroup(value, search_type):
        if value == "" or value == "all" or search_type != 'host':
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "hostgroups": regx
        }

    @staticmethod
    def get_token_hgroup(value, search_type):
        return MongoAggregationTokens.get_token_hostgroup(value, search_type)

    @staticmethod
    def get_token_hg(value, search_type):
        return MongoAggregationTokens.get_token_hostgroup(value, search_type)

    @staticmethod
    def get_token_servicegroup(value, search_type):
        if value == "" or value == "all" or search_type != 'service':
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "servicegroups": regx
        }

    @staticmethod
    def get_token_sgroup(value, search_type):
        return MongoAggregationTokens.get_token_servicegroup(value, search_type)

    @staticmethod
    def get_token_sg(value, search_type):
        return MongoAggregationTokens.get_token_servicegroup(value, search_type)

    # todo to implemnt with contactgroups list query
    # @staticmethod
    # def get_token_contactgroup(value, search_type):
    #     if value == "" or value == "all":
    #         return None
    #     regx = re.compile(value, re.IGNORECASE)
    #     if search_type == 'host':
    #         return {
    #             "$or": [
    #                 {"contactgroups.name": regx},
    #                 {"contactgroups.alias": regx},
    #             ]
    #         }
    #     elif search_type == 'service':
    #         return {
    #             "$or": [
    #                 {"services_contactgroups.name": regx},
    #                 {"services_contactgroups.alias": regx},
    #             ]
    #         }
    #     return None
    #
    # @staticmethod
    # def get_token_cgroup(value, search_type):
    #     return MongoAggregationTokens.get_token_contactgroup(value, search_type)
    #
    # @staticmethod
    # def get_token_cg(value, search_type):
    #     return MongoAggregationTokens.get_token_contactgroup(value, search_type)

    # todo to implemnt with realms list query
    # @staticmethod
    # def get_token_realm(value, search_type):
    #     if value == "":
    #         return None
    #     regx = re.compile(value, re.IGNORECASE)
    #     return {
    #         "$or": [
    #             {"realm.name": regx},
    #             {"realm.alias": regx},
    #         ]
    #     }

    @staticmethod
    def get_token_htag(value, search_type):
        if value == "" or value == "all" or search_type != 'host':
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "tags": regx
        }

    @staticmethod
    def get_token_stag(value, search_type):
        if value == "" or value == "all" or search_type != 'service':
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "tags": regx
        }

    # todo to implemnt with contacts list query
    # @staticmethod
    # def get_token_ctag(value, search_type):
    #     if value == "" or value == "all":
    #         return None
    #     regx = re.compile(value, re.IGNORECASE)
    #     if search_type == 'host':
    #         return {
    #             "$or": [
    #                 {"contacts.tags": regx},
    #             ]
    #         }
    #     elif search_type == 'service':
    #         return {
    #             "$or": [
    #                 {"services_contacts.tags": regx},
    #             ]
    #         }

    @staticmethod
    def get_token_duration(value, search_type):
        operator, value = re.match("([=><]{0,2})(\\d)", value).groups()
        if value == "":
            return None
        duration = time.time() - (int(value[0:-1]) * MongoAggregationTokens.seconds_per_unit[value[-1]])
        return {
            "ls_last_state_changed": {MongoAggregationTokens.mongo_comparation_operators[operator]: duration}
        }

    @staticmethod
    def get_token_tech(value, search_type):
        if value == "" or search_type != 'host':
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_TECH'},
                {"customs.v": regx},
            ]
        }

    @staticmethod
    def get_token_perf(value, search_type):
        perf, operator, value = re.match("([\\w_]+)([=><]{0,2})([\\d]+)", value).groups()
        if value == "" or not MongoAggregationTokens.__is_float(value):
            return None
        return {
            "ls_perfs." + perf: {MongoAggregationTokens.mongo_comparation_operators[operator]: float(value)}
        }

    # todo to implement
    # @staticmethod
    # def get_token_reg(value, search_type):
    #     # if i.__class__.my_type == 'service':
    #     #     l2 = i.host.cpe_registration_tags.split(',')
    #     # elif i.__class__.my_type == 'host':
    #     #     l2 = i.cpe_registration_tags.split(',')
    #     # else:
    #     #     l2 = []
    #     return None

    # todo to implement
    # @staticmethod
    # def get_token_regstate(value, search_type):
    #     # if i.__class__.my_type == 'service':
    #     #     l2 = i.host.cpe_registration_state
    #     # elif i.__class__.my_type == 'host':
    #     #     l2 = i.cpe_registration_state
    #     # else:
    #     #     l2 = ''
    #     return None

    @staticmethod
    def get_token_location(value, search_type):
        if value == "" or search_type != 'host':
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_LOCATION'},
                {"customs.v": regx},
            ]
        }

    @staticmethod
    def get_token_loc(value, search_type):
        return MongoAggregationTokens.get_token_location(value, search_type)

    @staticmethod
    def get_token_vendor(value, search_type):
        if value == "" or search_type != 'host':
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_VENDOR'},
                {"customs.v": regx},
            ]
        }

    @staticmethod
    def get_token_model(value, search_type):
        if value == "" or search_type != 'host':
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

    @staticmethod
    def get_token_city(value, search_type):
        if value == "" or search_type != 'host':
            return None
        regx = re.compile(value, re.IGNORECASE)
        return {
            "$and": [
                {"customs.k": '_CUSTOMER_CITY'},
                {"customs.v": regx},
            ]
        }

    @staticmethod
    def get_token_isaccess(value, search_type):
        if search_type != 'host':
            return None
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

    @staticmethod
    def get_token_his(value, search_type):
        if value == "" or search_type != 'host':
            return None
        # regx = re.compile(value, re.IGNORECASE)
        return {
            "$or": [
                {"ls_state_id": int(value)},
                {"ls_state": value.upper()},
            ]
        }

    @staticmethod
    def get_token_ack(value, search_type):
        if value in ("false", "no"):
            return get_token_isnot("ack")
        elif value in ("true", "yes"):
            return get_token_is("ack")
        else:
            return get_token_is("ack")

    @staticmethod
    def get_token_downtime(value, search_type):
        if value in ("false", "no"):
            return get_token_isnot("downtime")
        elif value in ("true", "yes"):
            return get_token_is("downtime")
        else:
            return get_token_is("downtime")

    @staticmethod
    def get_token_critical(value, search_type):
        if value in ("false", "no"):
            return get_token_isnot("critical")
        elif value in ("true", "yes"):
            return get_token_is("critical")
        else:
            return get_token_is("critical")

    @staticmethod
    def get_token_crit(value, search_type):
        return MongoAggregationTokens.get_token_critical(value, search_type)

    @staticmethod
    def get_token_cri(value, search_type):
        return MongoAggregationTokens.get_token_critical(value, search_type)

    @staticmethod
    def get_token_strings(value, search_type):
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
                    # {"hostgroup.name": regx},
                    {"ls_output": regx},
                    {"ls_state": regx},
                    {"name": regx},
                    {"notes": regx},
                    # {"realm.name": regx},
                ]
            }
        elif search_type == 'service':
            return {
                "$or": [
                    {"name": regx},
                    {"alias": regx},
                    {"services_customs.v": regx},
                ]
            }