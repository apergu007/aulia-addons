# -*- coding: utf-8 -*-
{
    'name'          : 'Stock Receipt Tolerance Approval',
    'version'       : '18.0.1.0.0',
    'summary'       : 'Require approval for incoming pickings when receipt exceeds product tolerance',
    'description'   : """
                        Module adds tolerance fields on product.template (percent or fixed qty) and prevents
                        validation of incoming pickings when received quantity exceeds the product tolerance.
                        An approval button on the picking allows managers to approve and continue validation.
                    """,
    'category'      : 'Inventory/Stock',
    'author'        : 'Tian',
    'license'       : 'LGPL-3',
    'depends'       : ['stock', 'purchase', 'product'],
    'data'          : [
                        'security/ir.model.access.csv',
                        'security/security.xml',
                        'views/product_template_views.xml',
                        'wizard/picking_warning_wizard_views.xml',
                        'views/stock_picking_views.xml',
                    ],
    'installable'   : True,
    'application'   : False,
    'auto_install'  : False,
}