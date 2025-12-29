# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.osv import expression
import ast


class ProductionLot(models.Model):
    _inherit = 'stock.lot'

    no_analisa_qc = fields.Char(string='No. Analisa QC', compute='_compute_no_analisa_qc', store=True)

    def _compute_no_analisa_qc(self):
        for l in self:
            no = ''
            domain = l._get_quality_check_domain(l)
            quality_checks = self.env['quality.check'].search(domain)
            if quality_checks:
                no = quality_checks.mapped('name')
                if no:
                    no = ', '.join(no)
            l.no_analisa_qc = no

    def action_open_quality_checks(self):
        self.ensure_one()
        res = super().action_open_quality_checks()
        final_domain = expression.AND([res['domain'], self._get_quality_check_domain(self)])
        quality_checks = self.env['quality.check'].search(final_domain)
        qc = quality_checks[0]
        if qc.type_form == 'raw':
            views = "bmo_quality.action_data_qc_raw"
        elif qc.type_form == 'half':
            views = "bmo_quality.action_data_qc_half"
        elif qc.type_form == 'finish':
            views = "bmo_quality.action_finished_goods"
        elif qc.type_form == 'kemas':
            views = "bmo_quality.action_data_qc_kemas"
        else:
            return res 

        action = self.env.ref(views).read()[0]
        action['domain'] = final_domain
        return action
