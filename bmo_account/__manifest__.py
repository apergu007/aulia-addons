# -*- coding: utf-8 -*-
{
        'name'              : 'Accounting Related Module Custom',
        'version'           : '18.0.1.1.1',
        'summary'           : """
                                Accounting Related Custom
                              """,
        'description'       : """ Accounting Related Custom """,
        'category'          : 'account',
        'author'            : 'Tian',
        'support'           : 'Tian',
        'website'           : '',
        'license'           : "LGPL-3",
        'depends'           : ['multi_discounts','bmo_stock_account'],
        'data'              : [
                                # 'security/ir.model.access.csv',
                                # 'security/ir_rule.xml',
                                # 'data/data.xml',
                                'views/account_account.xml',
                                'views/account_move.xml',
                              ],
}

