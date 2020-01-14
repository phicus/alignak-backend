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
        '$addFields': {
            'customs': {
                '$objectToArray': '$customs'
            }
        }
    })

    return pipeline


def get_token_is(value):
    token_is = {
        "UP": {"services.ls_state_id": 0},
        "OK": {"ls_state_id": 0},
        "PENDING": {"$or": [{"ls_state": "PENDING"}, {"services.ls_state": "PENDING"}]},
        "ACK": {"$or": [{"ls_acknowledged": True}, {"services.ls_acknowledged": True}]},
        "DOWNTIME": {"$or": [{"ls_downtimed": True}, {"services.ls_downtimed": True}]},
        "SOFT": {"$or": [{"ls_state_type": "SOFT"}, {"services.ls_state_type": "SOFT"}]},
    }

    if type(value) == str and value in token_is:
        response = token_is[value]
    elif is_int(value):
        response = {"$or": [{"ls_state": int(value)}, {"services.ls_state": int(value)}]}
    else:
        response = None

    # print('get_token_is ==> {}'.format(response))
    return response


def get_token_isnot(value):
    token_isnot = {
        "UP": {"services.ls_state_id": {"$ne": 0}},
        "OK": {"ls_state_id": {"$ne": 0}},
        "PENDING": {"$or": [{"ls_state": {"$ne": "PENDING"}}, {"services.ls_state": {"$ne": "PENDING"}}]},
        "ACK": {"$or": [{"ls_acknowledged": False}, {"services.ls_acknowledged": False}]},
        "DOWNTIME": {"$or": [{"ls_downtimed": False}, {"services.ls_downtimed": False}]},
        "SOFT": {"$or": [{"ls_state_type": {"$ne": "SOFT"}}, {"services.ls_state_type": {"$ne": "SOFT"}}]},
    }
    # print('get_token_isnot ==> V: {}, T: {}, In {}, isInt: {}'
    #       .format(value, type(value), value in token_isnot, is_int(value)))
    if type(value) == str and value in token_isnot:
        response = token_isnot[value]
    elif is_int(value):
        response = {"$or": [{"ls_state_id": {"$ne": int(value)}}, {"services.ls_state_id": {"$ne": int(value)}}]}
    else:
        response = None

    # print('get_token_isnot ==> {}'.format(response))
    return response


def get_token_bi(value):
    operator, value = re.match("([=><]{0,2})(\\d)", value).groups()

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


def get_token_strings(value):
    if value is "":
        return None
    regx = re.compile(value, re.IGNORECASE)
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
        ]
    }


def sort_and_paginate(pipeline, sort, pagination):
    if sort is not None:
        asc, field = re.match("([-]?)(\\w)", sort).groups()
        pipeline.append({'$sort': {field: -1 if asc == '-' else 1}})

    pipeline.append({
        '$group': {
            '_id': None,
            'count': {'$sum': 1},
            'results': {'$push': '$$ROOT'}
        }
    })
    pipeline.append({
        '$project': {
            'count': 1,
            'offset': 1,
            'limit': 1,
            'rows': {'$slice': ['$results', int(pagination['offset']), int(pagination['limit'])]}
        }
    })
    pipeline.append({
        '$addFields': {
            'offset': int(pagination['offset']),
            'limit': int(pagination['limit'])
        }
    })
    return pipeline


def get_pipeline(search_dict, sort, pagination):
    pipeline = join_tables([])
    for token in search_dict:
        for value in search_dict[token]:
            if token == "is":
                response = get_token_is(value)
                if response is not None:
                    pipeline.append({"$match": response})
            elif token == "isnot":
                response = get_token_isnot(value)
                if response is not None:
                    pipeline.append({"$match": response})
            elif token == "bi":
                response = get_token_bi(value)
                if response is not None:
                    pipeline.append({"$match": response})
            elif token == "strings":
                response = get_token_strings(value)
                if response is not None:
                    pipeline.append({"$match": response})

    return sort_and_paginate(pipeline, sort, pagination)


def all_hosts(search, sort, pagination, debug=False):
    mongo = app.data.driver.db
    search_dict = {}

    search_tokens = search.split(' ')
    for token in search_tokens:
        if ':' in token:
            key, value = tuple(token.split(':'))
            if key not in search_dict:
                search_dict[key] = []
            search_dict[key].append(value)
        else:
            if 'strings' not in search_dict:
                search_dict['strings'] = []
            search_dict['strings'].append(token)

    host = mongo["host"]
    pipeline = get_pipeline(search_dict, sort, pagination)

    if debug is not False:
        return {
            'aggregation': pipeline,
            'search': search,
            'search_tokens': search_tokens,
            'search_dict': search_dict
        }
    else:
        return [h for h in host.aggregate(pipeline)]
