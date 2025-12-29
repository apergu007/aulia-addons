# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _

class PoDeliveryTo(models.Model):
    _name = "po.delivery.to"
    _description = "PO Delivery To"

    types = fields.Selection([
        ('reguler', 'Reguler'),('asset', 'Assets'),
        ('non_reguler', 'Non Reguler'),
        ], string='PR Type')
    p_categ = fields.Selection([
        ('bahan_baku', 'Bahan Baku'),('bahan_kemas', 'Bahan Kemas'),
        ('lain', 'Lain Lain'),
        ], string='Purchase Category')
    picking_type_id = fields.Many2one("stock.picking.type",string="Delivery To")