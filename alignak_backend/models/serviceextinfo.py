def get_name():
    return 'serviceextinfo'


def get_schema():
    return {
        'schema': {
            'imported_from': {
                'type': 'string',
                'default': ''
            },

            'use': {
                'type': 'objectid',
                'data_relation': {
                    'resource': 'serviceextinfo',
                    'embeddable': True
                },
            },

            'name': {
                'type': 'string',
                'default' : ''
            },

            'definition_order': {
                'type': 'integer',
                'default': 100
            },

            'register': {
                'type': 'boolean',
                'default': True
            },

            'host_name': {
                'type': 'string',
                'required': True,
                'unique': True,
                'default' : ''
            },

            'service_description': {
                'type': 'string',
                'default' : ''
            },

            'notes': {
                'type': 'string',
                'default' : ''
            },

            'notes_url': {
                'type': 'string',
                'default' : ''
            },

            'icon_image': {
                'type': 'string',
                'default' : ''
            },

            'icon_image_alt': {
                'type': 'string',
                'default' : ''
            },
        }
    }