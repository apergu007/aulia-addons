{
    'name'          : 'BMO Report - Faktur Keluaran Excel',
    'version'       : '18.0.1.1.1',
    'summary'       : 'Laporan Faktur Keluaran dalam format Excel',
    'author'        : 'Tian',
    'depends'       : ['account'],
    'category'      : 'Accounting',
    'license'       : 'AGPL-3',
    'data'          : [
                        'security/ir.model.access.csv',
                        'wizard/faktur_keluaran_wizard.xml'
                      ],
    'installable'   : True,
    'application'   : False
}