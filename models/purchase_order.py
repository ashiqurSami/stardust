from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..utils.mail_utils import get_smtp_server_email
import num2words

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    approval_state = fields.Selection([
        ("draft", "Draft"),
        ("coo_confirmed", "Confirmed by COO"),
        ("coo_approved", "Approved by COO"),
        ("md_waiting", "Waiting for MD Approval"),
        ("md_approved", "Approved by MD"),
    ], default="draft", tracking=True, copy=False, readonly=True)

    requires_md_approval = fields.Boolean(store=True, readonly=True, compute="_compute_requires_md_approval")
    approved_by = fields.Many2one("res.users", string="Approved By", readonly=True, copy=False, tracking=True)
    confirmed_by = fields.Many2one("res.users", string="Confirmed By", readonly=True, copy=False, tracking=True)
    confirmed_date = fields.Datetime(string="Confirmation Date", readonly=True, copy=False, tracking=True)

    @api.depends("order_line.price_unit")
    def _compute_requires_md_approval(self):
        """
        Computes whether each purchase order requires MD approval based on the price threshold
        configured in `stardust.laptop_threshold_price`. Sets `requires_md_approval` to True
        if any order line's price exceeds the threshold.
        """
        ICP = self.env['ir.config_parameter'].sudo()
        laptop_threshold_price = float(ICP.get_param("stardust.laptop_threshold_price", default=50000.0))

        for order in self:
            order.requires_md_approval = any(l.price_unit > laptop_threshold_price for l in order.order_line)

    def button_confirm(self):
        for order in self:
            # If MD approval is required: then the approval state must be md_approved
            if order.requires_md_approval and order.approval_state != 'md_approved':
                raise UserError(_("MD approval is required before confirming this Purchase Order."))

            # If MD approval is not required: then the approval state must be coo_confirmed
            if not order.requires_md_approval and order.approval_state != 'coo_confirmed':
                raise UserError(_("COO must approve this Purchase Order before confirmation."))
        return super().button_confirm()

    def notify_vendor(self,order):
        if order.state != 'purchase':
            return
        email_values = {
            'email_from': get_smtp_server_email(self.env),
            'email_to': order.partner_id.email,
            'subject': f'New PO is created {order.name}'
        }
        contexts = {
            'po_name': order.name,
            'approved_by': order.approved_by.name,
            'approval_date': order.date_approve,
            'contact_person': order.create_uid.name,
            'contact_person_email': order.create_uid.email
        }
        # Get the email template for notifying the vendor
        template = self.env.ref('stardust.email_template_notify_vendor').sudo()

        #send email to vendor
        template.with_context(**contexts).send_mail(order.id, email_values=email_values)

    def action_coo_confirm(self):
        """
        Step 1 for COO. Does NOT finalize any PO
        - If MD approval required → go to md_waiting state and enables MD Approve button
        - If MD approval not required → stay in coo_confirmed and enables COO Approve button
        """
        for order in self:
            if order.state not in ('draft', 'sent'):
                raise UserError(_("Only RFQs can be confirmed by the COO."))

            if order.approval_state in ('coo_approved', 'md_approved'):
                raise UserError(_("This Purchase Order has already been finally approved."))

            vals = {
                'confirmed_by': self.env.user.id,
                'confirmed_date': fields.Datetime.now(),
            }
            if order.requires_md_approval:
                vals['approval_state'] = 'md_waiting'
                body = _("Confirmed by COO. Waiting for MD approval.")
            else:
                vals['approval_state'] = 'coo_confirmed'
                body = _("Confirmed by COO. MD approval not required.")
            order.write(vals)
            order.message_post(body=body)
        return True

    def action_coo_approve(self):
        """
        Step 2 for COO, when MD approval is NOT required. Finalizes the PO
        """
        for order in self:
            if order.state not in ('draft', 'sent'):
                raise UserError(_("Only RFQs can be approved by the COO."))
            if order.requires_md_approval:
                raise UserError(_("MD approval is required for this PO; COO cannot finalize."))
            if order.approval_state != 'coo_confirmed':
                raise UserError(_("COO approval is only allowed after COO has confirmed the RFQ."))

            order.write({
                'approval_state': 'coo_approved',
                'approved_by': self.env.user.id,
            })
            order.message_post(body=_("COO approved. Finalizing Purchase Order."))
            super(PurchaseOrder, order).button_confirm()
            self.notify_vendor(order)  #send email to vendor
        return True

    def action_md_approve(self):
        """
        Final approval by MD when MD approval is required for exceeding the threshold price. Finalizes the PO
        """
        for order in self:
            if order.state not in ('draft', 'sent'):
                raise UserError(_("Only RFQs can be approved by the MD."))
            if not order.requires_md_approval:
                raise UserError(_("This PO does not require MD approval."))
            if order.approval_state != 'md_waiting':
                raise UserError(_("This PO is not waiting for MD approval."))

            order.write({
                'approval_state': 'md_approved',
                'approved_by': self.env.user.id,
            })
            order.message_post(body=_("MD approved. Finalizing Purchase Order."))
            super(PurchaseOrder, order).button_confirm()
            self.notify_vendor(order) #send email to vendor
        return True

    def button_draft(self):
        # run the native cancel (sets state='cancel', does all core logic)
        res = super().button_draft()

        # reset custom approval workflow to Draft
        for order in self:
            order.write({
                'approval_state': 'draft',
                'confirmed_by': False,
                'confirmed_date': False,
                'approved_by': False,
            })
            order.message_post(body=_("Purchase Order cancelled. Approval workflow reset to Draft."))

        return res

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('stardust.group_stardust_procurement_team'):
            raise UserError("You do not have permission to create Purchase Orders.")
        return super(PurchaseOrder, self).create(vals_list)

    def amount_total_to_words(self):
        # Get the company's currency code (e.g., USD, EUR, BDT)
        currency_code = self.currency_id.name

        # Check if the currency is BDT (Bangladeshi Taka)
        if currency_code == 'BDT':
            # Custom logic for converting BDT to words
            return self.convert_bdt_to_words(self.amount_total)
        else:
            # Convert the amount_total to words using num2words for supported currencies
            words = num2words.num2words(self.amount_total, to='currency', lang='en', currency=currency_code)
            return words.title()

    def convert_bdt_to_words(self, amount):
        # Here we create a custom method to convert BDT amount to words
        taka_in_words = num2words.num2words(amount, to='currency', lang='en',
                                            currency='INR')  # INR format is similar to BDT in words
        # Replace "Rupees" with "Taka" and "Paise" with "Poisha"
        taka_in_words = taka_in_words.replace("Rupees", "Taka").replace("rupees", "taka")
        taka_in_words = taka_in_words.replace("Paise", "Poisha").replace("paise", "poisha")
        # Remove commas and "And" for a cleaner result
        taka_in_words = taka_in_words.replace(",", "").replace(" And", "")

        return taka_in_words.title()
