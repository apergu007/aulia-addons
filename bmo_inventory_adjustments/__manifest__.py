# -*- coding: utf-8 -*-
{
'name'          : 'Inventory Adjustment with Lot/Serial BK',
'summary'       : 'Adjust quantity and value with Lot/Serial support (Odoo 18)',
'version'       : '18.0.1.0.0',
'category'      : 'Inventory/Inventory',
'author'        : 'You',
'website'       : 'https://bemosoft.com/',
'depends'       : ['stock', 'mail', 'stock_account'],
'data'          : [
                    'security/ir.model.access.csv',
                    'views/stock_inventory_views.xml',
                    'views/stock_quant_views.xml',
                  ],
'application'   : False,
'installable'   : True,
'license'       : 'LGPL-3',
}