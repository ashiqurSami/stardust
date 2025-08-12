from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    signature_image = fields.Image(
        string='Signature',
        max_width=600, max_height=200,  # good size for reports
        help="Upload a transparent PNG/JPG of your handwritten signature."
    )
