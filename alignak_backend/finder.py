# import json
# from flask import Blueprint, request, current_app as app
#
# blueprint = Blueprint('prefix_uri', __name__)
#
#
# @blueprint.route("/all", methods=['GET'])
# def search_all():  # pylint: disable=inconsistent-return-statements
#     """
#     Damelo todo papi
#     """
#
#     search = request.args.get('search') or "{}"
#
#     mongo = app.data.driver.db
#     host = mongo["host"]
#
#     from bson import json_util
#
#     result = [h for h in host.find(json.loads(search))]
#
#     return json.dumps(result, default=json_util.default)

import re
import json
from alignak_backend.app import app
from bson.objectid import ObjectId
from datetime import datetime


def is_int(value):
    try:
        num = int(value)
    except ValueError:
        return False
    return True


def join_tables(pipeline):
    pipeline.append({
        '$lookup': {
            'from': 'hostgroup',
            'localField': '_id',
            'foreignField': 'hosts',
            'as': 'hostgroup'
        }
    })
    pipeline.append({
        '$unwind': {
            'path': '$hostgroup',
            'preserveNullAndEmptyArrays': True
        }
    })
    pipeline.append({
        '$lookup': {
            'from': 'realm',
            'localField': '_realm',
            'foreignField': '_id',
            'as': 'realm'
        }
    })
    pipeline.append({
        '$unwind': {
            'path': '$realm',
            'preserveNullAndEmptyArrays': True
        }
    })
    pipeline.append({
        '$lookup': {
            'from': 'service',
            'localField': '_id',
            'foreignField': 'host',
            'as': 'services'
        }
    })
    pipeline.append({
        '$unwind': {
            'path': '$services',
            'preserveNullAndEmptyArrays': True
        }
    })
    pipeline.append({
        '$addFields': {
            'customs': {
                '$objectToArray': '$customs'
            }
        }
    })
    # TODO: Add Services customs
    pipeline.append({
        '$addFields': {
            'services_customs': {
                '$objectToArray': '$services.customs'
            }
        }
    })

    return pipeline


def sort_and_paginate(pipeline, sort, pagination):
    field = '_id'
    order = 1
    offset = int(pagination['offset'])
    limit = int(pagination['limit'])

    if sort is not None:
        order, field = re.match("([-]?)(\\w+)", sort).groups()
        pipeline.append({
            '$sort': {
                field: -1 if order == '-' else 1,
                'ls_state_id': -1,
                'services.ls_state_id': -1,
            }
        })

    pipeline.append({
        '$group': {
            '_id': None,
            'count': {'$sum': 1},
            'results': {'$push': '$$ROOT'}
        }
    })
    pipeline.append({
        '$project': {
            '_id': 0,
            'count': 1,
            'results': {'$slice': ['$results', offset, limit]}
        }
    })
    pipeline.append({
        '$addFields': {
            'pagination': {
                'offset': offset,
                'limit': limit,
                # 'prev': None if offset <= 0 or offset - limit < 0 else offset - limit,
                # 'next': offset + limit if offset <=
            },
            'sort': {
                'field': field,
                'order': 'DESC' if order == '-' else 'ASC'
            },
        }
    })
    return pipeline


def get_token_is(value, search_type):
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
    elif is_int(value):
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


def get_token_isnot(value, search_type):
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
                "$or": [
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
                "$or": [
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
                "$or": [
                    {
                        "$or": [
                            {"services": None},
                            {"services.ls_state": {"$ne": "PENDING"}},
                        ]
                    },
                    {"ls_state": {"$ne": "PENDING"}}
                ]
            },
            "ACK": {
                "$or": [
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
                "$or": [
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
    elif is_int(value):
        if search_type == 'host':
            response = {"ls_state_id": {"$ne": int(value)}}
        elif search_type == 'service':
            response = {"services.ls_state_id": {"$ne": int(value)}}
        else:
            response = {"$or": [{"ls_state_id": {"$ne": int(value)}}, {"services.ls_state_id": {"$ne": int(value)}}]}
    else:
        response = None

    # print('get_token_isnot ==> {}'.format(response))
    return response


def get_token_bi(value, search_type):
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
            response = {"$or": [{"business_impact": {"$gt": int(value)}}, {"services.business_impact": {"$gt": int(value)}}]}
        elif operator == '>=' or operator == '=>':
            response = {"$or": [{"business_impact": {"$gte": int(value)}}, {"services.business_impact": {"$gte": int(value)}}]}
        elif operator == '<':
            response = {"$or": [{"business_impact": {"$lt": int(value)}}, {"services.business_impact": {"$lt": int(value)}}]}
        elif operator == '<=' or operator == '=<':
            response = {"$or": [{"business_impact": {"$lte": int(value)}}, {"services.business_impact": {"$lte": int(value)}}]}
        else:
            response = None

    # print('get_token_bi ==> {}'.format(response))
    return response


# def get_token_name(value, search_type):
#     return None
#
#
# def get_token_host(value, search_type):
#     return None
#
#
# def get_token_service(value, search_type):
#     return None
#
#
# def get_token_contact(value, search_type):
#     return None
#
#
# def get_token_hgroup(value, search_type):
#     return None
#
#
# def get_token_sgroup(value, search_type):
#     return None
#
#
# def get_token_cgroup(value, search_type):
#     return None
#
#
# def get_token_realm(value, search_type):
#     return None
#
#
# def get_token_htag(value, search_type):
#     return None
#
#
# def get_token_stag(value, search_type):
#     return None
#
#
# def get_token_ctag(value, search_type):
#     return None
#
#
# def get_token_duration(value, search_type):
#     return None
#
#
# def get_token_tech(value, search_type):
#     return None
#
#
# def get_token_perf(value, search_type):
#     return None
#
#
# def get_token_reg(value, search_type):
#     return None
#
#
# def get_token_regstate(value, search_type):
#     return None
#
#
# def get_token_loc(value, search_type):
#     return None
#
#
# def get_token_vendor(value, search_type):
#     return None
#
#
# def get_token_model(value, search_type):
#     return None
#
#
# def get_token_city(value, search_type):
#     return None
#
#
# def get_token_isaccess(value, search_type):
#     return None
#
#
# def get_token_his(value, search_type):
#     return None
#
#
# def get_token_ack(value, search_type):
#     return None
#
#
# def get_token_downtime(value, search_type):
#     return None
#
#
# def get_token_crit(value, search_type):
#     return None


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
                {"services_customs.v": regx},
            ]
        }


def get_pipeline(realm, search_dict, sort, pagination):
    pipeline = join_tables([])

    pipeline.append({"$match": {
        "_realm": ObjectId(realm),
        "name": {"$ne": "_dummy"},
        "_is_template": False
    }})

    search_type = search_dict.get('type', 'all')

    for token in search_dict:
        for value in search_dict[token]:
            if token == "is":
                response = get_token_is(value, search_type)
                if response is not None:
                    pipeline.append({"$match": response})
            elif token == "isnot":
                response = get_token_isnot(value, search_type)
                if response is not None:
                    pipeline.append({"$match": response})
            elif token == "bi" or token == "bp":
                response = get_token_bi(value, search_type)
                if response is not None:
                    pipeline.append({"$match": response})
            # elif token == "name":
            #     response = get_token_name(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif (token == "h" or token == "host") and value != "all":
            #     response = get_token_host(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif (token == "s" or token == "service") and value != "all":
            #     response = get_token_service(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif (token == "c" or token == "contact") and value != "all":
            #     response = get_token_contact(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif (token == "hg" or token == "hgroup") and value != "all":
            #     response = get_token_hgroup(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif (token == "sg" or token == "sgroup") and value != "all":
            #     response = get_token_sgroup(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif (token == "cg" or token == "cgroup") and value != "all":
            #     response = get_token_cgroup(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "realm":
            #     response = get_token_realm(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "htag" and value != "all":
            #     response = get_token_htag(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "stag" and value != "all":
            #     response = get_token_stag(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "ctag" and value != "all":
            #     response = get_token_ctag(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "duration":
            #     response = get_token_duration(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "tech":
            #     response = get_token_tech(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "perf":
            #     response = get_token_perf(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "reg":
            #     response = get_token_reg(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "regstate":
            #     response = get_token_regstate(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "loc":
            #     response = get_token_loc(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "vendor":
            #     response = get_token_vendor(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "model":
            #     response = get_token_model(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "city":
            #     response = get_token_city(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "isaccess":
            #     response = get_token_isaccess(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "his":
            #     response = get_token_his(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "ack":
            #     response = get_token_ack(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "downtime":
            #     response = get_token_downtime(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            # elif token == "crit" or token == "critical":
            #     response = get_token_crit(value, search_type)
            #     if response is not None:
            #         pipeline.append({"$match": response})
            elif token == "strings":
                response = get_token_strings(value, search_type)
                if response is not None:
                    pipeline.append({"$match": response})

    return sort_and_paginate(pipeline, sort, pagination)


def all_hosts(search, sort, pagination, user, debug=False):
    mongo = app.data.driver.db
    unique_keys = ['type']
    search_dict = {
        'type': 'all'
    }
    realm = user['_realm']

    order, field = '', '_id'
    if sort is not None:
        order, field = re.match("([-]?)(\\w+)", sort).groups()
    default_response = {
        'count': 0,
        'results': [],
        'pagination': {
            'offset': int(pagination['offset']),
            'limit': int(pagination['limit'])
        },
        'sort': {
            'field': field,
            'order': 'DESC' if order == '-' else 'ASC'
        },
    }
    # app.logger.info("\n\n\n==> RealM: {}\n\n\n".format(realm))

    search_tokens = search.lower().split(' ')
    for token in search_tokens:
        if ':' in token:
            key, value = tuple(token.split(':'))
            if key not in search_dict:
                search_dict[key] = []
            if key in unique_keys:  # This keys can't be append, there must be only one value for them
                search_dict[key] = value
            else:
                search_dict[key].append(value)
        else:
            if 'strings' not in search_dict:
                search_dict['strings'] = []
            search_dict['strings'].append(token)

    host = mongo["host"]
    pipeline = get_pipeline(realm, search_dict, sort, pagination)

    start = datetime.now()
    aggregation = host.aggregate(pipeline, allowDiskUse=True)
    agregation_list = list(aggregation)
    app.logger.debug('\n\n\n==> Aggregation: {}\n\n\n'.format(agregation_list))
    result = agregation_list[0] if len(agregation_list) > 0 else default_response
    result['hosts'] = host.find({"name": {"$ne": "_dummy"}, "_is_template": False}).count()
    result['services'] = mongo['service'].count()
    elapsed = datetime.now() - start
    app.logger.info('\n\n\n==> Mongo aggregation execution time elapsed (hh:mm:ss.ms): {}\n\n\n'.format(elapsed))

    if debug:
        debug = {
            'aggregation': pipeline,
            'search': search,
            'search_tokens': search_tokens,
            'search_dict': search_dict,
            'execution_time': str(elapsed)
        }
        result['debug'] = debug

    return result
