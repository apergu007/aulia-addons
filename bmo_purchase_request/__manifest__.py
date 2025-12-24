# -*- coding: utf-8 -*-

{
    'name'          : "Custom Purchase Request",
    'summary'       : """ Custom Purchase Request """,
    'description'   : """ Custom Purchase Request """,
    'author'        : 'Tian',
    'maintainer'    : 'Tian',
    'website'       : "https://bemosoft.com/",
    'category'      : 'Purchase Management',
    'version'       : "18.0.1.0.0",
    'license'       : 'AGPL-3',
    'depends'       : ['purchase_request','purchase_stock'],
    'data'          : [
                        # 'security/ir.model.access.csv',
                        'views/purchase_request_view.xml',
                        "report/report_pr_inherit.xml",
                      ],
}
