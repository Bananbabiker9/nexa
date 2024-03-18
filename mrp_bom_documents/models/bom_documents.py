# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class BOMDocument(models.Model):
    _name = 'bom.document'


    name = fields.Char(string='Document Number', required=True, copy=False, help='You can give your'
                                                                                 'Document number.')
    description = fields.Text(string='Description', copy=False, help="Description")
    expiry_date = fields.Date(string='Expiry Date', copy=False, help="Date of expiry")
    bom_ref = fields.Many2one('mrp.bom', invisible=1, copy=False)
    doc_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_rel', 'doc_id', 'attach_id3', string="Attachment",
                                         help='You can attach the copy of your document', copy=False)

class BOM(models.Model):
    _inherit = 'mrp.bom'

    def _document_count(self):
        for each in self:
            document_ids = self.env['bom.document'].sudo().search([('bom_ref', '=', each.id)])
            each.document_count = len(document_ids)

    def document_view(self):
        self.ensure_one()
        domain = [
            ('bom_ref', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'bom.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
            'context': "{'default_bom_ref': %s}" % self.id
        }

    document_count = fields.Integer(compute='_document_count', string='# Documents')


class BOMAttachment(models.Model):
    _inherit = 'ir.attachment'

    doc_attach_rel = fields.Many2many('bom.document', 'doc_attachment_id', 'attach_id3', 'doc_id',
                                      string="Attachment", invisible=1)

