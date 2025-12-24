from collections import defaultdict, namedtuple
from dateutil.relativedelta import relativedelta
from math import log10

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.date_utils import add, subtract
from odoo.tools.float_utils import float_round, float_compare
from odoo.osv.expression import OR, AND, FALSE_DOMAIN
from collections import OrderedDict


class MrpProductionSchedule(models.Model):
    _inherit = 'mrp.production.schedule'