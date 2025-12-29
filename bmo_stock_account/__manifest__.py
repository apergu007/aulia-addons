# -*- coding: utf-8 -*-

{
    'name'          : "Custom Stock Account",
    'summary'       : """ Stock Account""",
    'description'   : """ Stock Account""",
    'author'        : 'Tian',
    'maintainer'    : 'Tian',
    'website'       : "https://bemosoft.com/",
    'category'      : 'Stock',
    'version'       : "18.0.1.0.0",
    'license'       : 'AGPL-3',
    'depends'       : ['stock_account','account','mrp_account'],
    'data'          : [
                        # 'security/ir.model.access.csv',
                        'views/product_views.xml',
                        'views/prod_categ.xml',
                      ],
}
