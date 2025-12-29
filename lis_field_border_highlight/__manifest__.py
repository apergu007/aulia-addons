# -*- coding: utf-8 -*-
{
    'name': "Field Border Highlight",
    'summary': "To show the field border",
    'description': """ Field Border Highlight """,
    'author': "Loyal IT Solutions Pvt Ltd",
    'website': "https://www.loyalitsolutions.com",
    'category': 'Uncategorized',
    'version': '18.0.1.0.0',
    'license': "LGPL-3",
    'depends': ['base'],
    'assets': {
        'web.assets_backend': [
            'lis_field_border_highlight/static/src/css/styles.css',
        ]
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
