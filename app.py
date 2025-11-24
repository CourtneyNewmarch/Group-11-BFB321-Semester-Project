from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = '23456'

#Linking the database to the backend code
def get_database_connection():
    """Get database connection"""
    conn = sqlite3.connect('Medications.db')
    conn.row_factory = sqlite3.Row
    return conn

#Pharmacy's Dashboard 
@app.route('/Pharmacy')
def dashboard():
    conn = get_db_connection()
    
    # Get total products (sum of all products)
    total_products = conn.execute('SELECT count(medication_name) FROM medications').fetchone()[0] or 0

    # Get total items (sum of all batches)
    total_items = conn.execute('SELECT SUM(quantity) FROM batches').fetchone()[0] or 0
    
    # Get low stock count (products with quantity <= min_stock_level)
    low_stock_count = conn.execute( '''
        SELECT SUM(b.quantity), m.safety_stock_level
        FROM medication m
        INNER JOIN batches b 
        ON m.medication_id = b.medication_id
        GROUP BY m.medication_id
        WHERE SUM(b.quantity) <= m.safety_stock_level
        ''').fetchone()[0]
    
    conn.close()
    return render_template('Pharmacy.html', 
                         total_products=total_products,
                         total_items=total_items,
                         low_stock_count=low_stock_count,
                         )


#The inventory management table for the pharmacy page
@app.route('/Pharmacy')
def Pharmary_InventoryTable():
    conn = get_database_connection()

    products = conn.execute('''
        SELECT m.medication_id, m.medication_name, MIN(b.expiry_date), SUM(b.quantity), m.safety_stock_level, m.unit_price
        FROM medication m
        INNER JOIN batches b 
        ON m.medication_id = b.medication_id
        GROUP BY m.medication_id
        ORDER BY m.medication_id
    ''').fetchall()

    conn.close()
    return render_template('Pharmacy.html', products=products)


#The inventory availablity table for the medical staff page
@app.route('/MedicalStaff')
def MedicalStaff_InventoryTable():
    conn = get_database_connection()

    products1 = conn.execute('''
        SELECT m.medication_id, m.medication_name, MIN(b.expiry_date), SUM(b.quantity), m.safety_stock_level, m.unit_price
        FROM medication m
        INNER JOIN batches b 
        ON m.medication_id = b.medication_id
        GROUP BY m.medication_id
        ORDER BY m.medication_id
    ''').fetchall()

    conn.close()
    return render_template('MedicalStaff.html', products1=products1)

#The order management table for the pharmacy page 
app.route('/Pharmacy',  methods=['GET', 'POST']  )
def Pharmacy_OrderTable():
    conn = get_database_connection()
    orders = conn.execute('''
        SELECT c.order_id, c.full_name_and_surname, c.user_type, c.created_at, c.item_ordered
        FROM customers c
        ORDER BY c.created_at DESC
    ''').fetchall()
    conn.close()

    conn = get_database_connection
    if request.method == 'POST':
        try:
            status = request.form['status']
            conn.execute('''
                INSERT INTO customers (status)
                VALUES (?)
            ''', (status))
            conn.commit()
            conn.close()
            return redirect(url_for('view_inventory'))
        
    return render_template('Pharmacy.html', orders=orders)


#The order management table for the medical staff page
app.route('/MedicalStaff')
def MedicalStaff_OrderTable():
    conn = get_database_connection()

    orders1 = conn.execute('''
        SELECT c.order_id, c.created_at, c.item_ordered
        FROM customers c
        WHERE c.user_type = 'internal_user'
        ORDER BY c.order_id
    ''').fetchall()

    conn.close()
    return render_template('MedicalStaff.html', orders1=orders1)


#The order management table for the customer page
app.route('/Customers')
def Customer_OrderTable():
    conn = get_database_connection()

    orders2 = conn.execute('''
        SELECT c.order_id, c.created_at, c.item_ordered
        FROM customers c
        WHERE c.user_type = 'external_user'
        ORDER BY c.order_id
    ''').fetchall()

    conn.close()
    return render_template('Customers.html', orders2=orders2)

#The suppliers table for the pharmacy page 

#Add supplier
@app.route('/manage_suppliers', methods=['POST'])
def add_supplier():
    if request.method == 'POST':
        try:
            # Get form data
            supplier_name = request.form['supplierName']
            contact_person = request.form['contactPerson']
            email = request.form.get('email', '').strip()
            phone = request.form.get('phoneNumber', '').strip()
            address = request.form.get('address', '').strip()
            
            conn = get_db_connection()
            
            # Insert new supplier into the database
            conn.execute('''
                INSERT INTO suppliers (supplier_name, contact_person, email, phone, address)
                VALUES (?, ?, ?, ?, ?)
            ''', (supplier_name, contact_person, email, phone, address))
            
            conn.commit()
            conn.close()
            
            flash('Supplier added successfully!', 'success')
            return redirect(url_for('Pharmacy.html'))
             
    return render_template('manage_suppliers.html')


