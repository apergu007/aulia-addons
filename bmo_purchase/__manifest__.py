# -*- coding: utf-8 -*-
{
        'name'              : 'PR PO Module',
        'version'           : '18.0.1.1.1',
        'summary'           : """
                                PR PO
                              """,
        'description'       : """ Purchase Request & Order """,
        'category'          : 'purchase_request',
        'author'            : 'Tian',
        'support'           : 'Tian',
        'website'           : '',
        'license'           : "LGPL-3",
        'depends'           : ['base','product','quality','bmo_purchase_approval_route','bmo_purchase_request_approval_route','multi_discounts'],
        'data'              : [
                                'security/security.xml',
                                'security/ir.model.access.csv',
                                'data/data.xml',
                                'views/master.xml',
                                'views/prod_categ.xml',
                                'views/pr_views.xml',
                                'views/purchase_request_approval_route.xml',
                                'views/po_views.xml',
                                'views/purchase_team_views.xml',
                                'wizards/purchase_request_line_make_purchase_order.xml',
                                'wizards/cancel_reason.xml',
                                # 'views/menu_view.xml',
                                'reports/report_po.xml',
                                'reports/report_pr_inherit.xml',
                              ],
}

