# -*- coding: utf-8 -*-
{
    'name'          : "Closing Period",
    'summary'       : """ Closing Period""",
    'description'   :   """ Closing Period """,
    'author'        : "Tian",
    'website'       : "https://bemosoft.com/",
    'category'      : 'Tools',
    'version'       : '18.0.1.0.0',
    'license'       : "LGPL-3",
    'depends'       : ['account_accountant','base'],
    'data'          : [
                        'security/res_groups.xml',
                        'security/ir.model.access.csv',
                        'security/account_security.xml',
                        'views/closing_period_view.xml',
                        'views/menu_view.xml',
                     ],
}
