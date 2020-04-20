// Add service metrics
db.service.find({}, {_id: 1}).forEach(function(s) {
    [{'metric' : 'quality', 'uom' : '%'}, {'metric' : 'dntxlatency', 'uom' : 'ms'}, {'metric' : 'ccq', 'uom' : '%'}, {'metric' : 'uptxlatency', 'uom' : 'ms'}].forEach(function(m) {
        db.perfdata.insert(
            {
                "type": "service",
                "host": null,
                "service": s._id,
                "min": 0,
                "max": 100,
                "thresholds": [
                    Math.floor(Math.random() * 50),
                    Math.floor(Math.random() * 50) + 50
                ],
                "value": Math.floor(Math.random() * 100),
                "metric": m.metric,
                "uom": m.uom
            }
        )        
    });
});

// Add metrics into service collection
db.service.updateMany({}, {$set: {ls_perfs: {}}});
db.service.find({}, {_id: 1}).forEach(function(s) {
    [{'metric' : 'quality', 'uom' : '%'}, {'metric' : 'dntxlatency', 'uom' : 'ms'}, {'metric' : 'ccq', 'uom' : '%'}, {'metric' : 'uptxlatency', 'uom' : 'ms'}].forEach(function(m) {
//        var metric_value = {
//            "min": 0,
//            "max": 100,
//            "thresholds": [
//                Math.floor(Math.random() * 50),
//                Math.floor(Math.random() * 50) + 50
//            ],
//            "value": Math.floor(Math.random() * 100),
//            "metric": m.metric,
//            "uom": m.uom
//        }
        var metric = {}
        metric["ls_perfs." + m.metric] = Math.floor(Math.random() * 100);    
        db.service.updateOne(
            {
                _id : s._id
            },
            {
                $set : metric
            }
        )        
    });
});


// Add hosts metrics
db.host.find({}, {_id: 1}).forEach(function(h) {
    [{'metric' : 'rta', 'uom' : 'ms'}, {'metric' : 'pl', 'uom' : '%'}].forEach(function(m) {
        db.perfdata.insert(
            {
                "min": 0,
                "max": 100,
                "thresholds": [
                    Math.floor(Math.random() * 50),
                    Math.floor(Math.random() * 50) + 50
                ],
                "value": Math.floor(Math.random() * 100),
                "metric": h.metric,
                "uom": h.uom
            }
        )        
    });
});

// Add metrics into host collection
db.host.updateMany({}, {$set: {ls_perfs: {}}});
db.host.find({}, {_id: 1}).forEach(function(h) {
    [{'metric' : 'rta', 'uom' : 'ms'}, {'metric' : 'pl', 'uom' : '%'}].forEach(function(m) {
//        var metric_value = {
//            "min": 0,
//            "max": 100,
//            "thresholds": [
//                Math.floor(Math.random() * 50),
//                Math.floor(Math.random() * 50) + 50
//            ],
//            "value": Math.floor(Math.random() * 100),
//            "metric": m.metric,
//            "uom": m.uom
//        }
        var metric = {}
        metric["ls_perfs." + m.metric] = Math.floor(Math.random() * 100);
        db.host.updateOne(
            {
                _id : h._id
            },
            {
                $set : metric
            }
        )        
    });
});


// Add hostgroups to hosts
db.host.updateMany({}, { $set : { hostgroups : []}});
db.hostgroups.find({}, {
    name: 1,
    hosts: 1
}).forEach(function(hg) {
    hg.hosts.forEach(function(h) {
        print(hg.name + ': ' + h + '\n')
        db.host.updateOne({
            _id: h
        }, {
            $push: {
                hostgroup: hg.name
            }
        })
    })
})

db.host.updateMany({
		name: {
				$regex: /cpe/
		},
		"ls_perfs.rta" : {
				$not : { $mod: [ 2, 0 ] }
		}
}, {
		$push: {
				hostgroups: 'cpegpon'
		}
})

db.host.updateMany({
		name: {
				$regex: /cpe/
		},
		"ls_perfs.rta" : {
				$mod: [ 2, 0 ]
		}
}, {
		$push: {
				hostgroups: 'cpewimax'
		}
})



user: {'_id': ObjectId('5cf787458f06ce2743d86b34'), 'service_notification_options': ['w', 'u', 'c', 'r', 'f', 's'], '_etag': 'c1f08562cbf0ed8c4ade9587fa03137b1dfdab59', 'address3': '', '_template_fields': [], '_is_template': False, 'definition_order': 100, 'tags': [], 'address1': '', '_templates': [], 'service_notifications_enabled': False, 'address4': '', 'address5': '', 'address6': '', 'customs': {}, 'is_admin': True, 'skill_level': 2, 'can_submit_commands': True, 'password': 'pbkdf2:sha1:150000$pQelI6gX$0f5229616dd5fc7ced72474237bf638c3016478d', 'pager': '', 'can_update_livestate': True, '_realm': ObjectId('5c0fd9d6ea20af5e9be34a76'), 'notificationways': [], '_updated': datetime.datetime(2019, 6, 5, 9, 11, 33, tzinfo=<bson.tz_util.FixedOffset object at 0x7f2969be2da0>), 'host_notification_period': ObjectId('5c0fd9d6ea20af5e9be34a7a'), 'name': 'admin', 'host_notifications_enabled': False, '_sub_realm': True, 'notes': '', 'service_notification_period': ObjectId('5c0fd9d6ea20af5e9be34a7a'), 'min_business_impact': 0, 'schema_version': 2, 'email': '', 'alias': 'Administrator', 'token': '1559725893405-90af1fc4-9f24-4a9e-a16c-e7e57f7fb521', 'webui_visible': True, 'ui_preferences': {'service-panel-check': {'opened': True}, 'dashboard_widgets': [{'id': 'services_chart_1579623964374', 'uri': '/services/widget', 'name': 'Services chart widget', 'icon': 'pie-chart', 'template': 'services_chart_widget', 'x': 6, 'y': 0, 'width': 6, 'minWidth': '3', 'maxWidth': '12', 'height': 11, 'minHeight': '2', 'maxHeight': '64'}, {'id': 'services_table_1564565425736', 'uri': '/services/widget?search=&count=-1&filter=', 'name': 'Services table widget', 'icon': 'table', 'template': 'services_table_widget', 'x': 0, 'y': 0, 'width': 6, 'minWidth': '3', 'maxWidth': '12', 'height': 17, 'minHeight': '2', 'maxHeight': '64'}], 'host-panel-check': {'opened': True}, 'table_host': {'search': {'regex': False, 'search': '', 'caseInsensitive': True, 'smart': True}, 'start': 0, 'length': 25, 'time': 1584215840732, 'order': [[0, 'desc']], 'columns': [{'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}]}, 'table_service': {'search': {'regex': False, 'search': '', 'caseInsensitive': True, 'smart': True}, 'start': 0, 'length': 25, 'time': 1586775615476, 'order': [[0, 'desc']], 'columns': [{'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}]}, 'table_history': {'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}, 'time': 1562919364202, 'start': 0, 'length': 25, 'order': [[0, 'desc']], 'columns': [{'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}]}, 'table_alignak': {'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}, 'time': 1564048812157, 'start': 0, 'length': 25, 'order': [[0, 'desc']], 'columns': [{'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}]}, 'table_hostgroup': {'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}, 'time': 1571479085382, 'start': 0, 'length': 25, 'order': [[0, 'desc']], 'columns': [{'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}]}, 'templates_table_host': {'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}, 'time': 1573525950789, 'start': 0, 'length': 25, 'order': [[0, 'desc']], 'columns': [{'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}]}, 'host-panel-variables': {'opened': True}, 'host-panel-perfdata': {'opened': True}, 'services-tree': {'opened': True}, 'table_user': {'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}, 'time': 1578414503370, 'start': 0, 'length': 25, 'order': [[0, 'desc']], 'columns': [{'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': False, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}]}, 'service-panel-perfdata': {'opened': True}, 'table_statsd': {'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}, 'time': 1582882198118, 'start': 0, 'length': 25, 'order': [[0, 'desc']], 'columns': [{'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}]}, 'table_grafana': {'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}, 'time': 1582882202851, 'start': 0, 'length': 25, 'order': [[0, 'desc']], 'columns': [{'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}, {'visible': True, 'search': {'search': '', 'smart': True, 'regex': False, 'caseInsensitive': True}}]}}, '_created': datetime.datetime(2019, 6, 5, 9, 11, 33, tzinfo=<bson.tz_util.FixedOffset object at 0x7f2969be2da0>), 'back_role_super_admin': True, 'imported_from': 'unknown', 'address2': '', 'host_notification_options': ['d', 'u', 'r', 'f', 's'], 'host_notification_commands': [ObjectId('5c0fd9d6ea20af5e9be34a7d')], 'service_notification_commands': [ObjectId('5c0fd9d6ea20af5e9be34a7d')]}