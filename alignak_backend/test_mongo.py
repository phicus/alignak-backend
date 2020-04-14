from alignak_backend.app import app
from bson import json_util
from bson.objectid import ObjectId
from datetime import datetime
import re
import json
from alignak_backend.mongo_aggregation import MongoAggregation

with app.app_context():
    mongo = app.data.driver.db
    m_host = mongo["host"]
    m_service = mongo['service']
    m_usergroup = mongo['usergroup']
    m_user = mongo['user']
    page_size = 10

    mongo_aggregation = MongoAggregation()

    def get_user(user):
        u = m_user.find_one({'name': user}, {'_id': 1})
        # print("    get_user: {}".format(u))
        return u

    def get_usergroups(user):
        u = get_user(user).get('_id')
        usergroups = list(m_usergroup.find({'users': ObjectId(u)}, {'_id': 1}))
        # print("    get_usergroups: {}".format(usergroups))
        return [ObjectId(token.get('_id')) for token in usergroups]

    def test_admin():
        print('\n\n\n==> test_admin')
        start = datetime.now()
        pipeline_hosts = [
            {
                '$sort': {
                    'business_impact': -1,
                    'ls_state_id': -1,
                }
            },
            {
                "$match": {
                    "$and": [
                        {"ls_state_id": {"$ne": 0}},
                        {"ls_state": {"$ne": "PENDING"}},
                        {"ls_acknowledged": False},
                        {"ls_downtimed": False},
                        {"ls_state_type": {"$ne": "SOFT"}},
                        {"business_impact": {"$gte": 2}}
                    ]
                    # "$or": [
                    #     {"ls_state_id": 0},
                    #     {"ls_state": "PENDING"},
                    #     {"ls_acknowledged": True},
                    #     {"ls_downtimed": True},
                    #     {"ls_state_type": "SOFT"},
                    #     {"business_impact": {"$gte": 2}}
                    # ]
                }
            },
            {
                "$skip": 0
            },
            {
                "$limit": page_size
            },
            {
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
            },
            # # Count of elements
            # {
            #     "$count": "count"
            # }
        ]
        # print("    test_admin - Pipeline Hosts: {}".format(pipeline_hosts))

        pipeline_services = [
            {
                '$sort': {
                    'business_impact': -1,
                    'ls_state_id': -1,
                }
            },
            {
                "$match": {
                    # "$and": [
                    #     {"ls_state_id": {"$ne": 0}},
                    #     {"ls_state": {"$ne": "PENDING"}},
                    #     {"ls_acknowledged": False},
                    #     {"ls_downtimed": False},
                    #     {"ls_state_type": {"$ne": "SOFT"}},
                    #     {"business_impact": {"$gte": 2}}
                    # ]
                    "$or": [
                        {"ls_state_id": 0},
                        {"ls_state": "PENDING"},
                        {"ls_acknowledged": True},
                        {"ls_downtimed": True},
                        {"ls_state_type": "SOFT"},
                        {"business_impact": {"$gte": 2}}
                    ]
                }
            },
            {
                "$skip": 0
            },
            {
                "$limit": page_size
            },
            # {
            #     '$lookup': {
            #         'from': 'host',
            #         'localField': 'host',
            #         'foreignField': '_id',
            #         'as': 'host',
            #     }
            # },
            # {
            #     '$unwind': {
            #         'path': '$host',
            #         'preserveNullAndEmptyArrays': False
            #     }
            # },
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "business_impact": 1,
                    "ls_acknowledged": 1,
                    "active_checks_enabled": 1,
                    "downtimed": 1,
                    "event_handler_enabled": 1,
                    "ls_state_id": 1,
                    "ls_state": 1,
                    "ls_last_check": 1,
                    "ls_next_check": 1,
                    "ls_output": 1,
                    "host": 1,
                    # "host._id": 1,
                    # "host.name": 1,
                }
            },
            # # Count of elements
            # {
            #     "$count": "count"
            # }
        ]
        # print("    test_admin - Pipeline Services: {}".format(pipeline_services))

        aggregation_hosts = m_host.aggregate(pipeline_hosts, allowDiskUse=True)
        hosts = list(aggregation_hosts)
        # print("    test_admin - Aggregation Hosts ({}): {}".format(len(hosts), hosts))
        aggregation_services = m_service.aggregate(pipeline_services, allowDiskUse=True)
        list_aggregation_services = list(aggregation_services)
        # print("    test_admin - Aggregation Services: {}".format(list_aggregation_services))
        service_host_ids = [ObjectId(h) for h in set([service.get('host') for service in list_aggregation_services])]
        # print("    test_admin - Service Host ids: {}".format(service_host_ids))
        service_hosts = list(m_host.find({"_id": {"$in": service_host_ids}}, {
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
                }))
        # print("    test_admin - Service Host: {}".format(hosts))
        [hosts.append(sh) for sh in service_hosts if sh not in hosts]

        for s in list_aggregation_services:
            for h in hosts:
                if h.get('_id') == s.get('host'):
                    if h.get('services', None) is None:
                        h['services'] = []
                    h.get('services').append(s)

        elapsed = datetime.now() - start
        print("    test_admin - Total Host ({}): {}".format(len(hosts), hosts))
        print('\n==> test_admin (hh:mm:ss.ms): {}\n'.format(elapsed))

    def test_metrics():
        print('\n\n\n==> test_metrics')
        start = datetime.now()
        # usergroups = get_usergroups('noc')
        # print("    test_metrics - usergroups: {}".format(usergroups))
        pipeline_hosts = [
            # {
            #     "$match": {
            #         "usergroups": {
            #             "$in": usergroups
            #         }
            #     }
            # },
            {
                '$sort': {
                    'business_impact': -1,
                    'ls_state_id': -1,
                }
            },
            {
                "$match": {
                    "$and": [
                        {"hostgroups": re.compile("gpon", re.IGNORECASE)},
                        {"ls_perfs.rta": {"$lt": 50}},
                    ]
                }
            },
            {
                "$skip": 0
            },
            {
                "$limit": page_size
            },
            {
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
            },
            # # Count of elements
            # {
            #     "$count": "count"
            # }
        ]
        # print("    test_metrics - Pipeline Hosts: {}".format(pipeline_hosts))

        pipeline_services = [
            # {
            #     "$match": {
            #         "usergroups": {
            #             "$in": usergroups
            #         }
            #     }
            # },
            {
                '$sort': {
                    'business_impact': -1,
                    'ls_state_id': -1,
                }
            },
            {
                "$match": {
                    "$and": [
                        {"ls_perfs.rta": {"$lt": 50}},

                    ]
                }
            },
            {
                "$skip": 0
            },
            {
                "$limit": page_size
            },
            # {
            #     '$lookup': {
            #         'from': 'host',
            #         'localField': 'host',
            #         'foreignField': '_id',
            #         'as': 'host',
            #     }
            # },
            # {
            #     '$unwind': {
            #         'path': '$host',
            #         'preserveNullAndEmptyArrays': False
            #     }
            # },
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "business_impact": 1,
                    "ls_acknowledged": 1,
                    "active_checks_enabled": 1,
                    "downtimed": 1,
                    "event_handler_enabled": 1,
                    "ls_state_id": 1,
                    "ls_state": 1,
                    "ls_last_check": 1,
                    "ls_next_check": 1,
                    "ls_output": 1,
                    "host": 1,
                    # "host._id": 1,
                    # "host.name": 1,
                }
            },
            # # Count of elements
            # {
            #     "$count": "count"
            # }
        ]
        # print("    test_metrics - Pipeline Services: {}".format(pipeline_services))

        aggregation_hosts = m_host.aggregate(pipeline_hosts, allowDiskUse=True)
        hosts = list(aggregation_hosts)
        # print("    test_metrics - Aggregation Hosts ({}): {}".format(len(hosts), hosts))
        aggregation_services = m_service.aggregate(pipeline_services, allowDiskUse=True)
        list_aggregation_services = list(aggregation_services)
        # print("    test_metrics - Aggregation Services: {}".format(list_aggregation_services))
        service_host_ids = [ObjectId(h) for h in set([service.get('host') for service in list_aggregation_services])]
        # print("    test_metrics - Service Host ids: {}".format(service_host_ids))
        service_hosts = list(m_host.find({"_id": {"$in": service_host_ids}}, {
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
                }))
        # print("    test_metrics - Service Host: {}".format(hosts))
        [hosts.append(sh) for sh in service_hosts if sh not in hosts]

        for s in list_aggregation_services:
            for h in hosts:
                if h.get('_id') == s.get('host'):
                    if h.get('services', None) is None:
                        h['services'] = []
                    h.get('services').append(s)

        elapsed = datetime.now() - start
        print("    test_metrics - Total Host ({}): {}".format(len(hosts), hosts))
        print('\n==> test_metrics (hh:mm:ss.ms): {}\n'.format(elapsed))

    def test_noc():
        print('\n\n\n==> test_noc')
        start = datetime.now()
        usergroups = get_usergroups('noc')
        # print("    test_noc - usergroups: {}".format(usergroups))
        pipeline_hosts = [
            # Filter by usergroups
            {
                "$match": {
                    "usergroups": {
                        "$in": usergroups
                    }
                }
            },
            {
                '$sort': {
                    'business_impact': -1,
                    'ls_state_id': -1,
                }
            },
            {
                "$match": {
                    "$and": [
                        {"ls_state_id": {"$ne": 0}},
                        {"ls_state": {"$ne": "PENDING"}},
                        {"ls_acknowledged": False},
                        {"ls_downtimed": False},
                        {"ls_state_type": {"$ne": "SOFT"}},
                        {"business_impact": {"$gte": 2}}
                    ]
                    # "$or": [
                    #     {"ls_state_id": 0},
                    #     {"ls_state": "PENDING"},
                    #     {"ls_acknowledged": True},
                    #     {"ls_downtimed": True},
                    #     {"ls_state_type": "SOFT"},
                    #     {"business_impact": {"$gte": 2}}
                    # ]
                }
            },
            {
                "$skip": 0
            },
            {
                "$limit": page_size
            },
            {
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
            },
            # # Count of elements
            # {
            #     "$count": "count"
            # }
        ]
        # print("    test_noc - Pipeline Hosts: {}".format(pipeline_hosts))

        pipeline_services = [
            # Filter by usergroups
            {
                "$match": {
                    "usergroups": {
                        "$in": usergroups
                    }
                }
            },
            {
                '$sort': {
                    'business_impact': -1,
                    'ls_state_id': -1,
                }
            },
            {
                "$match": {
                    # "$and": [
                    #     {"ls_state_id": {"$ne": 0}},
                    #     {"ls_state": {"$ne": "PENDING"}},
                    #     {"ls_acknowledged": False},
                    #     {"ls_downtimed": False},
                    #     {"ls_state_type": {"$ne": "SOFT"}},
                    #     {"business_impact": {"$gte": 2}}
                    # ]
                    "$or": [
                        {"ls_state_id": 0},
                        {"ls_state": "PENDING"},
                        {"ls_acknowledged": True},
                        {"ls_downtimed": True},
                        {"ls_state_type": "SOFT"},
                        {"business_impact": {"$gte": 2}}
                    ]
                }
            },
            {
                "$skip": 0
            },
            {
                "$limit": page_size
            },
            # {
            #     '$lookup': {
            #         'from': 'host',
            #         'localField': 'host',
            #         'foreignField': '_id',
            #         'as': 'host',
            #     }
            # },
            # {
            #     '$unwind': {
            #         'path': '$host',
            #         'preserveNullAndEmptyArrays': False
            #     }
            # },
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "business_impact": 1,
                    "ls_acknowledged": 1,
                    "active_checks_enabled": 1,
                    "downtimed": 1,
                    "event_handler_enabled": 1,
                    "ls_state_id": 1,
                    "ls_state": 1,
                    "ls_last_check": 1,
                    "ls_next_check": 1,
                    "ls_output": 1,
                    "host": 1,
                    # "host._id": 1,
                    # "host.name": 1,
                }
            },
            # # Count of elements
            # {
            #     "$count": "count"
            # }
        ]
        # print("    test_noc - Pipeline Services: {}".format(pipeline_services))

        aggregation_hosts = m_host.aggregate(pipeline_hosts, allowDiskUse=True)
        hosts = list(aggregation_hosts)
        # print("    test_noc - Aggregation Hosts: {}".format(hosts))
        aggregation_services = m_service.aggregate(pipeline_services, allowDiskUse=True)
        list_aggregation_services = list(aggregation_services)
        # print("    test_noc - Aggregation Services: {}".format(list_aggregation_services))
        service_host_ids = [ObjectId(h) for h in set([service.get('host') for service in list_aggregation_services])]
        # print("    test_noc - Service Host ids: {}".format(service_host_ids))
        service_hosts = list(m_host.find({"_id": {"$in": service_host_ids}}, {
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
        }))
        # print("    test_noc - Service Host: {}".format(service_hosts))
        [hosts.append(sh) for sh in service_hosts if sh not in hosts]
        elapsed = datetime.now() - start
        print("    test_noc - Total Host ({}): {}".format(len(hosts), hosts))
        print('\n==> test_noc (hh:mm:ss.ms): {}\n'.format(elapsed))

    def test_callcenter():
        print('\n\n\n==> test_callcenter')
        start = datetime.now()
        usergroups = get_usergroups('callcenter')
        # print("    test_callcenter - usergroups: {}".format(usergroups))

        regx = re.compile("cpe", re.IGNORECASE)
        pipeline_hosts = [
            # Filter by usergroups
            {
                "$match": {
                    "usergroups": {
                        "$in": usergroups
                    }
                }
            },
            {
                '$sort': {
                    'business_impact': -1,
                    'ls_state_id': -1,
                }
            },
            {
                '$addFields': {
                    'customs': {
                        '$objectToArray': '$customs'
                    }
                }
            },
            {
                "$match": {
                    "$or": [
                        {"address": regx},
                        {"alias": regx},
                        {"customs.v": regx},
                        {"display_name": regx},
                        {"ls_output": regx},
                        {"ls_state": regx},
                        {"name": regx},
                        {"notes": regx},
                    ]
                }
            },
            {
                "$skip": 0
            },
            {
                "$limit": page_size
            },
            {
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
            },
            # # Count of elements
            # {
            #     "$count": "count"
            # }
        ]
        # print("    test_callcenter - Pipeline Hosts: {}".format(pipeline_hosts))

        aggregation_hosts = m_host.aggregate(pipeline_hosts, allowDiskUse=True)
        hosts = list(aggregation_hosts)
        elapsed = datetime.now() - start
        print("    test_callcenter - Hosts ({}): {}".format(len(hosts), hosts))
        print('\n==> test_callcenter (hh:mm:ss.ms): {}\n'.format(elapsed))

    def test_admin2():
        print('\n==> test_admin2')
        hosts = mongo_aggregation.get_hosts(search="isnot:UP isnot:OK isnot:PENDING isnot:ACK "
                                                   + "isnot:DOWNTIME isnot:SOFT bi:>=2", debug=True)
        print("    test_admin2 - Total Host({}/{}): {}".format(len(hosts.get('results')), hosts.get('count'),
                                                               hosts.get('results')))
        print("    test_admin2 - Aggregation: {}".format(
            json.dumps(hosts.get('debug').get('aggregations').get('hosts'), default=json_util.default)))
        print('\n==> test_admin2 (hh:mm:ss.ms): {}\n'.format(hosts.get('debug').get('execution_times')))

    def test_metrics2():
        print('\n==> test_metrics2')
        hosts = mongo_aggregation.get_hosts(search="hg:gpon perf:rta<50", debug=True)
        print("    test_metrics2 - Total Host({}/{}): {}".format(len(hosts.get('results')), hosts.get('count'),
                                                                 hosts.get('results')))
        print("    test_metrics2 - Aggregation: {}".format(
            json.dumps(hosts.get('debug').get('aggregations').get('hosts'), default=json_util.default)))
        print('\n==> test_metrics2 (hh:mm:ss.ms): {}\n'.format(hosts.get('debug').get('execution_times')))

    def test_noc2():
        print('\n==> test_noc2')
        hosts = mongo_aggregation.get_hosts(search="isnot:UP isnot:OK isnot:PENDING isnot:ACK "
                                                   + "isnot:DOWNTIME isnot:SOFT bi:>=2",
                                            user="noc", debug=True)
        print("    test_noc2 - Total Host({}/{}): {}".format(len(hosts.get('results')), hosts.get('count'),
                                                             hosts.get('results')))
        print("    test_noc2 - Aggregation: {}".format(
            json.dumps(hosts.get('debug').get('aggregations').get('hosts'), default=json_util.default)))
        print('\n==> test_noc2 (hh:mm:ss.ms): {}\n'.format(hosts.get('debug').get('execution_times')))

    def test_callcenter2():
        print('\n==> test_callcenter2')
        hosts = mongo_aggregation.get_hosts(search="cpe", user="callcenter", debug=True)
        print("    test_callcenter2 - Total Host({}/{}): {}".format(len(hosts.get('results')), hosts.get('count'),
                                                                    hosts.get('results')))
        print("    test_callcenter2 - Aggregation: {}".format(
            json.dumps(hosts.get('debug').get('aggregations').get('hosts'), default=json_util.default)))
        print('\n==> test_callcenter2 (hh:mm:ss.ms): {}\n'.format(hosts.get('debug').get('execution_times')))


if __name__ == "__main__":
    test_admin()
    test_admin2()
    test_metrics()
    test_metrics2()
    test_noc()
    test_noc2()
    test_callcenter()
    test_callcenter2()

