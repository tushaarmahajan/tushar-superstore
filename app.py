from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from io import BytesIO
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from sqlalchemy import func, desc
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet
    from sqlalchemy.exc import OperationalError
except ImportError as e:
    raise ImportError("Required library 'reportlab' or 'sqlalchemy' is not installed. Please run 'pip install reportlab sqlalchemy'") from e

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # Use a secure key in production
db = SQLAlchemy(app)

# Models
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    is_draft = db.Column(db.Boolean, default=False)
    items = db.relationship('BillItem', backref='bill', lazy=True)

class BillItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    bill_id = db.Column(db.Integer, db.ForeignKey('bill.id'), nullable=False)
    product = db.relationship('Product')

# Helper function to serialize products
def serialize_products(products):
    return [{
        'id': p.id,
        'name': p.name,
        'price': float(p.price),
        'quantity': p.quantity,
        'category_id': p.category_id
    } for p in products]

# Routes
@app.route('/')
def index():
    products = Product.query.all()
    categories = Category.query.all()
    total_products = len(products)
    total_categories = len(categories)
    total_stock_value = sum(p.price * p.quantity for p in products)

    # Additional analysis
    total_bills = Bill.query.filter_by(is_draft=False).count()
    total_sales = sum(bill.total for bill in Bill.query.filter_by(is_draft=False).all()) if total_bills > 0 else 0.0
    avg_product_price = sum(p.price for p in products) / total_products if total_products > 0 else 0.0
    low_stock_items = [p for p in products if p.quantity < 5]
    low_stock_count = len(low_stock_items)

    return render_template('index.html', products=products, categories=categories,
                         total_products=total_products, total_categories=total_categories,
                         total_stock_value=total_stock_value, total_bills=total_bills,
                         total_sales=total_sales, avg_product_price=avg_product_price,
                         low_stock_count=low_stock_count, low_stock_items=low_stock_items)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        category_id = int(request.form['category_id'])
        
        product = Product(name=name, price=price, quantity=quantity, category_id=category_id)
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('index'))
    
    categories = Category.query.all()
    return render_template('add_product.html', categories=categories)

@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_category.html')

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.quantity = int(request.form['quantity'])
        product.category_id = int(request.form['category_id'])
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('index'))
    
    categories = Category.query.all()
    return render_template('edit_product.html', product=product, categories=categories)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    # Generate analytics data
    analytics_data = generate_analytics()
    return render_template('dashboard.html', **analytics_data)

@app.route('/api/sales_chart')
def sales_chart():
    # Sales over time
    bills = Bill.query.filter_by(is_draft=False).order_by(Bill.date).all()
    if not bills:
        return jsonify({'data': [], 'layout': {}})
    
    df = pd.DataFrame([{
        'date': bill.date.strftime('%Y-%m-%d'),
        'total': bill.total
    } for bill in bills])
    
    df['date'] = pd.to_datetime(df['date'])
    daily_sales = df.groupby('date')['total'].sum().reset_index()
    
    fig = px.line(daily_sales, x='date', y='total', 
                  title='Daily Sales Trend',
                  labels={'total': 'Sales Amount (₹)', 'date': 'Date'})
    fig.update_layout(template='plotly_white')
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)

@app.route('/api/category_chart')
def category_chart():
    # Sales by category
    category_sales = db.session.query(
        Category.name,
        func.sum(BillItem.quantity * BillItem.price).label('total_sales')
    ).join(Product).join(BillItem).join(Bill).filter(
        Bill.is_draft == False
    ).group_by(Category.name).all()
    
    if not category_sales:
        return jsonify({'data': [], 'layout': {}})
    
    categories = [item[0] for item in category_sales]
    sales = [float(item[1]) for item in category_sales]
    
    fig = px.pie(values=sales, names=categories, 
                 title='Sales Distribution by Category')
    fig.update_layout(template='plotly_white')
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)

@app.route('/api/top_products_chart')
def top_products_chart():
    # Top selling products
    top_products = db.session.query(
        Product.name,
        func.sum(BillItem.quantity).label('total_quantity'),
        func.sum(BillItem.quantity * BillItem.price).label('total_revenue')
    ).join(BillItem).join(Bill).filter(
        Bill.is_draft == False
    ).group_by(Product.name).order_by(
        desc('total_revenue')
    ).limit(10).all()
    
    if not top_products:
        return jsonify({'data': [], 'layout': {}})
    
    product_names = [item[0] for item in top_products]
    revenues = [float(item[2]) for item in top_products]
    
    fig = px.bar(x=product_names, y=revenues,
                 title='Top 10 Products by Revenue',
                 labels={'x': 'Product', 'y': 'Revenue (₹)'})
    fig.update_layout(template='plotly_white', xaxis_tickangle=-45)
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)

@app.route('/api/inventory_chart')
def inventory_chart():
    # Inventory levels
    products = Product.query.all()
    if not products:
        return jsonify({'data': [], 'layout': {}})
    
    product_names = [p.name for p in products]
    quantities = [p.quantity for p in products]
    
    # Color code based on stock levels
    colors_list = ['red' if q < 5 else 'orange' if q < 20 else 'green' for q in quantities]
    
    fig = px.bar(x=product_names, y=quantities,
                 title='Current Inventory Levels',
                 labels={'x': 'Product', 'y': 'Quantity in Stock'},
                 color=quantities,
                 color_continuous_scale=['red', 'orange', 'green'])
    fig.update_layout(template='plotly_white', xaxis_tickangle=-45)
    
    return json.dumps(fig, cls=PlotlyJSONEncoder)

@app.route('/api/dashboard_metrics')
def dashboard_metrics():
    """API endpoint to get all dashboard metrics as JSON for real-time updates"""
    analytics_data = generate_analytics()
    
    # Convert SQLAlchemy objects to dictionaries for JSON serialization
    recent_bills_data = []
    for bill in analytics_data['recent_bills']:
        recent_bills_data.append({
            'id': bill.id,
            'date': bill.date.isoformat(),
            'total': float(bill.total)
        })
    
    recent_products_data = []
    for product in analytics_data['recent_products']:
        recent_products_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'quantity': product.quantity
        })
    
    return jsonify({
        'total_products': analytics_data['total_products'],
        'total_categories': analytics_data['total_categories'],
        'total_bills': analytics_data['total_bills'],
        'total_draft_bills': analytics_data['total_draft_bills'],
        'total_revenue': float(analytics_data['total_revenue']),
        'avg_bill_value': float(analytics_data['avg_bill_value']),
        'total_stock_value': float(analytics_data['total_stock_value']),
        'low_stock_products': analytics_data['low_stock_products'],
        'out_of_stock_products': analytics_data['out_of_stock_products'],
        'recent_bills': recent_bills_data,
        'recent_products': recent_products_data,
        'today_sales': float(analytics_data['today_sales']),
        'week_sales': float(analytics_data['week_sales']),
        'month_sales': float(analytics_data['month_sales'])
    })

def generate_analytics():
    # Key metrics
    total_products = Product.query.count()
    total_categories = Category.query.count()
    total_bills = Bill.query.filter_by(is_draft=False).count()
    total_draft_bills = Bill.query.filter_by(is_draft=True).count()
    
    # Financial metrics
    total_revenue = db.session.query(func.sum(Bill.total)).filter(Bill.is_draft == False).scalar() or 0
    avg_bill_value = total_revenue / total_bills if total_bills > 0 else 0
    
    # Inventory metrics
    total_stock_value = db.session.query(func.sum(Product.price * Product.quantity)).scalar() or 0
    low_stock_products = Product.query.filter(Product.quantity < 5).count()
    out_of_stock_products = Product.query.filter(Product.quantity == 0).count()
    
    # Recent activity
    recent_bills = Bill.query.filter_by(is_draft=False).order_by(desc(Bill.date)).limit(5).all()
    recent_products = Product.query.order_by(desc(Product.created_at)).limit(5).all()
    
    # Time-based analytics
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    today_sales = db.session.query(func.sum(Bill.total)).filter(
        func.date(Bill.date) == today,
        Bill.is_draft == False
    ).scalar() or 0
    
    week_sales = db.session.query(func.sum(Bill.total)).filter(
        func.date(Bill.date) >= week_ago,
        Bill.is_draft == False
    ).scalar() or 0
    
    month_sales = db.session.query(func.sum(Bill.total)).filter(
        func.date(Bill.date) >= month_ago,
        Bill.is_draft == False
    ).scalar() or 0
    
    return {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_bills': total_bills,
        'total_draft_bills': total_draft_bills,
        'total_revenue': total_revenue,
        'avg_bill_value': avg_bill_value,
        'total_stock_value': total_stock_value,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'recent_bills': recent_bills,
        'recent_products': recent_products,
        'today_sales': today_sales,
        'week_sales': week_sales,
        'month_sales': month_sales
    }

@app.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    categories = Category.query.all()
    if request.method == 'POST':
        try:
            if 'preview' in request.form:
                product_ids = request.form.getlist('product_id[]')
                quantities = request.form.getlist('quantity[]')
                if not product_ids or not quantities:
                    flash('Please select at least one product!', 'error')
                    return redirect(url_for('create_bill'))
                
                total = 0.0
                items = []
                for pid, qty in zip(product_ids, quantities):
                    qty = int(qty) if qty else 0
                    if qty <= 0:
                        continue
                    product = Product.query.get_or_404(int(pid))
                    if product.quantity < qty:
                        flash(f'Insufficient stock for {product.name}!', 'error')
                        return redirect(url_for('create_bill'))
                    item_total = product.price * qty
                    total += item_total
                    items.append({'product': product, 'quantity': qty, 'total': item_total})

                return render_template('create_bill.html', products=serialize_products(Product.query.all()), categories=categories, preview=True, items=items, total=total)
            
            elif 'save_draft' in request.form:
                product_ids = request.form.getlist('product_id[]')
                quantities = request.form.getlist('quantity[]')
                
                if not product_ids and not quantities:
                    flash('No items to save as draft!', 'warning')
                    return redirect(url_for('create_bill'))
                
                bill = Bill(total=0.0, is_draft=True)
                db.session.add(bill)
                db.session.commit()
                
                total = 0.0
                items = []
                for pid, qty in zip(product_ids, quantities):
                    qty = int(qty) if qty and int(qty) > 0 else 0
                    if qty <= 0:
                        continue
                    product = Product.query.get_or_404(int(pid))
                    item_total = product.price * qty
                    total += item_total
                    bill_item = BillItem(product_id=product.id, quantity=qty, price=product.price, bill_id=bill.id)
                    items.append(bill_item)
                    db.session.add(bill_item)
                
                bill.total = total
                db.session.commit()
                flash('Bill saved as draft!', 'success')
                return redirect(url_for('index'))
            
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            
            if not product_ids or not quantities:
                flash('Please select at least one product!', 'error')
                return redirect(url_for('create_bill'))
            
            bill = Bill(total=0.0)
            db.session.add(bill)
            db.session.commit()
            
            total = 0.0
            items = []
            for pid, qty in zip(product_ids, quantities):
                qty = int(qty)
                if qty <= 0:
                    continue
                product = Product.query.get_or_404(int(pid))
                if product.quantity < qty:
                    flash(f'Insufficient stock for {product.name}!', 'error')
                    db.session.delete(bill)
                    db.session.commit()
                    return redirect(url_for('create_bill'))
                
                product.quantity -= qty
                item_total = product.price * qty
                total += item_total
                bill_item = BillItem(product_id=product.id, quantity=qty, price=product.price, bill_id=bill.id)
                items.append(bill_item)
                db.session.add(bill_item)
            
            bill.total = total
            db.session.commit()
            
            # Generate PDF bill
            pdf_buffer = generate_bill_pdf(bill, items)
            flash('Bill created successfully!', 'success')
            return send_file(pdf_buffer, as_attachment=True, download_name=f'bill_{bill.id}.pdf', mimetype='application/pdf')
        except OperationalError as e:
            db.session.rollback()
            flash(f'Database error: {str(e)}. Please check the data or contact support.', 'error')
            return redirect(url_for('create_bill'))
    
    products = serialize_products(Product.query.all())
    return render_template('create_bill.html', products=products, categories=categories)

def generate_bill_pdf(bill, items):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Add logo if available
    logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=100, height=100)
        elements.append(logo)
    else:
        flash('Logo file (logo.png) not found. Bill generated without logo.', 'warning')
    elements.append(Spacer(1, 12))

    # Title
    title = Paragraph("Tushar SuperStore", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Bill Info
    bill_info = f"Bill No: {bill.id}<br/>Date: {bill.date.strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(Paragraph(bill_info, styles['Normal']))
    elements.append(Spacer(1, 12))

    # Table Data
    table_data = [['Product', 'Quantity', 'Price (₹)', 'Total (₹)']]
    for item in items:
        row = [item.product.name, str(item.quantity), f"₹{item.price:.2f}", f"₹{item.quantity * item.price:.2f}"]
        table_data.append(row)
    table_data.append(['Total', '', '', f"₹{bill.total:.2f}"])

    # Table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Total Amount
    total_text = f"<b>Total Amount: ₹{bill.total:.2f}</b>"
    elements.append(Paragraph(total_text, styles['Heading2']))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# Create database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)