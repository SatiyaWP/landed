from odoo import models, fields, api
class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    partner_ids = fields.Many2many('res.partner', string="Vendor/Partner")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(LandedCost, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        View = self.env['ir.ui.view'].sudo()
        from lxml import etree
        if res.get('view_id'):
           view_id = res['view_id']
        if view_id:
           root_view = View.browse(view_id).read_combined(['arch'])
           res['arch'] = root_view['arch']
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//group/field[@name='date']"):
            partner = etree.Element('field', {'name': 'partner_ids'})
            node.addnext(partner)
            break
        res['arch'], res['fields'] = View.postprocess_and_fields(self._name, doc, view_id)
        return res
