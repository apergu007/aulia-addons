# -*- coding: utf-8 -*-
{
        'name'              : 'Sale Dynamic Approval Process',
        'version'           : '18.0.1.1.1',
        'summary'           : """
                                  Dynamic, Customizable and flexible approval cycle for Sale Order
                              """,
        'description'       : """ Sale Order Approval Cycle """,
        'category'          : 'Sale',
        'author'            : 'Tian',
        'support'           : 'Tian',
        'website'           : '',
        'license'           : "LGPL-3",
        'data'              : [
                                'security/ir.model.access.csv',
                                'security/ir_rule.xml',
                                'views/sale_team_views.xml',
                                'views/sale_approval_route.xml',
                                'views/res_config_settings_views.xml',
                              ],
        'depends'           : ['base', 'sale'],
}

