frappe.pages['wholesale-billing'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Wholesale Billing',
		single_column: true
	});

	$(wrapper).find('.layout-main-section').html(frappe.render_template('wholesale_billing', {}));

    // --- State & Variables ---
    let rowCount = 0;
    page.customer_field = null; // Store reference to customer field

    // --- DOM Elements ---
    const $tbody = $('#wb-item-body');
    const $subtotal = $('#wb-subtotal');
    const $taxTotal = $('#wb-tax-total');
    const $grandTotal = $('#wb-grand-total');

    // --- Core Functions ---
    function addRow() {
        rowCount++;
        // Notice we changed the first <td> to hold a wrapper div instead of a standard input
        const rowHTML = `
            <tr data-row-id="${rowCount}">
                <td class="wb-item-cell" style="padding-bottom: 0;"></td>
                <td><input type="number" class="wb-qty" value="1" min="1"></td>
                <td><input type="number" class="wb-rate" value="0"></td>
                <td><input type="number" class="wb-tax" value="0"></td>
                <td class="wb-row-total" style="font-weight: 500;">₹0.00</td>
                <td style="text-align: center;"><button class="wb-btn-remove" tabindex="-1">✕</button></td>
            </tr>
        `;
        const $row = $(rowHTML).appendTo($tbody);

        // Inject standard Frappe Link field for the Item
        const itemControl = frappe.ui.form.make_control({
            parent: $row.find('.wb-item-cell'),
            df: {
                fieldtype: 'Link',
                options: 'Item',
                fieldname: 'item_code_' + rowCount,
                placeholder: 'Search Item...',
                onchange: function() {
                    let itemCode = this.value;
                    if(itemCode) fetchItemDetails(itemCode, $row);
                }
            },
            render_input: true
        });
        
        // Remove standard frappe bottom margin to fit our tight table design
        $row.find('.frappe-control').css('margin-bottom', '0');
        
        // Store control in the row for easy access later when saving
        $row.data('itemControl', itemControl);
        
        // Focus the new field automatically
        setTimeout(() => itemControl.set_focus(), 100);
        
        calculateTotals();
    }

    function fetchItemDetails(itemCode, $row) {
        let customer = page.customer_field ? page.customer_field.get_value() : '';
        
        // Ping ERPNext's standard item details API
        frappe.call({
            method: 'erpnext.stock.get_item_details.get_item_details',
            args: {
                item_code: itemCode,
                company: frappe.defaults.get_default('company'),
                customer: customer,
                qty: 1
            },
            callback: function(r) {
                if(r.message) {
                    // Populate rate (prioritizes price lists, falls back to standard rate)
                    let rate = r.message.price_list_rate || r.message.standard_rate || 0;
                    $row.find('.wb-rate').val(rate);
                    
                    // Optional: If you want to auto-fetch tax, you'd pull it from r.message here
                    calculateTotals();
                }
            }
        });
    }

    function calculateTotals() {
        let subtotal = 0;
        let totalTax = 0;

        $tbody.find('tr').each(function() {
            const qty = parseFloat($(this).find('.wb-qty').val()) || 0;
            const rate = parseFloat($(this).find('.wb-rate').val()) || 0;
            const taxPerc = parseFloat($(this).find('.wb-tax').val()) || 0;

            const rowSubtotal = qty * rate;
            const rowTax = rowSubtotal * (taxPerc / 100);
            const rowTotal = rowSubtotal + rowTax;

            $(this).find('.wb-row-total').text('₹' + rowTotal.toFixed(2));

            subtotal += rowSubtotal;
            totalTax += rowTax;
        });

        $subtotal.text('₹' + subtotal.toFixed(2));
        $taxTotal.text('₹' + totalTax.toFixed(2));
        $grandTotal.text('₹' + (subtotal + totalTax).toFixed(2));
    }

    function clearBill() {
        if(confirm("Clear this bill?")) {
            if(page.customer_field) page.customer_field.set_value('');
            $('#wb-pay-type').val('Cash');
            $tbody.empty();
            addRow(); 
        }
    }

    // --- Setup Customer Field ---
    page.customer_field = frappe.ui.form.make_control({
        parent: $('#wb-customer').parent(),
        df: {
            fieldtype: 'Link',
            options: 'Customer',
            fieldname: 'customer',
            placeholder: 'Select Customer...',
            onchange: function() {
                // If customer changes, you might want to re-fetch item prices based on their price list
                console.log("Customer selected:", this.value);
            }
        },
        render_input: true
    });
    $('#wb-customer').hide(); // Hide raw input

    // --- Event Listeners ---
    $tbody.on('input', '.wb-qty, .wb-rate, .wb-tax', function() {
        calculateTotals();
    });

    $tbody.on('click', '.wb-btn-remove', function() {
        $(this).closest('tr').remove();
        if ($tbody.find('tr').length === 0) addRow();
        calculateTotals();
    });

    $('#wb-add-row').on('click', addRow);
    $('#wb-clear-btn').on('click', clearBill);

    $('#wb-save-btn').on('click', function() {
        frappe.msgprint("Ready to write the Python save logic next!");
    });

    // --- Keyboard Shortcuts ---
    frappe.ui.keys.add_shortcut({
        shortcut: 'f4',
        action: () => addRow(),
        description: 'Add new item row',
        page: page
    });

    frappe.ui.keys.add_shortcut({
        shortcut: 'ctrl+enter',
        action: () => $('#wb-save-btn').click(),
        description: 'Save & Print Bill',
        page: page
    });

    // --- Initialization ---
    addRow(); 
};
