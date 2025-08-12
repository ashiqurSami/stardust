from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo import http
from odoo.http import request
from odoo import _


class PurchasePortal(CustomerPortal):
    @http.route(['/my/purchase-orders', '/my/purchase-orders/page/<int:page>'], auth='user', website=True)
    def purchase_portal(self, page=1, sortby=None, search=None, search_in=None, **kw):
        """
        Render the read-only list view of purchase orders in the vendor portal.

        Provides pagination, sorting, and searching functionality for the vendor's assigned purchase orders.
        Vendors can only view their assigned purchase orders with state 'purchase' and cannot create, update, cancel, or delete them.
        The view allows filtering purchase orders by name or all fields and sorting by date or name.

        Args:
            page (int): Current page number for pagination. Default is 1.
            sortby (str): Sorting key ('date' or 'name'). Default is 'date'.
            search (str): Search query string.
            search_in (str): Field to search in ('all' or 'name'). Default is 'name'.
            **kw: Additional keyword arguments (not used).

        Returns:
            werkzeug.wrappers.Response: Rendered HTML view of the purchase order list page with sorting,
            searching, and pagination applied.
        """
        limit = 5
        searchbar_sortings = {
            'date': {'label': 'Newest', 'order': 'date_approve desc'},
            'name': {'label': 'Name', 'order': 'name'},
            'price': {'label': 'Price', 'order': 'amount_total'},
        }
        search_list = {
            'all': {'label': 'All', 'input': 'all', 'domain': []},
            'name': {'label': 'Name', 'input': 'name', 'domain': [('name', 'ilike', search)]},
        }
        sortby = sortby or 'date'
        search_in = search_in or 'name'
        order = searchbar_sortings[sortby]['order']

        # Restrict to purchase orders assigned to the current vendor with state 'purchase'
        vendor_id = request.env.user.partner_id.id
        search_domain = [('partner_id', '=', vendor_id), ('state', '=', 'purchase')]
        search_domain += search_list[search_in]['domain']

        purchase_count = request.env['purchase.order'].sudo().search_count(search_domain)
        pager = portal_pager(
            url="/my/purchase-orders",
            url_args={'sortby': sortby, 'search_in': search_in, 'search': search},
            total=purchase_count,
            page=page,
            step=limit
        )
        purchase_orders = request.env['purchase.order'].sudo().search(
            search_domain, order=order, limit=limit, offset=pager['offset']
        )

        return request.render(
            'stardust.portal_purchase_order_tree_view',
            {
                'purchase_orders': purchase_orders,
                'page_name': 'purchase_list',
                'pager': pager,
                'searchbar_sortings': searchbar_sortings,
                'searchbar_inputs': search_list,
                'sortby': sortby,
                'search_in': search_in,
                'search': search,
                'default_url': '/my/purchases',
            }
        )

    @http.route(['/my/purchase-orders/<int:purchase_id>'], auth='user', website=True)
    def purchase_detail(self, purchase_id, **kw):
        """
        Render the read-only detailed view of a specific purchase order.

        Vendors can only view details of their assigned purchase orders with state 'purchase' or 'cancel'.
        No create, update, cancel, or delete actions are allowed.

        Args:
            purchase_id (int): ID of the purchase order to display.
            **kw: Additional keyword arguments (not used).

        Returns:
            werkzeug.wrappers.Response: Rendered HTML view of the purchase order details page.
        """
        purchase_order = request.env['purchase.order'].sudo().browse(purchase_id)

        # Verify the purchase order belongs to the current vendor and is in 'purchase' state
        if (purchase_order and purchase_order.partner_id.id == request.env.user.partner_id.id
                and purchase_order.state == 'purchase'):
            return request.render(
                'stardust.portal_purchase_order_detail',
                {
                    'purchase': purchase_order,
                    'page_name': 'purchase_detail',
                }
            )
        return request.not_found()
