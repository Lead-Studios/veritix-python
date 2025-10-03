from flask import Flask, request, send_file, jsonify
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
import qrcode
import io
from datetime import datetime
import json

app = Flask(__name__)

def generate_qr_code(data):
    """Generate QR code and return as image buffer"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer

def create_ticket_pdf(ticket_data):
    """Create a styled PDF ticket with QR code"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Colors
    primary_color = HexColor('#2563eb')
    secondary_color = HexColor('#64748b')
    text_color = HexColor('#1e293b')
    
    # Header background
    c.setFillColor(primary_color)
    c.rect(0, height - 2*inch, width, 2*inch, fill=1, stroke=0)
    
    # Title
    c.setFillColor(HexColor('#ffffff'))
    c.setFont("Helvetica-Bold", 32)
    c.drawString(1*inch, height - 1.2*inch, "EVENT TICKET")
    
    # Event Name
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(text_color)
    c.drawString(1*inch, height - 2.8*inch, ticket_data.get('event_name', 'N/A'))
    
    # Event Details Section
    y_position = height - 3.5*inch
    c.setFont("Helvetica", 12)
    c.setFillColor(secondary_color)
    
    details = [
        ("Date:", ticket_data.get('event_date', 'N/A')),
        ("Time:", ticket_data.get('event_time', 'N/A')),
        ("Venue:", ticket_data.get('venue', 'N/A')),
        ("Location:", ticket_data.get('location', 'N/A')),
    ]
    
    for label, value in details:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, y_position, label)
        c.setFont("Helvetica", 12)
        c.drawString(2*inch, y_position, value)
        y_position -= 0.3*inch
    
    # Buyer Information Section
    y_position -= 0.3*inch
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(text_color)
    c.drawString(1*inch, y_position, "Ticket Holder Information")
    
    y_position -= 0.4*inch
    c.setFont("Helvetica", 12)
    c.setFillColor(secondary_color)
    
    buyer_details = [
        ("Name:", ticket_data.get('buyer_name', 'N/A')),
        ("Email:", ticket_data.get('buyer_email', 'N/A')),
        ("Ticket ID:", ticket_data.get('ticket_id', 'N/A')),
        ("Ticket Type:", ticket_data.get('ticket_type', 'General')),
        ("Price:", f"${ticket_data.get('price', '0.00')}"),
    ]
    
    for label, value in buyer_details:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, y_position, label)
        c.setFont("Helvetica", 12)
        c.drawString(2*inch, y_position, value)
        y_position -= 0.3*inch
    
    # QR Code Section
    qr_data = json.dumps({
        'ticket_id': ticket_data.get('ticket_id', ''),
        'event_name': ticket_data.get('event_name', ''),
        'buyer_email': ticket_data.get('buyer_email', ''),
        'event_date': ticket_data.get('event_date', ''),
    })
    
    qr_buffer = generate_qr_code(qr_data)
    qr_image = ImageReader(qr_buffer)
    
    # Draw QR code on right side
    qr_size = 2.5*inch
    qr_x = width - qr_size - 1*inch
    qr_y = height - 5*inch
    
    c.drawImage(qr_image, qr_x, qr_y, qr_size, qr_size)
    
    # QR Code label
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(secondary_color)
    c.drawCentredString(qr_x + qr_size/2, qr_y - 0.3*inch, "Scan to verify")
    
    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(secondary_color)
    footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    c.drawCentredString(width/2, 0.5*inch, footer_text)
    c.drawCentredString(width/2, 0.3*inch, "Please present this ticket at the venue entrance")
    
    # Border
    c.setStrokeColor(primary_color)
    c.setLineWidth(2)
    c.rect(0.5*inch, 0.5*inch, width - 1*inch, height - 1*inch, fill=0, stroke=1)
    
    c.save()
    buffer.seek(0)
    return buffer

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """
    Generate PDF ticket from POST request
    
    Expected JSON format:
    {
        "event_name": "Summer Music Festival",
        "event_date": "2025-07-15",
        "event_time": "18:00",
        "venue": "Central Park Amphitheater",
        "location": "New York, NY",
        "buyer_name": "John Doe",
        "buyer_email": "john.doe@example.com",
        "ticket_id": "TKT-2025-001234",
        "ticket_type": "VIP",
        "price": "150.00"
    }
    """
    try:
        ticket_data = request.get_json()
        
        # Validate required fields
        required_fields = ['event_name', 'buyer_name', 'buyer_email', 'ticket_id']
        missing_fields = [field for field in required_fields if not ticket_data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Generate PDF
        pdf_buffer = create_ticket_pdf(ticket_data)
        
        # Return PDF file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"ticket_{ticket_data['ticket_id']}.pdf"
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'PDF Ticket Generator'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)