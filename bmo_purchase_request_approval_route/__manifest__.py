# -*- coding: utf-8 -*-
{
        'name'              : 'PR Dynamic Approval Process',
        'version'           : '18.0.1.1.1',
        'summary'           : """
                                PR dynamic approval
                              """,
        'description'       : """ Purchase Request Approval Cycle """,
        'category'          : 'purchase_request',
        'author'            : 'Tian',
        'support'           : 'Tian',
        'website'           : 'https://bemosoft.com/',
        'license'           : "LGPL-3",
        'depends'           : ['base', 'purchase_request'],
        'data'              : [
                                'security/ir.model.access.csv',
                                'security/ir_rule.xml',
                                'views/purchase_request_approval_route.xml',
                                'views/purchase_request_view.xml',
                                'views/purchase_request_line_view.xml',
                                # 'wizard/purchase_request_line_make_purchase_order_view.xml',
                                'views/menu_view.xml',
                              ],
}

