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


#create order database for customers
con = sqlite3.connect("orders.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    items TEXT NOT NULL,
    delivery_address TEXT NOT NULL,
    prescription_required TEXT,
    special_instructions TEXT,
    delivery_date TEXT,
    delivery_time TEXT,
    payment_method TEXT
)
""")

con.commit()
con.close()

#move the orders to the db
def save_order_to_db(data):
    con = sqlite3.connect("orders.db")
    con.row_factory= sqlite3.Row                                
    cur = con.cursor()

    cur.execute("""
        INSERT INTO orders (
            customer_name, items, delivery_address,
            prescription_required, special_instructions,
            delivery_date, delivery_time, payment_method
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['customer_name'],
        data['items'],
        data['delivery_address'],
        data['prescription_required'],
        data['special_instructions'],
        data['delivery_date'],
        data['delivery_time'],
        data['payment_method']
    ))

    con.commit()
    con.close()

# add the order
@app.route('/Customers', methods=['GET', 'POST'])
def place_order():
    form= OrderForm()

    if form.validate_on_submit():
        # Prepare order data as a dictionary
        order_data = {
            'customer_name': form.customer_name.data,
            'items': form.items.data,
            'delivery_address': form.delivery_address.data,
            'prescription_required': form.prescription_required.data,
            'special_instructions': form.special_instructions.data,
            'delivery_date': str(form.delivery_date.data),
            'delivery_time': form.delivery_time.data,
            'payment_method': form.payment_method.data
        }

        # Save to SQLite
        save_order_to_db(order_data)

        
        return redirect(url_for('order_success'))

    return render_template('place_order1.html', form=form)


# Add Item functionality
@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        try:
            # Get form data
            product_id = request.form['productID']
            product_name = request.form['productName']
            batch_id = request.form['batchID']
            quantity = int(request.form['quantity'])
            expiry_date = request.form['expiryDate']
            
            conn = get_database_connection()
            
            # Check if medication exists, if not create it
            medication = conn.execute(
                'SELECT * FROM medications WHERE medication_id = ?', (product_id,)
            ).fetchone()
            
            if not medication:
                # Create new medication with default safety stock level
                conn.execute('''
                    INSERT INTO medications (medication_id, medication_name, safety_stock_level, unit_price, supplier_id)
                    VALUES (?, ?, 10, 0.0, 1)
                ''', (product_id, product_name))
                flash(f'New medication {product_name} created with ID {product_id}', 'info')
            
            # Add batch
            conn.execute('''
                INSERT INTO batches (batch_id, quantity, expiry_date, medication_id)
                VALUES (?, ?, ?, ?)
            ''', (batch_id, quantity, expiry_date, product_id))
            
            # Record stock update
            conn.execute('''
                INSERT INTO stock_updates (medication_id, supplier_id, batch_id, username, 
                                         update_type, quantity_change, old_quantity, new_quantity, reason)
                VALUES (?, 1, ?, 'system', 'add', ?, 0, ?, 'restock')
            ''', (product_id, batch_id, quantity, quantity))
            
            conn.commit()
            conn.close()
            
            flash(f'Item {product_name} (Batch {batch_id}) added successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except sqlite3.IntegrityError:
            flash('Error: Batch ID already exists or invalid medication ID', 'error')
        except Exception as e:
            flash(f'Error adding item: {str(e)}', 'error')
    
    return render_template('add_item.html')

# Remove Item functionality
@app.route('/remove_item', methods=['GET', 'POST'])
def remove_item():
    if request.method == 'POST':
        try:
            # Get form data
            product_id = request.form['productID']
            product_name = request.form['productName']
            batch_id = request.form['batchID']
            quantity_to_remove = int(request.form['quantity'])
            reason = request.form.get('reason', 'other')
            
            conn = get_database_connection()
            
            # Check if batch exists and has sufficient quantity
            batch = conn.execute('''
                SELECT quantity FROM batches 
                WHERE batch_id = ? AND medication_id = ?
            ''', (batch_id, product_id)).fetchone()
            
            if not batch:
                flash('Error: Batch not found for the specified product', 'error')
                return redirect(url_for('remove_item'))
            
            current_quantity = batch['quantity']
            
            if current_quantity < quantity_to_remove:
                flash(f'Error: Only {current_quantity} items available in batch {batch_id}', 'error')
                return redirect(url_for('remove_item'))
            
            # Update batch quantity
            new_quantity = current_quantity - quantity_to_remove
            
            if new_quantity == 0:
                # Remove batch if quantity becomes zero
                conn.execute('DELETE FROM batches WHERE batch_id = ?', (batch_id,))
            else:
                # Update batch quantity
                conn.execute('''
                    UPDATE batches SET quantity = ? WHERE batch_id = ?
                ''', (new_quantity, batch_id))
            
            # Record stock update
            conn.execute('''
                INSERT INTO stock_updates (medication_id, supplier_id, batch_id, username, 
                                         update_type, quantity_change, old_quantity, new_quantity, reason)
                VALUES (?, 1, ?, 'system', 'remove', ?, ?, ?, ?)
            ''', (product_id, batch_id, quantity_to_remove, current_quantity, new_quantity, reason))
            
            conn.commit()
            conn.close()
            
            flash(f'Successfully removed {quantity_to_remove} items from {product_name} (Batch {batch_id})', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error removing item: {str(e)}', 'error')
    
    return render_template('remove_item.html')

# Edit Safety Stock functionality
@app.route('/edit_item', methods=['GET', 'POST'])
def edit_item():
    if request.method == 'POST':
        try:
            # Get form data
            product_id = request.form['ProductID']
            product_name = request.form['productName']
            new_safety_stock = int(request.form['editSafetyStock'])
            
            conn = get_database_connection()
            
            # Check if medication exists
            medication = conn.execute(
                'SELECT * FROM medications WHERE medication_id = ?', (product_id,)
            ).fetchone()
            
            if not medication:
                flash('Error: Medication not found', 'error')
                return redirect(url_for('edit_item'))
            
            # Get current safety stock level
            current_safety_stock = conn.execute(
                'SELECT safety_stock_level FROM medications WHERE medication_id = ?', (product_id,)
            ).fetchone()[0]
            
            # Update safety stock level
            conn.execute('''
                UPDATE medications 
                SET safety_stock_level = ?, medication_name = ?
                WHERE medication_id = ?
            ''', (new_safety_stock, product_name, product_id))
            
            # Record stock update for tracking changes
            quantity_change = new_safety_stock - current_safety_stock
            conn.execute('''
                INSERT INTO stock_updates (medication_id, supplier_id, batch_id, username, 
                                         update_type, quantity_change, old_quantity, new_quantity, reason)
                VALUES (?, 1, NULL, 'system', 'set', ?, ?, ?, 'adjustment')
            ''', (product_id, quantity_change, current_safety_stock, new_safety_stock))
            
            conn.commit()
            conn.close()
            
            flash(f'Safety stock level for {product_name} updated to {new_safety_stock}', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error updating safety stock: {str(e)}', 'error')
    
    return render_template('edit_item.html')

# Helper function to get database connection (fixing the typo in your existing code)
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('Medications.db')
    conn.row_factory = sqlite3.Row
    return conn

# Also update your existing dashboard function to use the correct connection function
@app.route('/Pharmacy')
def dashboard():
    conn = get_db_connection()  # Fixed function name
    
    # Get total products (sum of all products)
    total_products = conn.execute('SELECT count(medication_name) FROM medications').fetchone()[0] or 0

    # Get total items (sum of all batches)
    total_items = conn.execute('SELECT SUM(quantity) FROM batches').fetchone()[0] or 0
    
    # Get low stock count (products with quantity <= min_stock_level)
    low_stock_count = conn.execute(''' 
        SELECT COUNT(*) 
        FROM medications m
        WHERE (
            SELECT COALESCE(SUM(b.quantity), 0) 
            FROM batches b 
            WHERE b.medication_id = m.medication_id
        ) <= m.safety_stock_level
    ''').fetchone()[0] or 0
    
    # Get products for inventory table
    products = conn.execute('''
        SELECT m.medication_id, m.medication_name, MIN(b.expiry_date) as earliest_expiry, 
               SUM(b.quantity) as total_quantity, m.safety_stock_level, m.unit_price
        FROM medications m
        LEFT JOIN batches b ON m.medication_id = b.medication_id
        GROUP BY m.medication_id
        ORDER BY m.medication_id
    ''').fetchall()
    
    # Get orders for order table
    orders = conn.execute('''
        SELECT order_id, full_name_and_surname, user_type, created_at, item_ordered
        FROM customers 
        ORDER BY created_at DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('Pharmacy.html', 
                         total_products=total_products,
                         total_items=total_items,
                         low_stock_count=low_stock_count,
                         products=products,
                         orders=orders)
