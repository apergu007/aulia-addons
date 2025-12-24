import logging
from odoo import models

_logger = logging.getLogger(__name__)

class StockRuleOverride(models.Model):
    _inherit = "stock.rule"


class ProcurementGroupDebug(models.Model):
    _inherit = "procurement.group"
