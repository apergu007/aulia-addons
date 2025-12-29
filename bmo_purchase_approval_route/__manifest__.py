# -*- coding: utf-8 -*-
{
        'name'              : 'PO Dynamic Approval Process',
        'version'           : '18.0.1.1.1',
        'summary'           : """
                                  Dynamic, Customizable and flexible approval cycle for purchase orders
                                  , Purchase dynamic approval
                                  , PO dynamic approval
                                  , RFQ dynamic approval
                                  , purchase approval
                                  , PO approval process
                                  , purchase order approval cycle
                                  , purchase order approval process
                                  , purchase order approval workflow
                                  , flexible approve purchase order
                                  , dynamic approve PO
                                  , dynamic purchase approval
                                  , purchase multi approval
                                  , purchase multi-level approval
                                  , purchase order multiple approval
                              """,
        'description'       : """ Purchase Order Approval Cycle """,
        'category'          : 'Purchases',
        'author'            : 'Tian',
        'support'           : 'Tian',
        'website'           : '',
        'license'           : "LGPL-3",
        'data'              : [
                                'security/ir.model.access.csv',
                                'security/purchase_security.xml',
                                'security/ir_rule.xml',
                                'data/purchase_approval_route.xml',
                                'views/purchase_team_views.xml',
                                'views/purchase_approval_route.xml',
                                'views/res_config_settings_views.xml',
                              ],
        'depends'           : ['base', 'purchase'],
        'images'            : [
                                'static/description/purchase_approval_route.png',
                                'static/description/po_team_form.png',
                                'static/description/po_sent_to_approve.png',
                              ],
}

