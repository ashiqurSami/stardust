from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.company'

    coo_signature_image = fields.Image(
        string='Signature by COO',
        max_width=600, max_height=200,  # good size for reports
        help="Upload a transparent PNG/JPG of your handwritten signature."
    )

    md_signature_image = fields.Image(
        string='Signature by MD',
        max_width=600, max_height=200,  # good size for reports
        help="Upload a transparent PNG/JPG of your handwritten signature."
    )
