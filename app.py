
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username, phone, email, password):
        self.id = username
        self.username = username
        self.phone = phone
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(username):
    with open("databases/member_detail.txt", "r") as file:
        for line in file:
            data = line.strip().split(',')
            if data[0] == username:
                return User(data[0], data[1], data[2], data[3])
    return None

@app.route('/')
def main():
    return render_template('main.html')

# Add these new routes
@app.route('/products')
@login_required
def products():
    return render_template('products.html')

@app.route('/sell')
@login_required
def sell():
    return render_template('sell.html')

@app.route('/messages')
@login_required
def messages():
    return render_template('messages.html')

@app.route('/account')
@login_required
def account():
    return render_template('account.html')

@app.route('/require_login')
def require_login():
    flash("Please login to access this feature")
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with open("databases/member_detail.txt", "r") as file:
            for line in file:
                data = line.strip().split(',')
                if (data[0] == username or data[2] == username) and check_password_hash(data[3], password):
                    user = User(data[0], data[1], data[2], data[3])
                    login_user(user)
                    return redirect(url_for('main'))
        
        flash("Invalid username or password.")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    #return redirect(url_for('login'))
    return render_template('main.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash("Passwords do not match!")
            return render_template('register.html')

        # Check if username or email already exists
        with open("databases/member_detail.txt", "r") as file:
            for line in file:
                data = line.strip().split(',')
                if data[0] == username:
                    flash("Username already exists!")
                    return render_template('register.html')
                if data[2] == email:
                    flash("Email already registered!")
                    return render_template('register.html')

        # Hash the password before storing
        hashed_password = generate_password_hash(password)
        
        with open("databases/member_detail.txt", "a") as file:
            file.write(f"{username},{phone},{email},{hashed_password}\n")
        
        flash("Registration successful! Please login.")
        return redirect(url_for('login'))
    
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)



'''
from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import json
from math import ceil

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('databases', exist_ok=True)

# Create product database file if it doesn't exist
if not os.path.exists('databases/products.json'):
    with open('databases/products.json', 'w') as f:
        json.dump([], f)

class User(UserMixin):
    def __init__(self, username, phone, email, password):
        self.id = username
        self.username = username
        self.phone = phone
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(username):
    with open("databases/member_detail.txt", "r") as file:
        for line in file:
            data = line.strip().split(',')
            if data[0] == username:
                return User(data[0], data[1], data[2], data[3])
    return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    """Generate a unique filename to prevent overwriting"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return f"{uuid.uuid4().hex}.{ext}"

# Load products from JSON file
def load_products():
    try:
        with open('databases/products.json', 'r') as f:
            return json.load(f)
    except:
        return []

# Save products to JSON file
def save_products(products):
    with open('databases/products.json', 'w') as f:
        json.dump(products, f, indent=4)

# Sample product categories
PRODUCT_CATEGORIES = {
    'smartphones': 'Smartphones',
    'laptops': 'Laptops',
    'tablets': 'Tablets',
    'cameras': 'Cameras',
    'audio': 'Audio',
    'accessories': 'Accessories',
    'other': 'Other'
}

# Main routes
@app.route('/')
def main():
    # Get featured products for homepage (4 most recent approved products)
    products = load_products()
    featured_products = [p for p in products if p.get('status') == 'approved']
    featured_products = sorted(featured_products, key=lambda p: p.get('created_at', ''), reverse=True)[:4]
    return render_template('main.html', featured_products=featured_products)

@app.route('/products')
def products():
    # Get filter parameters
    search_query = request.args.get('search', '').lower()
    category = request.args.get('category', '').lower()
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    conditions = request.args.getlist('condition')
    sort_by = request.args.get('sort_by', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 6  # Number of products per page
    
    # Load products
    all_products = load_products()
    
    # Filter only approved products
    filtered_products = [p for p in all_products if p.get('status') == 'approved']
    
    # Filter by search query
    if search_query:
        filtered_products = [p for p in filtered_products if search_query in p.get('title', '').lower() or 
                            search_query in p.get('description', '').lower() or 
                            search_query in p.get('brand', '').lower()]
    
    # Filter by category
    if category and category != 'all':
        filtered_products = [p for p in filtered_products if p.get('category', '').lower() == category]
    
    # Filter by price range
    if min_price:
        try:
            min_price_float = float(min_price)
            filtered_products = [p for p in filtered_products if float(p.get('price', 0)) >= min_price_float]
        except ValueError:
            pass
    
    if max_price:
        try:
            max_price_float = float(max_price)
            filtered_products = [p for p in filtered_products if float(p.get('price', 0)) <= max_price_float]
        except ValueError:
            pass
    
    # Filter by condition
    if conditions:
        filtered_products = [p for p in filtered_products if p.get('condition') in conditions]
    
    # Sort products
    if sort_by == 'price_low':
        filtered_products.sort(key=lambda p: float(p.get('price', 0)))
    elif sort_by == 'price_high':
        filtered_products.sort(key=lambda p: float(p.get('price', 0)), reverse=True)
    elif sort_by == 'popular':
        # For demo purposes, just sorting by title as a proxy for popularity
        filtered_products.sort(key=lambda p: p.get('title', ''))
    else:  # newest
        # Sort by created_at date (newest first)
        filtered_products.sort(key=lambda p: p.get('created_at', ''), reverse=True)
    
    # Pagination
    total_products = len(filtered_products)
    total_pages = ceil(total_products / per_page)
    
    # Ensure page is within valid range
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Get products for current page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_products = filtered_products[start_idx:end_idx]
    
    # Generate pagination range like [1, 2, 3, '...', 10]
    def generate_pagination_range(current_page, total_pages):
        if total_pages <= 5:
            return list(range(1, total_pages + 1))
        
        if current_page <= 3:
            return [1, 2, 3, 4, '...', total_pages]
        
        if current_page >= total_pages - 2:
            return [1, '...', total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
        
        return [1, '...', current_page - 1, current_page, current_page + 1, '...', total_pages]
    
    pagination_range = generate_pagination_range(page, total_pages) if total_pages > 1 else []
    
    return render_template(
        'products.html',
        products=paginated_products,
        categories=PRODUCT_CATEGORIES,
        selected_category=category,
        total_pages=total_pages,
        current_page=page,
        pagination_range=pagination_range,
        total_products=total_products
    )

@app.route('/product/<product_id>')
def product_detail(product_id):
    products = load_products()
    product = next((p for p in products if p.get('id') == product_id), None)
    
    if not product or product.get('status') != 'approved':
        flash('Product not found or not available yet.')
        return redirect(url_for('products'))
    
    # Get seller information
    seller = load_user(product.get('user_id'))
    
    # Get similar products (same category, exclude current product)
    similar_products = [p for p in products if p.get('category') == product.get('category') 
                       and p.get('id') != product_id and p.get('status') == 'approved'][:4]
    
    return render_template('product_detail.html', product=product, seller=seller, similar_products=similar_products)

@app.route('/sell')
@login_required
def sell():
    return render_template('sell.html', categories=PRODUCT_CATEGORIES)

@app.route('/submit_listing', methods=['POST'])
@login_required
def submit_listing():
    try:
        # Get form data
        category = request.form.get('category')
        title = request.form.get('title')
        brand = request.form.get('brand')
        model = request.form.get('model')
        year = request.form.get('year')
        condition = request.form.get('condition')
        description = request.form.get('description')
        included_items = request.form.getlist('included_items')
        price = request.form.get('price')
        original_price = request.form.get('original_price')
        negotiable = request.form.get('negotiable')
        shipping_method = request.form.get('shipping_method')
        shipping_cost = request.form.get('shipping_cost')
        shipping_paid_by = request.form.get('shipping_paid_by')
        
        # Process main photo
        main_photo_filename = None
        if 'main_photo' in request.files:
            main_photo = request.files['main_photo']
            if main_photo and allowed_file(main_photo.filename):
                filename = secure_filename(main_photo.filename)
                unique_filename = generate_unique_filename(filename)
                # Create directory if it doesn't exist
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                main_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                main_photo_filename = unique_filename
        
        # Process additional photos
        additional_photo_filenames = []
        if 'additional_photos' in request.files:
            # Handle multiple files
            additional_photos = request.files.getlist('additional_photos')
            for photo in additional_photos:
                if photo and allowed_file(photo.filename) and photo.filename:
                    filename = secure_filename(photo.filename)
                    unique_filename = generate_unique_filename(filename)
                    photo.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                    additional_photo_filenames.append(unique_filename)
        
        # Create a new listing
        new_listing = {
            'id': uuid.uuid4().hex,
            'user_id': current_user.id,
            'category': category,
            'title': title,
            'brand': brand,
            'model': model,
            'year': year,
            'condition': condition,
            'description': description,
            'included_items': included_items,
            'price': price,
            'original_price': original_price,
            'negotiable': negotiable == 'yes',
            'shipping_method': shipping_method,
            'shipping_cost': shipping_cost,
            'shipping_paid_by': shipping_paid_by,
            'main_photo': main_photo_filename,
            'additional_photos': additional_photo_filenames,
            'status': 'pending',  # Initial status is pending for admin approval
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save the listing to the product database
        products = load_products()
        products.append(new_listing)
        save_products(products)
        
        flash('Your item has been submitted for review! It will be listed after approval.', 'success')
        return redirect(url_for('account_listings'))
        
    except Exception as e:
        # Log the error and show a user-friendly message
        print(f"Error submitting listing: {str(e)}")
        flash('There was an error submitting your listing. Please try again.', 'error')
        return redirect(url_for('sell'))

@app.route('/messages')
@login_required
def messages():
    return render_template('messages.html')

@app.route('/account')
@login_required
def account():
    return render_template('account.html')

@app.route('/account/listings')
@login_required
def account_listings():
    # Load all products
    products = load_products()
    
    # Filter products for the current user
    user_listings = [p for p in products if p.get('user_id') == current_user.id]
    
    # Group by status
    pending_listings = [p for p in user_listings if p.get('status') == 'pending']
    active_listings = [p for p in user_listings if p.get('status') == 'approved']
    rejected_listings = [p for p in user_listings if p.get('status') == 'rejected']
    
    return render_template(
        'account_listings.html', 
        pending_listings=pending_listings,
        active_listings=active_listings,
        rejected_listings=rejected_listings
    )

@app.route('/require_login')
def require_login():
    flash("Please login to access this feature")
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with open("databases/member_detail.txt", "r") as file:
            for line in file:
                data = line.strip().split(',')
                if (data[0] == username or data[2] == username) and check_password_hash(data[3], password):
                    user = User(data[0], data[1], data[2], data[3])
                    login_user(user)
                    return redirect(url_for('main'))
        
        flash("Invalid username or password.")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash("Passwords do not match!")
            return render_template('register.html')

        # Check if username or email already exists
        with open("databases/member_detail.txt", "r") as file:
            for line in file:
                data = line.strip().split(',')
                if data[0] == username:
                    flash("Username already exists!")
                    return render_template('register.html')
                if data[2] == email:
                    flash("Email already registered!")
                    return render_template('register.html')

        # Hash the password before storing
        hashed_password = generate_password_hash(password)
        
        with open("databases/member_detail.txt", "a") as file:
            file.write(f"{username},{phone},{email},{hashed_password}\n")
        
        flash("Registration successful! Please login.")
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # For demo purposes, hardcoded admin credentials
        # In production, you'd use a more secure approach
        if username == 'admin' and password == 'admin123':
            user = User('admin', 'admin_phone', 'admin@secondlife.com', 'admin_password')
            user.is_admin = True
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        
        flash("Invalid admin credentials")
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Check if user is admin
    if not getattr(current_user, 'is_admin', False):
        flash("Unauthorized access")
        return redirect(url_for('main'))
    
    return render_template('admin_dashboard.html')

@app.route('/admin/listings')
@login_required
def admin_listings():
    # Check if user is admin
    if not getattr(current_user, 'is_admin', False):
        flash("Unauthorized access")
        return redirect(url_for('main'))
    
    # Load all products
    products = load_products()
    
    # Filter by status if provided
    status = request.args.get('status', 'pending')
    filtered_products = [p for p in products if p.get('status') == status]
    
    return render_template('admin_listings.html', products=filtered_products, status=status)

@app.route('/admin/listing/<product_id>', methods=['GET'])
@login_required
def admin_view_listing(product_id):
    # Check if user is admin
    if not getattr(current_user, 'is_admin', False):
        flash("Unauthorized access")
        return redirect(url_for('main'))
    
    # Load all products
    products = load_products()
    product = next((p for p in products if p.get('id') == product_id), None)
    
    if not product:
        flash('Product not found')
        return redirect(url_for('admin_listings'))
    
    return render_template('admin_view_listing.html', product=product)

@app.route('/admin/approve/<product_id>', methods=['POST'])
@login_required
def admin_approve_listing(product_id):
    # Check if user is admin
    if not getattr(current_user, 'is_admin', False):
        flash("Unauthorized access")
        return redirect(url_for('main'))
    
    # Load all products
    products = load_products()
    
    # Find and update the product
    for product in products:
        if product.get('id') == product_id:
            product['status'] = 'approved'
            product['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    
    # Save the updated products
    save_products(products)
    
    flash('Listing approved successfully!')
    return redirect(url_for('admin_listings', status='pending'))

@app.route('/admin/reject/<product_id>', methods=['POST'])
@login_required
def admin_reject_listing(product_id):
    # Check if user is admin
    if not getattr(current_user, 'is_admin', False):
        flash("Unauthorized access")
        return redirect(url_for('main'))
    
    reason = request.form.get('reason', 'Did not meet our listing guidelines')
    
    # Load all products
    products = load_products()
    
    # Find and update the product
    for product in products:
        if product.get('id') == product_id:
            product['status'] = 'rejected'
            product['rejection_reason'] = reason
            product['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    
    # Save the updated products
    save_products(products)
    
    flash('Listing rejected')
    return redirect(url_for('admin_listings', status='pending'))

if __name__ == '__main__':
    app.run(debug=True)
'''