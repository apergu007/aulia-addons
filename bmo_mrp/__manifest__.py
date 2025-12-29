# -*- coding: utf-8 -*-

{
    'name'          : "BMO MRP",
    'summary'       : """ MRP """,
    'description'   : """ MRP  """,
    'author'        : 'Tian',
    'maintainer'    : 'Tian',
    'website'       : " ",
    'category'      : 'Manufacturing/Manufacturing',
    'version'       : "18.0.1.0.0",
    'license'       : 'AGPL-3',
    'depends'       : ['mrp','bmo_stock','mrp_mps'],
    'data'          : [
                        'security/ir.model.access.csv',
                        'security/security.xml',
                        'views/bom.xml',
                        'views/production.xml',
                        'views/mrp_mps_views.xml',
                        'views/mrp_eco.xml',
                        'views/product_views.xml',
                        'wizard/confirmation_qty.xml',
                      ],
}
