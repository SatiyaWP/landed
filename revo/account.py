from odoo import models, fields, api
class AccountInvoice(models.Model): 
    _inherit = 'account.invoice'

    cost_id = fields.Many2one('stock.landed.cost', string="Landed Cost")

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountInvoice, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        View = self.env['ir.ui.view'].sudo()
        from lxml import etree
        if res.get('view_id'):
           view_id = res['view_id']
        if view_id:
           root_view = View.browse(view_id).read_combined(['arch'])
           res['arch'] = root_view['arch']
        doc = etree.XML(res['arch'])
        #Tambahan biar tidak error customer invoice
        if self.env.context.get('type') == 'in_invoice':
          for node in doc.xpath("//group/field[@name='currency_id']"):
            landed_cost = etree.Element('field', {'name': 'cost_id'})
            node.addnext(landed_cost)
            landed_cost.addnext(etree.Element('button', {'name': 'create_landed_cost', 'string': 'Create Landed Cost', 'type': 'object', 'attrs': "{'invisible': [('cost_id', '!=', False)]}"}))
            break
        res['arch'], res['fields'] = View.postprocess_and_fields(self._name, doc, view_id)
        return res

    @api.onchange('cost_id')
    def onchange_landed_cost(self):
        if self.cost_id:
           if self.cost_id.cost_lines:
              self.invoice_line_ids = ()
              invoice_lines = []
              for line in self.cost_id.cost_lines:
                  account_id = line.account_id
                  if not account_id:
                     args = {'type': self.type, 'product': line.product_id, 'fiscal': self.fiscal_position_id, 'company': self.company_id}
                     account_id = self.get_invoice_line_account(**args)
                  invoice_lines += [{'product_id': line.product_id.id, 'name': line.name, 'account_id': account_id.id, 'price_unit': line.price_unit, 'quantity': 1}]
              self.update({'invoice_line_ids': invoice_lines})

    @api.multi
    def create_landed_cost(self):
        env = self.sudo().env
        journal_id = env['account.journal'].search([('name', 'ilike', 'Landed Cost')], limit=1)
        cost_id = env['stock.landed.cost'].create({'date': self.date_invoice, 'account_journal_id': journal_id.id, 'partner_ids': self.partner_id})
        for line_id in self.invoice_line_ids:
            cost = line_id.price_unit
            if self.currency_id.id != self.env.user.company_id.currency_id.id:#.name != 'IDR':
               cost /= self.currency_id.rate
            env['stock.landed.cost.lines'].create({'product_id': line_id.product_id.id, 'name': line_id.name, 'account_id': line_id.account_id.id, 'price_unit': cost, 'split_method': 'by_current_cost_price', 'cost_id': cost_id.id})
        self.cost_id = cost_id
