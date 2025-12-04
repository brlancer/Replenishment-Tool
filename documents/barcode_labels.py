import os
import sys
from pyairtable import Api
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import config
import json


def fetch_purchase_orders_for_barcode_labels():
    """Fetch purchase orders from Airtable that are marked for barcode label generation."""
    
    # Initialize Airtable API client
    api = Api(config.AIRTABLE_API_KEY)
    
    # Initialize Airtable tables
    purchase_orders_table = api.table(config.AIRTABLE_PRODUCTION_DEV_BASE_ID, "Purchase Orders")
    line_items_table = api.table(config.AIRTABLE_PRODUCTION_DEV_BASE_ID, "Line Items")
    
    # Fetch purchase orders with "Generate barcode labels" field set to True
    purchase_orders = purchase_orders_table.all(
        formula="{Generate barcode labels}",
        fields=["PO #"]
    )

    # If no purchase orders are found, return early
    if not purchase_orders:
        print("No purchase orders selected for barcode label generation.")
        return []

    # Fetch line items for each purchase order
    for po_record in purchase_orders:
        po_number = po_record['fields']['PO #']
        print(f"Fetching line items for purchase order number: {po_number}...")
        line_items = line_items_table.all(
            formula=f"{{PO #}} = '{po_number}'",
            fields=['Position', 'Line Item Name', 'sku', 'Quantity Ordered', 'Option1 Value', 'Barcode']
        )
        # Sort line items by 'Position'
        line_items.sort(key=lambda item: item['fields'].get('Position', 0))
        print(f"Fetched {len(line_items)} line items for purchase order number: {po_number}.")
        po_record['line_items'] = line_items

    # Print the contents of the first purchase order for debugging purposes
    if purchase_orders:
        print(json.dumps(purchase_orders[0], indent=2))

    return purchase_orders


def validate_and_format_barcode(barcode_value):
    """
    Validate and format a barcode value to EAN13 format (13 digits).
    
    Args:
        barcode_value: The barcode value to validate (can be string, int, or list)
    
    Returns:
        str: A 13-digit string suitable for EAN13, or None if invalid
    """
    # Handle list values (Airtable often returns lists)
    if isinstance(barcode_value, list):
        if len(barcode_value) > 0:
            barcode_value = barcode_value[0]
        else:
            return None
    
    # Convert to string and remove any whitespace
    barcode_str = str(barcode_value).strip()
    
    # Remove any non-digit characters
    barcode_digits = ''.join(filter(str.isdigit, barcode_str))
    
    # Validate we have digits
    if not barcode_digits:
        return None
    
    # Pad with leading zeros if less than 13 digits
    if len(barcode_digits) < 13:
        barcode_digits = barcode_digits.zfill(13)
    # Truncate if more than 13 digits (take rightmost 13)
    elif len(barcode_digits) > 13:
        barcode_digits = barcode_digits[-13:]
    
    return barcode_digits


def generate_barcode_labels(order):
    """Generate a PDF sheet of barcode labels for a purchase order."""
    filename = f"barcode_labels_{order['id']}.pdf"
    
    # Page setup: 8.5" x 11" letter size
    page_width, page_height = letter
    
    # Label specifications (all in inches, converted to points)
    label_width = 1.5 * inch
    label_height = 1.5 * inch
    corner_radius = 0.03125 * inch
    
    # Margins and spacing
    top_margin = 0.5 * inch
    bottom_margin = 0.5 * inch
    left_margin = 0.7812 * inch
    right_margin = 0.7812 * inch
    horizontal_spacing = 0.3125 * inch
    vertical_spacing = 0.2 * inch
    
    # Calculate positions based on pitch
    horizontal_pitch = 1.8125 * inch
    vertical_pitch = 1.7 * inch
    
    # Labels per sheet: 4 columns x 6 rows = 24 labels
    labels_per_row = 4
    labels_per_column = 6
    labels_per_page = labels_per_row * labels_per_column
    
    # Create PDF
    c = canvas.Canvas(filename, pagesize=letter)
    
    po_number = order['fields']['PO #']
    line_items = order.get('line_items', [])
    
    if not line_items:
        print(f"Warning: No line items found for PO {po_number}")
        # Create empty page
        c.showPage()
        c.save()
        
        # Save to output directory
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        debug_filename = os.path.join(output_dir, filename)
        os.rename(filename, debug_filename)
        return debug_filename
    
    # Expand line items based on Quantity Ordered
    expanded_line_items = []
    total_labels = 0
    
    for item in line_items:
        # Extract quantity, with validation
        qty = item['fields'].get('Quantity Ordered', 1)
        
        # Handle non-integer quantities (cast to int)
        try:
            qty = int(qty) if qty is not None else 1
        except (ValueError, TypeError):
            qty = 1
        
        # Skip items with quantity 0 or negative
        if qty <= 0:
            continue
        
        # Add item to expanded list qty times
        expanded_line_items.extend([item] * qty)
        total_labels += qty
    
    # Warn if total labels exceeds 10,000
    if total_labels > 10000:
        print(f"Warning: Total labels ({total_labels}) exceeds 10,000. PDF generation may take longer.")
    
    # If no valid items after expansion, create empty page
    if not expanded_line_items:
        print(f"Warning: No line items with valid quantities found for PO {po_number}")
        c.showPage()
        c.save()
        
        # Save to output directory
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        debug_filename = os.path.join(output_dir, filename)
        os.rename(filename, debug_filename)
        return debug_filename
    
    # Process each expanded line item
    for item_index, item in enumerate(expanded_line_items):
        # Determine position on page
        label_on_page = item_index % labels_per_page
        
        # Start new page if needed
        if item_index > 0 and label_on_page == 0:
            c.showPage()
        
        # Calculate row and column for this label
        row = label_on_page // labels_per_row
        col = label_on_page % labels_per_row
        
        # Calculate x, y position (bottom-left corner of label)
        x = left_margin + col * horizontal_pitch
        y = page_height - top_margin - label_height - row * vertical_pitch

        # Draw a 1px black border around the label
        c.saveState()
        c.setLineWidth(1)  # 1pt = 1/72 inch, close to 1px for print
        c.setStrokeColorRGB(0, 0, 0)
        c.rect(x, y, label_width, label_height, stroke=1, fill=0)
        c.restoreState()

        # Extract field values
        fields = item['fields']
        sku = fields.get('sku', [''])[0] if isinstance(fields.get('sku', ['']), list) else fields.get('sku', '')
        line_item_name = fields.get('Line Item Name', [''])[0] if isinstance(fields.get('Line Item Name', ['']), list) else fields.get('Line Item Name', '')
        option1_value = fields.get('Option1 Value', [''])[0] if isinstance(fields.get('Option1 Value', ['']), list) else fields.get('Option1 Value', '')
        barcode_value = fields.get('Barcode', '')

        # Validate and format barcode
        barcode_formatted = validate_and_format_barcode(barcode_value)

        # Define text areas within the label
        text_margin = 0.05 * inch  # Small margin inside label
        text_x = x + text_margin
        text_width = label_width - 2 * text_margin
        
        # Top section: PO, SKU, PRODUCT (small font, left-aligned)
        c.setFont("Helvetica", 6)
        current_y = y + label_height - text_margin - 6  # Start from top
        
        # PO line
        c.drawString(text_x, current_y, f"PO: {po_number}")
        current_y -= 8
        
        # SKU line
        c.drawString(text_x, current_y, f"SKU: {sku}")
        current_y -= 8
        
        # PRODUCT line (with wrapping if needed)
        product_label = f"PRODUCT: {line_item_name}"
        # Simple wrapping: split at max characters per line
        max_chars = 30  # Approximate for 6pt font in 1.4" width
        if len(product_label) > max_chars:
            # Wrap text
            words = product_label.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if len(test_line) <= max_chars:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            for line in lines[:3]:  # Max 3 lines for product
                c.drawString(text_x, current_y, line)
                current_y -= 8
        else:
            c.drawString(text_x, current_y, product_label)
            current_y -= 8
        
        # Middle section: Option1 Value (large bold, centered)
        if option1_value:
            c.setFont("Helvetica-Bold", 18)
            option_text_width = c.stringWidth(option1_value, "Helvetica-Bold", 18)
            option_x = x + (label_width - option_text_width) / 2
            option_y = y + label_height * 0.4  # Middle of label
            c.drawString(option_x, option_y, option1_value)
        
        # Bottom section: EAN13 Barcode (centered, full width)
        if barcode_formatted:
            try:
                # Calculate barcode dimensions to fit in label
                barcode_display_width = label_width - 2 * text_margin
                barcode_display_height = 0.4 * inch
                
                # Create barcode widget with proper sizing
                barcode_widget = Ean13BarcodeWidget(
                    value=barcode_formatted,
                    barHeight=0.3 * inch,
                    barWidth=0.012 * inch,  # Width of individual bars
                    fontSize=6
                )
                
                # Get actual barcode dimensions
                barcode_actual_width = barcode_widget.width
                
                # Create drawing sized to actual barcode
                d = Drawing(barcode_actual_width, barcode_display_height)
                d.add(barcode_widget)
                
                # Calculate centered position on label
                barcode_canvas_x = x + (label_width - barcode_actual_width) / 2
                barcode_canvas_y = y + 0.05 * inch
                
                # Render barcode on canvas
                renderPDF.draw(d, c, barcode_canvas_x, barcode_canvas_y)
                
            except Exception as e:
                print(f"Error generating barcode for {barcode_formatted}: {e}")
                # Draw error text instead
                c.setFont("Helvetica", 6)
                error_text = f"Invalid: {barcode_value}"
                c.drawString(text_x, y + 0.1 * inch, error_text)
    
    # Finalize PDF
    c.showPage()
    c.save()
    
    # Save to output directory for debugging
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    debug_filename = os.path.join(output_dir, filename)
    os.rename(filename, debug_filename)
    print(f"Barcode labels saved to {debug_filename} for debugging purposes.")
    
    return debug_filename


def upload_barcode_labels(order, filename):
    """Upload barcode labels PDF to Airtable."""
    
    # Initialize Airtable API client
    api = Api(config.AIRTABLE_API_KEY)
    
    # Initialize Airtable table
    purchase_orders_table = api.table(config.AIRTABLE_PRODUCTION_DEV_BASE_ID, "Purchase Orders")
    
    # Remove any existing attachments in the 'Barcode labels' field and uncheck 'Generate barcode labels'
    purchase_orders_table.update(order['id'], {
        "Barcode labels": [],
        "Generate barcode labels": False
    })
    
    # Upload the barcode labels as an attachment to the purchase order record
    with open(filename, 'rb') as file:
        purchase_orders_table.upload_attachment(order['id'], 'Barcode labels', filename)
    
    print(f"Barcode labels uploaded to purchase order number: {order['fields']['PO #']}.")


def barcode_labels():
    """Main workflow: fetch purchase orders, generate barcode labels, and upload them."""
    orders = fetch_purchase_orders_for_barcode_labels()
    
    if not orders:
        print("No orders to process for barcode labels.")
        return
    
    for order in orders:
        try:
            filename = generate_barcode_labels(order)
            upload_barcode_labels(order, filename)
            # Clean up the file after upload
            if os.path.exists(filename):
                os.remove(filename)
            print(f"Successfully processed barcode labels for PO {order['fields']['PO #']}")
        except Exception as e:
            print(f"Error processing barcode labels for PO {order['fields'].get('PO #', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
