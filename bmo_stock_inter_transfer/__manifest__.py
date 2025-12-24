# -*- coding: utf-8 -*-
{
    'name'          : 'Stock Internal Transfer Accounting',
    'version'       : '18.0.1.0.0',
    'category'      : 'Inventory/Accounting',
    'summary'       : 'Internal transfer accounting for Odoo 18',
    'description'   : 'Accounting entries for internal transfer & production layer movement.',
    'author'        : 'Tian',
    'license'       : 'LGPL-3',
    'depends'       : ['stock_account','mrp_account'],
    'data'          : [
                        'security/ir.model.access.csv',
                        'views/product_views.xml',
                        'views/stock_picking_type_views.xml',
                        'views/res_company_views.xml',
                      ],
    'installable'   : True,
}
