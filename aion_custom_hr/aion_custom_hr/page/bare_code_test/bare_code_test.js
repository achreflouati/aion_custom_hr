frappe.pages['bare-code-test'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Scanner Code-Barre Item',
        single_column: true
    });

    // Créer l'interface du scanner
    let scanner_html = `
        <div class="frappe-control" style="margin: 20px;">
            <div class="form-group">
                <label class="control-label">Code-Barre</label>
                <input type="text" class="form-control" id="barcode-input" 
                       placeholder="Scannez ou tapez le code-barre ici..." 
                       autofocus autocomplete="off">
            </div>
        </div>
        
        <div id="item-info" style="margin: 20px; display: none;">
            <div class="row">
                <div class="col-md-6">
                    <h4>Informations Item</h4>
                    <table class="table table-bordered">
                        <tr><td><strong>Code Item:</strong></td><td id="item-code"></td></tr>
                        <tr><td><strong>Nom Item:</strong></td><td id="item-name"></td></tr>
                        <tr><td><strong>Groupe:</strong></td><td id="item-group"></td></tr>
                        <tr><td><strong>Prix Standard:</strong></td><td id="standard-rate"></td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h4>Stock par Dépôt</h4>
                    <div id="warehouse-stock"></div>
                </div>
            </div>
        </div>
        
        <div id="error-message" style="margin: 20px; display: none;">
            <div class="alert alert-warning">
                <strong>Aucun item trouvé</strong> pour ce code-barre.
            </div>
        </div>
    `;

    $(page.body).html(scanner_html);

    // Variables globales
    let barcode_timeout;
    
    // Event listener pour le champ code-barre
    $('#barcode-input').on('input', function() {
        let barcode = $(this).val().trim();
        
        // Clear previous timeout
        if (barcode_timeout) {
            clearTimeout(barcode_timeout);
        }
        
        if (barcode.length > 2) {
            // Délai pour éviter les appels multiples
            barcode_timeout = setTimeout(() => {
                search_item_by_barcode(barcode);
            }, 300);
        } else {
            // Masquer les résultats si code trop court
            hide_results();
        }
    });

    // Event listener pour Enter
    $('#barcode-input').on('keypress', function(e) {
        if (e.which === 13) { // Enter key
            let barcode = $(this).val().trim();
            if (barcode) {
                search_item_by_barcode(barcode);
            }
        }
    });

    // Fonction de recherche
    function search_item_by_barcode(barcode) {
        // Afficher un loader
        show_loading();
        
        frappe.call({
            method: 'aion_custom_hr.aion_custom_hr.doctype.item_barecode_test.item_barecode_test.fetch_item_by_barcode',
            args: {
                barcode: barcode
            },
            callback: function(r) {
                hide_loading();
                
                if (r.message && r.message.success) {
                    show_item_info(r.message.data);
                    frappe.show_alert({
                        message: 'Item trouvé: ' + r.message.data.item_name,
                        indicator: 'green'
                    });
                } else {
                    show_error();
                    frappe.show_alert({
                        message: 'Aucun item trouvé pour ce code-barre',
                        indicator: 'orange'
                    });
                }
            },
            error: function() {
                hide_loading();
                show_error();
                frappe.show_alert({
                    message: 'Erreur lors de la recherche',
                    indicator: 'red'
                });
            }
        });
    }

    // Afficher les informations de l'item
    function show_item_info(data) {
        hide_error();
        
        $('#item-code').text(data.item_code || '');
        $('#item-name').text(data.item_name || '');
        $('#item-group').text(data.item_group || '');
        $('#standard-rate').text(data.standard_rate ? 
            format_currency(data.standard_rate) : '0.00');
        
        // Afficher le stock par dépôt
        let warehouse_html = '';
        if (data.warehouse_stock && data.warehouse_stock.length > 0) {
            warehouse_html = '<table class="table table-bordered table-sm">';
            warehouse_html += '<thead><tr><th>Dépôt</th><th>Qté Actuelle</th><th>Qté Réservée</th><th>Qté Disponible</th></tr></thead>';
            warehouse_html += '<tbody>';
            
            data.warehouse_stock.forEach(function(stock) {
                warehouse_html += '<tr>';
                warehouse_html += '<td>' + (stock.warehouse_name || stock.warehouse) + '</td>';
                warehouse_html += '<td>' + (stock.actual_qty || 0) + '</td>';
                warehouse_html += '<td>' + (stock.reserved_qty || 0) + '</td>';
                warehouse_html += '<td>' + (stock.available_qty || 0) + '</td>';
                warehouse_html += '</tr>';
            });
            
            warehouse_html += '</tbody></table>';
        } else {
            warehouse_html = '<div class="alert alert-info">Aucun stock trouvé</div>';
        }
        
        $('#warehouse-stock').html(warehouse_html);
        $('#item-info').show();
    }

    // Masquer les résultats
    function hide_results() {
        $('#item-info').hide();
        hide_error();
    }

    // Afficher erreur
    function show_error() {
        $('#item-info').hide();
        $('#error-message').show();
    }

    // Masquer erreur
    function hide_error() {
        $('#error-message').hide();
    }

    // Afficher loading
    function show_loading() {
        $('#barcode-input').attr('placeholder', 'Recherche en cours...');
    }

    // Masquer loading
    function hide_loading() {
        $('#barcode-input').attr('placeholder', 'Scannez ou tapez le code-barre ici...');
    }

    // Formater currency
    function format_currency(amount) {
        return parseFloat(amount).toFixed(2) + ' ' + (frappe.defaults.get_default('currency') || 'EUR');
    }

    // Auto-focus sur le champ barcode
    setTimeout(() => {
        $('#barcode-input').focus();
    }, 100);
};