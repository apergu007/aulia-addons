# -*- coding: utf-8 -*-

{
    'name'          : "Sales",
    'summary'       : """ Sales """,
    'description'   : """ Sales """,
    'author'        : 'Tian',
    'maintainer'    : 'Tian',
    'website'       : " ",
    'category'      : 'Sales/Sales',
    'version'       : "18.0.1.0.0",
    'license'       : 'AGPL-3',
    'depends'       : ['sale','bmo_sale_approval_route','multi_discounts'],
    'data'          : [
                        'security/security.xml',
                        'security/ir.model.access.csv',
                        'report/sale_inv_views.xml',
                        'views/master.xml',
                        'views/sale_approve.xml',
                        'views/account_move_views.xml',
                        'views/product.xml',
                        'views/partner.xml',
                        'views/sale_order.xml',
                      ],
}
