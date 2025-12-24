# -*- coding: utf-8 -*-
{
        'name'              : 'Quality Module Custom',
        'version'           : '18.0.1.1.1',
        'summary'           : """
                                Quality Custom
                              """,
        'description'       : """ Quality Custom """,
        'category'          : 'quality',
        'author'            : 'Tian',
        'support'           : 'Tian',
        'website'           : '',
        'license'           : "LGPL-3",
        'depends'           : ['quality','quality_control','purchase_stock','web'],
        'data'              : [
                                'security/security.xml',
                                'security/ir.model.access.csv',
                                # 'security/ir_rule.xml',
                                'data/ir_sequence.xml',
                                'template_public/raw_view.xml',
                                'template_public/packaging_view.xml',
                                'template_public/semi_view.xml',
                                'template_public/finished_view.xml',
                                'wizard/import_master_qc.xml',
                                'views/quality_control.xml',
                                'views/master_qc_data.xml',
                                'views/raw_material.xml',
                                'views/packaging_material.xml',
                                'views/semi_finished_raw_material.xml',
                                'views/finished_goods.xml',
                                'views/base_quality_check.xml',
                                'views/account_move.xml',
                                'views/stock_move.xml',
                                'views/stock_lot.xml',
                                'views/menu.xml',
                              ],
}

