import os
import requests
from flask import send_from_directory
from reportlab.pdfgen import canvas
from flask import Response
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter
from flask import Flask, render_template, flash, redirect, url_for
from flask import send_file
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_login import LoginManager
from wtforms import PasswordField
import pandas as pd
from flask import send_file
from flask_mail import Mail, Message
from celery import Celery
from datetime import datetime, timedelta
from celery.schedules import crontab
from flask import render_template
from flask_mail import Message
from twilio.rest import Client
from flask import jsonify
from datetime import datetime, timedelta
from flask_migrate import Migrate




app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pos.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "supersecretkey"
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # ✅ Add this after initializing `db`



# Email Configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "ajkleinf@gmail.com"
app.config["MAIL_PASSWORD"] = "kftk iwwo nnlo owgl"
app.config["MAIL_DEFAULT_SENDER"] = "ajkleinf@gmail.com"

mail = Mail(app)

def generate_receipt(sale_id, product_name, quantity, total_price):
    receipt_dir = "receipts"
    if not os.path.exists(receipt_dir):
        os.makedirs(receipt_dir)

    receipt_path = f"{receipt_dir}/receipt_{sale_id}.pdf"

    # Create the PDF
    c = canvas.Canvas(receipt_path)

    # Add store logo (optional)
    logo_path = "static/logo.png"  # Store your logo in 'static/' folder
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, 50, 700, width=100, height=100)  # Adjust size & position

    # Add text to the receipt
    c.setFont("Helvetica", 16)
    c.drawString(100, 750, "Store Receipt")
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, f"Sale ID: {sale_id}")
    c.drawString(100, 710, f"Product: {product_name}")
    c.drawString(100, 690, f"Quantity: {quantity}")
    c.drawString(100, 670, f"Total Price: ${total_price:.2f}")
    c.drawString(100, 650, "Thank you for your purchase!")

    # Save the PDF
    c.save()

    return receipt_path  # Return the file path of the generated receipt

def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'], broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    return celery

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # 🔹 Redirect to login if unauthenticated

# Celery Configuration
app.config["broker_url"] = "redis://localhost:6379/0"
app.config["result_backend"] = "redis://localhost:6379/0"

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config["broker_url"], backend=app.config["result_backend"])
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)

TELEGRAM_BOT_TOKEN = "7994933931:AAHRzdRiDUa-DroW8JCGFy-gOmWr2lJfRRw"
TELEGRAM_CHAT_ID = "6587625714"

def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Telegram notification sent!")
        else:
            print(f"❌ Telegram Error: {response.text}")
    except Exception as e:
        print(f"❌ Failed to send Telegram notification: {e}")

def notify_low_stock():
    low_stock_products = Product.query.filter(Product.stock < 5).all()  # Change the threshold as needed

    if low_stock_products:
        message = "⚠️ Low Stock Alert!\n"
        for product in low_stock_products:
            message += f"🔻 {product.name} - Only {product.stock} left!\n"

        send_telegram_message(message)  # Call function to send message

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("✅ Telegram message sent successfully!")
    else:
        print("❌ Failed to send Telegram message:", response.text)

# Test sending a message
send_telegram_notification("🚀 POS System: Test message!")

@celery.task
def send_sales_report():
    sales = Sale.query.all()

    if not sales:
        return "No sales data to send."

    file_path = "sales_report.xlsx"
    data = {
        "Sale ID": [sale.id for sale in sales],
        "Product ID": [sale.product_id for sale in sales],
        "Quantity": [sale.quantity for sale in sales],
        "Total Price": [sale.total_price for sale in sales],
        "Timestamp": [sale.timestamp for sale in sales],
    }
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    # Send Email
    try:
        msg = Message("📊 Automated Sales Report", recipients=["owner@example.com"])
        msg.body = "Here is your scheduled sales report."
        with open(file_path, "rb") as report:
            msg.attach("sales_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", report.read())

        mail.send(msg)
        
        # ✅ Send WhatsApp & Telegram Notifications
        send_whatsapp_notification("📊 Your sales report has been sent via email!")
        send_telegram_message("📊 Your sales report has been sent via email!")

        return "Email & Notifications Sent!"
    except Exception as e:
        return f"❌ Email Failed: {str(e)}"

    
    # Twilio Credentials
TWILIO_SID = "AC9aeb3614cd22eade3ed864a6e7165ceb"
TWILIO_AUTH_TOKEN = "127efd0bbed3256a63510f0f2020e6d9"
TWILIO_WHATSAPP_NUMBER = "+14155238886"  # Twilio Sandbox Number
ADMIN_WHATSAPP_NUMBER = "+639993915274"  # Your actual WhatsApp number

def send_whatsapp_notification(message):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=ADMIN_WHATSAPP_NUMBER
        )
        print("✅ WhatsApp notification sent!")
    except Exception as e:
        print(f"❌ Failed to send WhatsApp notification: {e}")

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Schedule a daily report at 8:00 AM
    sender.add_periodic_task(crontab(hour=8, minute=0), send_sales_report.s())
    
    # Schedule a weekly report (every Monday at 9:00 AM)
    sender.add_periodic_task(crontab(day_of_week=1, hour=9, minute=0), send_sales_report.s())

@app.route("/receipts/<filename>")
@login_required
def get_receipt(filename):
    return send_from_directory("receipts", filename)

# Define Database Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

    # Product Form
class ProductForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired()])
    price = FloatField("Price", validators=[DataRequired()])
    stock = IntegerField("Stock", validators=[DataRequired()])
    submit = SubmitField("Add Product")

class SaleForm(FlaskForm):
    product_id = IntegerField("Product ID", validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    submit = SubmitField("Process Sale")

 

# Add User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # In production, use hashing!
    role = db.Column(db.String(20), nullable=False)  # "admin" or "cashier"


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    product = db.relationship("Product", backref=db.backref("sales", lazy=True))

class BackupSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    delivery_time = db.Column(db.String(50), nullable=False)  # e.g., "3 days"

class RestockRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"), nullable=False)
    quantity_requested = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="Pending")  # Pending, Shipped, Delivered
    estimated_delivery = db.Column(db.DateTime, nullable=True)  # ✅ Ensure this is included!

    product = db.relationship("Product", backref=db.backref("restock_requests", lazy=True))
    supplier = db.relationship("Supplier", backref=db.backref("restock_requests", lazy=True))



# Auto-restock function
from datetime import datetime, timedelta

def auto_request_restock(product):
    supplier = Supplier.query.order_by(Supplier.delivery_time).first()  # Choose fastest supplier
    
    if supplier:
        delivery_days = int(supplier.delivery_time.split()[0])  # Extract number of days
        estimated_delivery = datetime.utcnow() + timedelta(days=delivery_days)

        new_request = RestockRequest(
            product_id=product.id,
            supplier_id=supplier.id,
            quantity_requested=10,  # Request 10 units
            status="Shipped",
            estimated_delivery=estimated_delivery
        )
        db.session.add(new_request)
        db.session.commit()

        message = f"🚚 Restock Ordered!\nProduct: {product.name}\nSupplier: {supplier.name}\nETA: {estimated_delivery.strftime('%Y-%m-%d')}"
        send_telegram_message(message)  # Notify admin


def notify_low_stock():
    low_stock_products = Product.query.filter(Product.stock < 5).all()

    if low_stock_products:
        message = "⚠️ Low Stock Alert!\n"
        for product in low_stock_products:
            message += f"🔻 {product.name} - Only {product.stock} left!\n"
            auto_request_restock(product)  # 🔹 Automatically request restock

        send_telegram_message(message)

#Export Logistics PDF
@app.route("/export_logistics_pdf")
@login_required
def export_logistics_pdf():
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("logistics_dashboard"))

    restock_requests = RestockRequest.query.all()
    pdf_path = "logistics_report.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "🚚 Logistics Report")
    
    y_position = 720
    for request in restock_requests:
        request_text = f"Product: {request.product.name}, Supplier: {request.supplier.name}, Qty: {request.quantity_requested}, Status: {request.status}, ETA: {request.estimated_delivery.strftime('%Y-%m-%d') if request.estimated_delivery else 'Unknown'}"
        c.drawString(100, y_position, request_text)
        y_position -= 20

    c.save()
    return send_file(pdf_path, as_attachment=True)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # ✅ Correct for SQLAlchemy 2.0


# Login Form
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")




# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.password == form.password.data:  # In production, use password hashing!
            login_user(user)
            flash(f"Welcome, {user.username}! You are logged in as {user.role}.", "success")

            # Redirect Admins & Cashiers to Different Pages
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user.role == "cashier":
                return redirect(url_for("cashier_dashboard"))
        
        flash("Invalid credentials", "danger")
    return render_template("login.html", form=form)

@app.route("/admin_dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("cashier_dashboard"))


    form = ProductForm()

    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data,
            price=form.price.data,
            stock=form.stock.data
        )
        db.session.add(new_product)
        db.session.commit()
        flash("✅ Product added successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    products = Product.query.all()
    return render_template("admin_dashboard.html", form=form, products=products)


@app.route("/cashier_dashboard")
@login_required
def cashier_dashboard():
    if current_user.role != "cashier":
        flash("Access Denied!", "danger")
        return redirect(url_for("admin_dashboard"))

    products = Product.query.all()  # ✅ Fetch all products
    return render_template("cashier_dashboard.html", products=products)


# Logout Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

# Restrict Product Addition to Admins

@app.route("/", methods=["GET", "POST"])
def home():
    if not current_user.is_authenticated:  # Redirect if not logged in
        return redirect(url_for("login"))

    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif current_user.role == "cashier":
        return redirect(url_for("cashier_dashboard"))

    return redirect(url_for("login"))  # Fallback to login

#Product
@app.route("/process_sale", methods=["GET", "POST"])
@login_required
def process_sale():
    form = SaleForm()

    if form.validate_on_submit():
        product = Product.query.get(form.product_id.data)

        if product and product.stock >= form.quantity.data:
            total_price = product.price * form.quantity.data
            product.stock -= form.quantity.data  # Reduce stock
            
            new_sale = Sale(product_id=product.id, quantity=form.quantity.data, total_price=total_price)
            db.session.add(new_sale)
            db.session.commit()

            notify_low_stock()  # 🔹 Check stock and notify if low

            flash(f"Sale successful! Total: ${total_price:.2f}", "success")

            # ✅ Generate the receipt and store the file path
            receipt_path = generate_receipt(new_sale.id, product.name, form.quantity.data, total_price)

            # ✅ Redirect to the receipt page, passing the file path
            return redirect(url_for("view_receipt", sale_id=new_sale.id))

        else:
            flash("Invalid product ID or insufficient stock.", "danger")

    return render_template("process_sale.html", form=form)

@app.route("/view_receipt/<int:sale_id>")
@login_required
def view_receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    # ✅ Generate the receipt path
    receipt_path = f"/receipts/receipt_{sale.id}.pdf"

    return render_template("view_receipt.html", receipt_path=receipt_path)


@app.route("/sales_report")
@login_required
def sales_report():
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("cashier_dashboard"))

    sales = Sale.query.all()
    
    # Calculate Gross Revenue (Total Sales)
    gross_revenue = sum(sale.total_price for sale in sales)

    # Assuming product cost is 30% of sale price (change if needed)
    cost_percentage = 0.30  
    net_revenue = gross_revenue * (1 - cost_percentage)

    task_id = None  # 🔹 Placeholder: Replace with actual Celery task ID when implemented

    return render_template("sales_report.html", 
                           sales=sales, 
                           gross_revenue=gross_revenue, 
                           net_revenue=net_revenue,
                           task_id=task_id)

@app.route("/reset_sales", methods=["POST"])
@login_required
def reset_sales():
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("sales_report"))

    sales = Sale.query.all()

    if not sales:
        flash("No sales to reset.", "warning")
        return redirect(url_for("sales_report"))

    # Step 1: Export sales to an Excel file
    file_path = "sales_report.xlsx"
    data = {
        "Sale ID": [sale.id for sale in sales],
        "Product ID": [sale.product_id for sale in sales],
        "Quantity": [sale.quantity for sale in sales],
        "Total Price": [sale.total_price for sale in sales],
        "Timestamp": [sale.timestamp for sale in sales],
    }
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    # Step 2: Send email with the report attached
    try:
        msg = Message("📊 Sales Report Before Reset", recipients=["ajkleinf@gmail.com"])
        msg.body = "Attached is the sales report before resetting sales."
        
        with open(file_path, "rb") as report:
            msg.attach("sales_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", report.read())

        mail.send(msg)
        flash("Sales report sent via email before reset!", "success")

    except Exception as e:
        flash(f"Email failed: {str(e)}", "danger")

    # Step 3: Delete all sales after sending email
    try:
        Sale.query.delete()
        db.session.commit()
        flash("All sales records have been reset!", "success")
    except:
        db.session.rollback()
        flash("Error resetting sales.", "danger")

    return redirect(url_for("sales_report"))


@app.route("/undo_reset_sales", methods=["POST"])
@login_required
def undo_reset_sales():
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("sales_report"))

    try:
        # Restore sales from backup
        for backup in BackupSale.query.all():
            restored_sale = Sale(
                product_id=backup.product_id,
                quantity=backup.quantity,
                total_price=backup.total_price,
                timestamp=backup.timestamp
            )
            db.session.add(restored_sale)

        # Clear backup after restoration
        BackupSale.query.delete()
        db.session.commit()

        flash("Sales have been restored!", "success")
    except:
        db.session.rollback()
        flash("Error restoring sales.", "danger")

    return redirect(url_for("sales_report"))

@app.route("/export_sales_pdf")
@login_required
def export_sales_pdf():
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("sales_report"))

    sales = Sale.query.all()

    if not sales:
        flash("No sales to export.", "warning")
        return redirect(url_for("sales_report"))

    pdf_path = "sales_report.pdf"
    c = canvas.Canvas(pdf_path)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "Sales Report")

    c.setFont("Helvetica", 12)
    y = 780
    for sale in sales:
        y -= 20
        c.drawString(50, y, f"Sale ID: {sale.id}, Product ID: {sale.product_id}, Quantity: {sale.quantity}, Total: ${sale.total_price:.2f}")

    c.save()

    return send_file(pdf_path, as_attachment=True)

@app.route("/test_email")
def test_email():
    try:
        msg = Message("Test Email", recipients=["your_email@gmail.com"])
        msg.body = "This is a test email from your POS system."
        mail.send(msg)
        return "✅ Email Sent Successfully!"
    except Exception as e:
        return f"❌ Email failed: {str(e)}"
    
from flask import jsonify

@app.route("/task_status/<task_id>")
def task_status(task_id):
    task = celery.AsyncResult(task_id)
    return jsonify({"status": task.status})

@app.route("/delete_product/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash(f"Product '{product.name}' deleted successfully!", "success")
    else:
        flash("Product not found!", "danger")

    return redirect(url_for("home"))

@app.route("/logistics_dashboard")
@login_required
def logistics_dashboard():
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("home"))

    suppliers = Supplier.query.all()
    restock_requests = RestockRequest.query.all()

    return render_template("logistics_dashboard.html", suppliers=suppliers, restock_requests=restock_requests)



@app.route("/update_shipment_status/<int:request_id>", methods=["POST"])
@login_required
def update_shipment_status(request_id):
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("logistics_dashboard"))

    request = RestockRequest.query.get(request_id)
    if request:
        request.status = request.form["new_status"]
        db.session.commit()
        flash(f"✅ Shipment status updated to {request.status}", "success")

    return redirect(url_for("logistics_dashboard"))  # 🔹 Return here to avoid unreachable code



if __name__ == "__main__":
    print("Starting Flask application...")  # Debug message
    with app.app_context():
        db.create_all()  # Ensure database tables are created
    app.run(debug=True)