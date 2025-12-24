# -*- coding: utf-8 -*-

{
    'name'          : "Stock",
    'summary'       : """ Stock """,
    'description'   : """ Stock """,
    'author'        : 'Tian',
    'maintainer'    : 'Tian',
    'website'       : " ",
    'category'      : 'Stock',
    'version'       : "18.0.1.0.0",
    'license'       : 'AGPL-3',
    'depends'       : ['stock','stock_account'],
    'data'          : [
                        # 'security/ir.model.access.csv',
                        'security/groups_security.xml',
                        'data/cron.xml',
                        'views/product.xml',
                        'views/stock_view.xml',
                        'views/stock_valuation.xml',
                      ],
}
