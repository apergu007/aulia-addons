{
    "name"          : "MRP Material Request",
    "version"       : "18.0.1.0",
    "author"        : "Tian",
    "category"      : "Manufacturing",
    "depends"       : ["mrp", "stock"],
    "data"          : [
                        "security/ir.model.access.csv",
                        "views/mrp_production_view.xml",
                        "wizard/mrp_material_request_wizard_view.xml"
                      ],
    "installable"   : True,
    "application"   : False,
    "license"       : "LGPL-3"
}
