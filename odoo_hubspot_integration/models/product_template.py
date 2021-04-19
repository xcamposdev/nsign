import logging

from odoo import fields, models, api
from datetime import datetime

_logger = logging.getLogger(__name__)


class ProductTemplate_HubSpot(models.Model):

    _inherit = "product.template"

    hubspot_line_item_id = fields.Char("HubSpot Line Item Id")
    hubspot_product_id = fields.Char("HubSpot Product Id")
    hubspot_product_imported = fields.Boolean(default=False, string="HubSpot es Importado")
    hubspot_crm_id = fields.Many2one('hubspot.crm', string="HubSpot Id")
    hubspot_write_date = fields.Datetime(string="HubSpot Fecha Modificación")

    def write(self, values):
        data = super(ProductTemplate_HubSpot, self).write(values)
        ################################################################
        self._cr.commit()
        try:
            if self.hubspot_product_id:
                self = data
                self.product_sincronize(data)
        except Exception as e:
            _logger.info("Error al exportar a hubspot {}".format(e))
        ################################################################
        return data


    def contact_sincronize(self):
        hubspot_operation = hubspot_crm.create_hubspot_operation('contact_company','import',hubspot_crm,'Procesando...')
        self._cr.commit()
        try:
            response_status, response_data = hubspot_crm.send_get_request_from_odoo_to_hubspot("GET",("objects/products/%s" % self.hubspot_product_id))

            if response_status:
                fecha_modificacion = company.get('properties').get('hs_lastmodifieddate')
                fecha_modificacion = hubspot_crm.convert_date_iso_format(fecha_modificacion)
                if fecha_modificacion < self.hubspot_write_date:
                    payload = {"properties":{
                        "name": product.name,
                        "hs_sku": product.default_code or "",
                        "description": product.description or "",
                        "hs_cost_of_goods_sold": product.standard_price or 0,
                        "price": product.price or 0,
                    }}
                    response_status, response_data = hubspot_crm.send_get_request_from_odoo_to_hubspot("PATCH",("objects/products/%s" % self.hubspot_contact_id), {}, payload)
                    self.write({
                        'hubspot_write_date': response_data.get('properties').get('hs_lastmodifieddate')
                    })
                    process_message = "Contacto Actualizado en HubSpot: {0}".format(contact_company.name)
                    
                hubspot_crm.create_hubspot_operation_detail('contact_company', 'import', False, response_data, hubspot_operation, False, process_message)
                self._cr.commit()
            else:
                process_message = "Error en la respuesta de importación de contacto Empresa {}".format(response_data)
                hubspot_crm.create_hubspot_operation_detail('contact_company','import','',response_data,hubspot_operation,True,process_message)

            hubspot_operation.write({'hubspot_message': "¡El proceso de importar contacto empresa se completó con éxito!"})
        except Exception as e:
            process_message="Error en la respuesta de importación de contacto empresa {}".format(e)
            _logger.info(process_message)
            hubspot_crm.create_hubspot_operation_detail('contact_company','import',response_data,process_message,hubspot_operation,True,process_message)
            hubspot_operation.write({'hubspot_message': "El proceso aún no está completo, ocurrio un Error! %s" % (e)})
        self._cr.commit()
        return contact_company


    def hubsport_to_odoo_import_product_single(self, hubspot_crm, hubspot_line_item_id):
        
        hubspot_operation = hubspot_crm.create_hubspot_operation('product','import',hubspot_crm,'Procesando...')
        self._cr.commit()
        try:
            parameters = {"limit":"50","archived":"false","properties":"hs_object_id,hs_product_id,name,quantity,price"}
            response_status, response_data = hubspot_crm.send_get_request_from_odoo_to_hubspot("GET",("objects/line_items/%s" % hubspot_line_item_id), parameters)
            if response_status:
                
                product_product = self.env['product.template'].search([('hubspot_product_id', '=', response_data.get('properties').get('hs_product_id',False))], limit=1)
                if not product_product:
                    product_product = self.env['product.template'].search([('hubspot_line_item_id', '=', response_data.get('id'))], limit=1)
                if not product_product:
                    product_product = self.env['product.template'].create({
                        'name': response_data.get('properties').get('name'),
                        'type':'product',
                        'hubspot_line_item_id': response_data.get('properties').get('hs_object_id'),
                        'hubspot_product_id': response_data.get('properties').get('hs_product_id'),
                        'hubspot_product_imported': True,
                        'hubspot_crm_id': hubspot_crm.id
                    })
                    process_message = "Producto Creado: {0}".format(product_product.name)
                else:
                    product_product.write({
                        'name': response_data.get('properties').get('name'),
                        'hubspot_line_item_id': response_data.get('properties').get('hs_object_id'),
                    })
                    process_message = "Product Actualizado: {0}".format(product_product.name)
                    
                hubspot_crm.create_hubspot_operation_detail('product', 'import', False, response_data, hubspot_operation, False, process_message)
                self._cr.commit()
            else:
                process_message = "Error en la respuesta de importación de producto {}".format(response_data)
                hubspot_crm.create_hubspot_operation_detail('product','import','',response_data,hubspot_operation,True,process_message)
            
            hubspot_operation.write({'hubspot_message': "¡El proceso de importar producto empresa se completó con éxito!"})
        except Exception as e:
            process_message="Error en la respuesta de importación de producto {}".format(e)
            _logger.info(process_message)
            hubspot_crm.create_hubspot_operation_detail('product','import',response_data,process_message,hubspot_operation,True,process_message)
            hubspot_operation.write({'hubspot_message': "El proceso aún no está completo, ocurrio un Error! %s" % (e)})
        self._cr.commit()
        return product_product
    
    
    def hubsport_to_odoo_import_product_all(self, hubspot_crm):
        hubspot_operation = hubspot_crm.create_hubspot_operation('product','import',hubspot_crm,'Procesando...')
        self._cr.commit()
        try:
            after = ''
            while True:
                if after:
                    parameters = {"limit":"50","archived":"false","after":after,"properties":"hs_object_id,name,hs_sku,description,hs_images,hs_url,price,recurringbillingfrequency,hs_cost_of_goods_sold"}
                else:
                    parameters = {"limit":"50","archived":"false","properties":"hs_object_id,name,hs_sku,description,hs_images,hs_url,price,recurringbillingfrequency,hs_cost_of_goods_sold"}

                response_status, response_data = hubspot_crm.send_get_request_from_odoo_to_hubspot("GET","objects/products", parameters)
                if response_status:
                    for res_data in response_data.get('results', []):
                        properties = res_data.get('properties')
                            
                        product_template = self.env['product.template'].search([('hubspot_product_id', '=', properties.get('hs_object_id'))], limit=1)
                        if not product_template:
                            product_template = self.env['product.template'].search([('default_code', '=', properties.get('hs_sku'))], limit=1)

                        if not product_template:
                            #hs_images,hs_url,recurringbillingfrequency,hs_lastmodifieddate"}

                            product_template = self.env['product.template'].create({
                                'name': properties.get('name'),
                                'description_sale': properties.get('description', False),
                                'default_code': properties.get('hs_sku', False),
                                'price': properties.get('price') and float(properties.get('price',0)),
                                'standard_price': properties.get('hs_cost_of_goods_sold') and float(properties.get('hs_cost_of_goods_sold',0)),
                                'type':'product',
                                'hubspot_line_item_id': False,
                                'hubspot_product_id': properties.get('hs_object_id'),
                                'hubspot_product_imported': True,
                                'hubspot_crm_id': hubspot_crm.id
                            })
                            process_message = "Producto Creado: {0}".format(product_template.name)
                        else:
                            fecha_modificacion = properties.get('hs_lastmodifieddate')
                            fecha_modificacion = hubspot_crm.convert_date_iso_format(fecha_modificacion)
                            if fecha_modificacion > product_template.write_date:
                                product_template.write({
                                    'name': properties.get('name'),
                                    'description_sale': properties.get('description', False),
                                    'default_code': properties.get('hs_sku', False),
                                    'price':  properties.get('price') and float(properties.get('price',0)),
                                    'standard_price': properties.get('hs_cost_of_goods_sold') and float(properties.get('hs_cost_of_goods_sold',0)),
                                    'hubspot_line_item_id': properties.get('hs_object_id'),
                                })
                                process_message = "Producto Actualizado: {0}".format(product_template.name)
                            else:
                                # response_status, response_data = hubspot_crm.send_get_request_from_odoo_to_hubspot("GET","objects/products", parameters)
                                # PATCH
                                process_message = "Producto no actualizado por fecha de modificación: {0}".format(product_template.name)
                            
                        hubspot_crm.create_hubspot_operation_detail('product', 'import', False, response_data, hubspot_operation, False, process_message)
                        self._cr.commit()
                    
                    if response_data.get('paging', False) and response_data.get('paging').get('next',False) and response_data.get('paging').get('next').get('after',False):
                        after = response_data.get('paging').get('next').get('after')
                    else:
                        break
                else:
                    process_message = "Error en la respuesta de importación de producto {}".format(response_data)
                    hubspot_crm.create_hubspot_operation_detail('product','import','',response_data,hubspot_operation,True,process_message)
                    break
            
            hubspot_operation.write({'hubspot_message': "¡El proceso de importar productos se completó con éxito!"})
        except Exception as e:
            process_message="Error en la respuesta de importación de producto {}".format(e)
            _logger.info(process_message)
            hubspot_crm.create_hubspot_operation_detail('product','import',response_data,process_message,hubspot_operation,True,process_message)
            hubspot_operation.write({'hubspot_message': "El proceso aún no está completo, ocurrio un Error! %s" % (e)})
        self._cr.commit()

    
    def hubsport_to_odoo_export_product_all(self, hubspot_crm):
        hubspot_operation = hubspot_crm.create_hubspot_operation('product','export',hubspot_crm,'Procesando...')
        self._cr.commit()
        try:
            products = self.env['product.template'].search([('hubspot_product_id','=',False),('hubspot_line_item_id','=',False)])
            if products:
                for product in products:
                    payload = {"properties":{
                        "name": product.name,
                        "hs_sku": product.default_code or "",
                        "description": product.description or "",
                        "hs_cost_of_goods_sold": product.standard_price or 0,
                        "price": product.price or 0,
                    }}
                    response_status, response_data = hubspot_crm.send_get_request_from_odoo_to_hubspot("POST","objects/products", {}, payload)
                    
                    if response_status:
                        product.write({
                            'hubspot_line_item_id': False,
                            'hubspot_product_id': response_data.get('properties').get('hs_object_id'),
                            'hubspot_crm_id': hubspot_crm.id
                        })
                        process_message = "Producto Creado: {0}".format(product.name)
                        hubspot_crm.create_hubspot_operation_detail('product', 'export', False, response_data, hubspot_operation, False, process_message)
                        self._cr.commit()
                    else:
                        process_message = "Error en la respuesta de exportación de producto {}".format(response_data)
                        hubspot_crm.create_hubspot_operation_detail('product','export','',response_data,hubspot_operation,True,process_message)
                
                hubspot_operation.write({'hubspot_message': "¡El proceso de exportar productos se completó con éxito!"})
        except Exception as e:
            process_message="Error en la respuesta de exportación de producto {}".format(e)
            _logger.info(process_message)
            hubspot_crm.create_hubspot_operation_detail('product','export',response_data,process_message,hubspot_operation,True,process_message)
            hubspot_operation.write({'hubspot_message': "El proceso aún no está completo, ocurrio un Error! %s" % (e)})
        self._cr.commit()