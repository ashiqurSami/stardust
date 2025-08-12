from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    laptop_threshold_price = fields.Float(string='Laptop Threshold Price', default=50000.0,
                                          config_parameter="stardust.laptop_threshold_price")
