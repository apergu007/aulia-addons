# -*- coding: utf-8 -*-
{
    "name"          : "Payment",
    "author"        : "Tian",
    "website"       : "",
    "category"      : "custom",
    "version"       : "18.0.0.0.1",
    "license"       : "OPL-1",
    "category"      : 'Accounting',
    'depends'       : ['account','accountant'],
    'data'          : [
                        'security/ir.model.access.csv',
                        'security/security.xml',
                        'views/account_payment_view.xml',
                        'views/menu.xml',
                     ],
}
