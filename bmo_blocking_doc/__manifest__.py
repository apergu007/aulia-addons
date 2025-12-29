{
    "name"          : "Blocking Document Info",
    "version"       : "18.0.1.0.0",
    "summary"       : "Show blocking document for MO and Picking in Odoo 18",
    "description"   : """
                        Display smart button and warning message showing which document 
                        is blocking a Manufacturing Order or a Picking (Waiting Another Operation).
                        Fully adapted for Odoo 18 OWL views (no attrs, using invisible expressions).
                      """,
    "author"        : "tian",
    "website"       : "",
    "category"      : "Manufacturing/Inventory",
    "depends"       : ["mrp", "stock"],
    "data"          : [
                        "views/mrp_production_view.xml",
                        "views/stock_picking_view.xml"
                      ],
    "installable"   : True,
    "application"   : False,
    "license"       : "LGPL-3"
}
