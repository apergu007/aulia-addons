{
    "name"          : "ATS Documentation",
    "version"       : "18.0.1.0.0",
    "summary"       : "User Manual & Buku Putih viewer for Odoo 18",
    "category"      : "Documents",
    "author"        : "Tian",
    "depends"       : ["base"],
    "data"          : [
                        "security/ir.model.access.csv",
                        "views/documentation_views.xml",
                        "views/menu_views.xml",
                     ],
    "installable"   : True,
    "application"   : True,
    "license"       : "LGPL-3"
}
