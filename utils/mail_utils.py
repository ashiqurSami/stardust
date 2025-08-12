from odoo.api import Environment

def get_smtp_server_email(env: Environment):
    mail_server = env['ir.mail_server'].sudo().search([], order='sequence', limit=1)
    return mail_server.smtp_user

