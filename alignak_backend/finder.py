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
from alignak_backend.mongo_aggregation import MongoAggregation


def all_hosts(search, sort, pagination, user, debug=False):
    realm = user['_realm']
    aggregation = MongoAggregation()
    pipeline = aggregation.get_aggregation(search, realm, sort, pagination)

    mongo = app.data.driver.db
    host = mongo["host"]
    service = mongo['service']

    start = datetime.now()
    aggregation = host.aggregate(pipeline, allowDiskUse=True)
    agregation_list = list(aggregation)

    app.logger.debug('\n\n\n==> Aggregation: {}\n\n\n'.format(agregation_list))

    result = agregation_list[0] if len(agregation_list) > 0 else aggregation.get_default_response()
    result['hosts'] = host.find({"name": {"$ne": "_dummy"}, "_is_template": False}).count()
    result['services'] = service.count()

    elapsed = datetime.now() - start
    app.logger.info('\n\n\n==> Mongo aggregation execution time elapsed (hh:mm:ss.ms): {}\n\n\n'.format(elapsed))

    if debug:
        debug = {
            'aggregation': pipeline,
            'search': search,
            'search_dict': aggregation.get_tokens(search),
            'execution_time': str(elapsed)
        }
        result['debug'] = debug

    return result
