from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import traceback


app = Flask(__name__)
app.secret_key = '23456'



# Linking the database to the backend code
def get_database_connection():
    """Get database connection"""
    conn = sqlite3.connect('Medications.db')
    conn.row_factory = sqlite3.Row
    return conn

# Front Page Route (Fixes navbar home link)
@app.route('/')
def home():
    return render_template('Frontpage.html')



# (API endpoint) portal's Dashboard - Consolidated route for all pharmacy data
@app.route('/pharmacy', methods=['GET', 'POST'])
def pharmacy_dashboard():
    conn = get_database_connection()

    
    # Dashboard stats
    total_products = conn.execute('SELECT COUNT(*) FROM medications').fetchone()[0] or 0
    total_items = conn.execute('SELECT COALESCE(SUM(quantity), 0) FROM batches').fetchone()[0] or 0
    

    # Dashboard stats (Fixed low stock count query)
    low_stock_query = """
        SELECT COUNT(*)
        FROM (
            SELECT m.medication_id, COALESCE(SUM(b.quantity), 0) as total_qty, m.safety_stock_level
            FROM medications m
            LEFT JOIN batches b ON m.medication_id = b.medication_id
            GROUP BY m.medication_id
            HAVING total_qty <= m.safety_stock_level
        ) sub
    """
    low_stock_count = conn.execute(low_stock_query).fetchone()[0] or 0

    
    # Products for inventory table (Fixed query with LEFT JOIN)
    products_query = """
        SELECT 
            m.medication_id,
            m.medication_name,
            MIN(b.expiry_date) as expiry_date,
            COALESCE(SUM(b.quantity), 0) as quantity,
            m.safety_stock_level,
            m.unit_price
        FROM medications m
        LEFT JOIN batches b ON m.medication_id = b.medication_id
        GROUP BY m.medication_id, m.medication_name, m.safety_stock_level, m.unit_price
        ORDER BY m.medication_name
    """
    products = conn.execute(products_query).fetchall()
    

    # Orders for order management table 
    orders_query = """
        SELECT 
            c.order_id,
            c.full_name_and_surname,
            c.user_type,
            c.created_at,
            c.item_ordered,
            c.status
        FROM customers c
        WHERE c.order_id IS NOT NULL
        ORDER BY c.created_at DESC
    """
    orders = conn.execute(orders_query).fetchall()
    

    # Handle POST for order status update in order management table
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        status = request.form['status']
        if order_id:
            conn.execute(
                'UPDATE customers SET status = ? WHERE order_id = ?',
                (status, order_id)
            )
            conn.commit()
            flash('Order status updated successfully!', 'success')
        else:
            flash('Error: No order ID provided.', 'error')
        conn.close()
        return redirect(url_for('pharmacy_dashboard'))
    

    conn.close()
    return render_template('Pharmacy.html',
                           total_products=total_products,
                           total_items=total_items,
                           low_stock_count=low_stock_count,
                           products=products,
                           orders=orders)



# (API endpoint) Medical Staff Portal's Dashboard - inventory and orders table, and delivery stats
@app.route('/medicalstaff')
def medicalstaff_dashboard():
    conn = get_database_connection()
    

    products_query = """
        SELECT 
            m.medication_id,
            m.medication_name,
            MIN(b.expiry_date) as expiry_date,
            COALESCE(SUM(b.quantity), 0) as quantity,
            m.safety_stock_level,
            m.unit_price
        FROM medications m
        LEFT JOIN batches b ON m.medication_id = b.medication_id
        GROUP BY m.medication_id, m.medication_name, m.safety_stock_level, m.unit_price
        ORDER BY m.medication_name
    """
    products1 = conn.execute(products_query).fetchall()
    

    # Also fetch orders for medical staff (internal users)
    orders_query = """
        SELECT 
            c.order_id,
            c.created_at,
            c.item_ordered
        FROM customers c
        WHERE c.user_type = 'internal_user' AND c.order_id IS NOT NULL
        ORDER BY c.order_id
    """
    orders1 = conn.execute(orders_query).fetchall()

    # Dashboard stats
    total_pending = conn.execute('SELECT COUNT(*) FROM customers WHERE customers.status == "Pending" ').fetchone()[0] or 0
    total_delivered = conn.execute('SELECT COUNT(*) FROM customers WHERE customers.status == "Delivered" ').fetchone()[0] or 0
    
    conn.close()
    return render_template('MedicalStaff.html', products1=products1, orders1=orders1, total_pending=total_pending, total_delivered=total_delivered)



# Customer Portal's Dashboard - Orders Table
@app.route('/customers')
def customer_dashboard():
    conn = get_database_connection()
    
    orders_query = """
        SELECT 
            c.order_id,
            c.created_at,
            c.item_ordered
        FROM customers c
        WHERE c.user_type = 'external_user' AND c.order_id IS NOT NULL
        ORDER BY c.order_id
    """
    orders2 = conn.execute(orders_query).fetchall()
    
    conn.close()
    return render_template('Customers.html', orders2=orders2)



# Add Item functionality in Pharmacy Portal
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
            
            # Add batch to the batches table
            conn.execute('''
                INSERT INTO batches (batch_id, quantity, expiry_date, medication_id)
                VALUES (?, ?, ?, ?)
            ''', (batch_id, quantity, expiry_date, product_id))

            conn.commit()
            conn.close()

            conn = get_database_connection()
            # Record stock update
            conn.execute('''
                INSERT INTO stock_updates (medication_id, supplier_id, batch_id, username, 
                                         update_type, quantity_change, old_quantity, new_quantity, reason)
                VALUES (?, 1, ?, 'system', 'add', ?, 0, ?, 'restock')
            ''', (product_id, batch_id, quantity, quantity))
            
            conn.commit()
            conn.close()
            
            flash(f'Item {product_name} and Batch {batch_id} added successfully!', 'success')
            return redirect(url_for('pharmacy_dashboard'))
            
        except sqlite3.IntegrityError:
            flash('Error: Batch ID already exists or invalid medication ID', 'error')
        except Exception as e:
            flash(f'Error adding item: {str(e)}', 'error')
    
    return render_template('add_item.html')


# Remove Item functionality 
@app.route('/remove_item', methods=['GET', 'POST'])
def remove_item():
    if request.method == 'POST':
        conn = None
        try:
            product_id = request.form['productID'].strip()
            batch_id = request.form['batchID'].strip()
            quantity_to_remove = int(request.form['quantity'])
            reason = request.form.get('reason', 'other')
            
            conn = get_database_connection()
            
            # Check batch and update
            batch = conn.execute('''
                SELECT quantity FROM batches WHERE batch_id = ? AND medication_id = ?
            ''', (batch_id, product_id)).fetchone()
            
            if not batch:
                flash('Batch not found for this product ID', 'error')
                return redirect(url_for('remove_item'))
            
            current_quantity = batch['quantity']
            print(f"Current quantity: {current_quantity}")
            
            if current_quantity < quantity_to_remove:
                flash(f'Only {current_quantity} items available in this batch', 'error')
                return redirect(url_for('remove_item'))
            
            new_quantity = current_quantity - quantity_to_remove
            
            if new_quantity == 0:
                conn.execute('DELETE FROM batches WHERE batch_id = ? AND medication_id = ?', (batch_id, product_id))
                flash(f'Batch {batch_id} completely removed', 'info')
            else:
                conn.execute('UPDATE batches SET quantity = ? WHERE batch_id = ? AND medication_id = ?', 
                           (new_quantity, batch_id, product_id))
                flash(f'Batch {batch_id} updated to {new_quantity} items', 'info')
            
            # Log the removal in stock_updates table
            try:
                # Get supplier_id for the medication
                supplier = conn.execute(
                    'SELECT supplier_id FROM medications WHERE medication_id = ?', (product_id,)
                ).fetchone()
                
                if supplier:
                    # Get current total quantity for this medication
                    current_total = conn.execute(
                        'SELECT SUM(quantity) as total FROM batches WHERE medication_id = ?', (product_id,)
                    ).fetchone()
                    
                    old_total = (current_total['total'] or 0) + quantity_to_remove
                    new_total = old_total - quantity_to_remove
                    
                    conn.execute('''
                        INSERT INTO stock_updates (medication_id, supplier_id, batch_id, username, 
                                                update_type, quantity_change, old_quantity, new_quantity, reason)
                        VALUES (?, ?, ?, 'system', 'remove', ?, ?, ?, ?)
                    ''', (product_id, supplier['supplier_id'], batch_id, quantity_to_remove, 
                          old_total, new_total, reason))
            except Exception as e:
                print(f"Could not log stock update: {e}")
            
            conn.commit()
            flash('Items removed successfully', 'success')
            return redirect(url_for('pharmacy_dashboard'))
            
        except ValueError as e:
            flash(f'Invalid input: Please check that quantity is a valid number.', 'error')
        except Exception as e:
            flash(f'Error removing items: {str(e)}', 'error')
            print(f"Error details: {traceback.format_exc()}")
        finally:
            if conn:
                conn.close()
    
    return render_template('remove_item.html')

        
# Edit Safety Stock functionality in Pharmacy Portal
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
                SET safety_stock_level = ? 
                WHERE medication_id = ?
            ''', (new_safety_stock, product_id))

            conn.commit()
            conn.close()

            conn = get_database_connection()
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
            return redirect(url_for('pharmacy'))
            
        except Exception as e:
            flash(f'Error updating safety stock: {str(e)}', 'error')
    
    return render_template('edit_item.html')


# Add suppliers in Pharmacy Portal
@app.route('/manage_suppliers', methods=['GET', 'POST'])
def manage_suppliers():
    if request.method == 'POST':
        # Get form data
        supplier_name = request.form['supplierName']
        contact_person = request.form['contactPerson']
        email = request.form.get('email', '').strip()
        phone = request.form.get('phoneNumber', '').strip()
        address = request.form.get('address', '').strip()
         
        conn = get_database_connection()
         
        # Insert new supplier into the database
        conn.execute('''
            INSERT INTO suppliers (supplier_name, contact_person, email, phone, address)
            VALUES (?, ?, ?, ?, ?)
        ''', (supplier_name, contact_person, email, phone, address))
         
        conn.commit()
        conn.close()
         
        flash('Supplier added successfully!', 'success')
        return redirect(url_for('pharmacy_dashboard'))  
        
    # For GET, render the form (assuming manage_suppliers.html exists)
    return render_template('manage_suppliers.html')



# Viewing suppliers in Pharmacy Portal 
@app.route('/view_suppliers')
def view_suppliers():
    conn = get_database_connection()
    suppliers = conn.execute('SELECT * FROM suppliers').fetchall()
    conn.close()
    return render_template('view_suppliers.html', suppliers=suppliers)  



# add external customer orders
@app.route('/place_order1', methods=['GET', 'POST'])
def place_customer_order():

    if request.method == 'POST':
        # Get form data
        Customer_id = request.form['CustomerID']
        Customer_name = request.form['CustomerName']
        items = request.form['items']
        address = request.form['deliveryAddress']
         
        conn = get_database_connection()
         
        # Insert new order into the database
        conn.execute('''
            INSERT INTO customers (customer_id, full_name_and_surname, user_type, item_ordered, address )
            VALUES (?, ?, 'external_user', ?, ?)
        ''', (Customer_id, Customer_name, items, address))
         
        conn.commit()
        conn.close()
         
        flash('Order added successfully!', 'success')
        return redirect(url_for('customer_dashboard'))  
        
    return render_template('place_order1.html')



# add internal customer (medical staff) orders
@app.route('/place_order2', methods=['GET', 'POST'])
def place_medicalstaff_order():

    if request.method == 'POST':
        # Get form data
        Customer_id = request.form['MedicalStaffID']
        Customer_name = request.form['MedicalStaffName']
        items = request.form['items']
        address = request.form['deliveryAddress']
         
        conn = get_database_connection()
         
        # Insert new order into the database
        conn.execute('''
            INSERT INTO customers (customer_id, full_name_and_surname, user_type, item_ordered, address )
            VALUES (?, ?, 'internal_user', ?, ?)
        ''', (Customer_id, Customer_name, items, address))
         
        conn.commit()
        conn.close()
         
        flash('Order added successfully!', 'success')
        return redirect(url_for('medicalstaff_dashboard'))  
        
    return render_template('place_order2.html')



# Add prescriptions
@app.route('/add_prescriptions')
def add_prescriptions():
    return render_template('add_prescriptions.html')



# Add terms of services
@app.route('/terms_of_services')
def add_termsOfServices():
    return render_template('terms_of_serives.html')

# Add privacy policy
@app.route('/privacy_policy')
def add_privacyPolicy():
    return render_template('privacy_policy.html')



#Medical Staff Portal Login
@app.route('/medicalstafflogin',  methods=['GET', 'POST'])
def medicalstaff_login():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id', '').strip()  # Added .strip() for safety
        password = request.form['password']
        
        #print(f"Debug: Attempting login with customer_id='{customer_id}', password='{password}'")  # TEMP DEBUG
        
        conn = get_database_connection()
        user_query = """
            SELECT *
            FROM customers
            WHERE customer_id = ?
        """
        user = conn.execute(user_query, (customer_id,)).fetchone()
        conn.close()
        
        #print(f"Debug: User found? {user is not None}, Type: {user['user_type'] if user else None}")  # TEMP DEBUG
        
        if user and user['password'] == password:
            if user['user_type'] == 'internal_user':
                flash('Medical staff login successful!', 'success')
                return redirect(url_for('medicalstaff_dashboard'))
            else:
                flash('This account is for registered medical staff only,', 'warning')
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('medicalStaffLogin.html')


#Customer Portal login
@app.route('/customerlogin', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id', '').strip()  # Added .strip() for safety
        password = request.form['password']
        
        #print(f"Debug: Attempting login with customer_id='{customer_id}', password='{password}'")  # TEMP DEBUG
        
        conn = get_database_connection()
        user_query = """
            SELECT *
            FROM customers
            WHERE customer_id = ?
        """
        user = conn.execute(user_query, (customer_id,)).fetchone()
        conn.close()
        
        #print(f"Debug: User found? {user is not None}, Type: {user['user_type'] if user else None}")  # TEMP DEBUG
        
        if user and user['password'] == password:
            if user['user_type'] == 'external_user':
                flash('Customer login successful!', 'success')
                return redirect(url_for('customer_dashboard'))
            else:
                flash('This account is for registered customers only.', 'warning')
        else:
            flash('Invalid credentials.', 'danger')
    
    return render_template('customerLogin.html')


#Pharmacy staff Portal Login
@app.route('/pharmacylogin', methods=['GET', 'POST'])
def pharmacy_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()  # Added .strip() for safety
        password = request.form['password']
        
        conn = get_database_connection()
        user_query = """
            SELECT *
            FROM pharmacy_personnel
            WHERE username = ?
        """
        user = conn.execute(user_query, (username,)).fetchone()
        conn.close()
        
        if user and user['password'] == password:
            return redirect(url_for('pharmacy_dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    
    return render_template('pharmacyLogin.html')


# Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            role = request.form.get('role')
            full_name = request.form.get('full_name', '').strip()
            password = request.form.get('password')
            customer_id = request.form.get('customer_id', '').strip()
            username = request.form.get('username', '').strip()

            if not full_name or not password:
                flash('Full name and password are required.', 'error')
                return redirect(url_for('signup'))

            conn = get_database_connection()

            if role == 'customer':
                if not customer_id:
                    flash('Customer ID is required for customers.', 'error')
                    conn.close()
                    return redirect(url_for('signup'))

                # Check if customer already exists
                existing = conn.execute(
                    'SELECT customer_id FROM customers WHERE customer_id = ? AND user_type = "external_user"',
                    (customer_id,)
                ).fetchone()
                if existing:
                    flash('Customer ID already exists. Please login.', 'warning')
                    conn.close()
                    return redirect(url_for('customer_login'))

                # Insert new customer
                conn.execute('''
                    INSERT INTO customers (customer_id, full_name_and_surname, user_type, password)
                    VALUES (?, ?, 'external_user', ?)
                ''', (customer_id, full_name, password))
                flash('Customer account created successfully! You can now log in.', 'success')
                conn.commit()
                conn.close()
                return redirect(url_for('customer_login'))

            elif role == 'medical':
                if not customer_id:
                    flash('Medical Staff ID is required.', 'error')
                    conn.close()
                    return redirect(url_for('signup'))

                # Check if medical staff already exists
                existing = conn.execute(
                    'SELECT customer_id FROM customers WHERE customer_id = ? AND user_type = "internal_user"',
                    (customer_id,)
                ).fetchone()
                if existing:
                    flash('Medical Staff ID already exists. Please login.', 'warning')
                    conn.close()
                    return redirect(url_for('medicalstaff_login'))

                # Insert new medical staff
                conn.execute('''
                    INSERT INTO customers (customer_id, full_name_and_surname, user_type, password)
                    VALUES (?, ?, 'internal_user', ?)
                ''', (customer_id, full_name, password))
                flash('Medical Staff account created successfully! You can now log in.', 'success')
                conn.commit()
                conn.close()
                return redirect(url_for('medicalstaff_login'))

            elif role == 'pharmacy':
                if not username:
                    flash('Username is required for pharmacy personnel.', 'error')
                    conn.close()
                    return redirect(url_for('signup'))

                # Check if username already exists
                existing = conn.execute(
                    'SELECT username FROM pharmacy_personnel WHERE username = ?',
                    (username,)
                ).fetchone()
                if existing:
                    flash('Username already exists. Please login.', 'warning')
                    conn.close()
                    return redirect(url_for('pharmacy_login'))

                # Insert new pharmacy personnel
                conn.execute('''
                    INSERT INTO pharmacy_personnel (username, full_name_and_surname, password)
                    VALUES (?, ?, ?)
                ''', (username, full_name, password))
                flash('Pharmacy Personnel account created successfully! You can now log in.', 'success')
                conn.commit()
                conn.close()
                return redirect(url_for('pharmacy_login'))

            else:
                flash('Invalid role selected.', 'danger')
                conn.close()
                return redirect(url_for('signup'))

        except sqlite3.IntegrityError as e:
            flash('Database error: User may already exist or invalid data.', 'error')
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'error')
            if 'conn' in locals() and conn:
                conn.close()

    return render_template('signup.html')



if __name__ == "__main__":
    app.run(debug=False) 
