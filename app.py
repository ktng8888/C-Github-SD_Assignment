import random 
import os
import time
from abc import ABC, abstractmethod
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
    # Get featured products from products.txt
    featured_products = []
    try:
        with open("databases/products.txt", "r") as file:
            lines = file.readlines()
            # Get the 4 most recent products (highest IDs)
            sorted_lines = sorted(lines, key=lambda line: int(line.strip().split('||')[0]), reverse=True)
            count = 0
            
            for line in sorted_lines:
                if count >= 5:  # Limit to 4 featured products
                    break
                    
                parts = line.strip().split('||')
                if len(parts) >= 15:
                    # Calculate discount and original price for display purposes
                    # For demonstration, we'll set random discounts between 10-25%
                    import random
                    current_price = float(parts[9])
                    discount_percent = random.randint(10, 25)
                    original_price = round(current_price / (1 - discount_percent/100), 2)
                    
                    # Format the product data
                    product = {
                        'id': parts[0],
                        'seller': parts[1],
                        'category': parts[2],
                        'status': parts[3],
                        'title': parts[4],
                        'brand': parts[5],
                        'model': parts[6],
                        'year': parts[7],
                        'description': parts[8].strip('"'),
                        'price': parts[9],
                        'current_price': current_price,
                        'original_price': original_price,
                        'discount_percent': discount_percent,
                        'shipping_method': parts[10],
                        'main_photo': parts[13],
                        # Create a display badge based on discount or condition
                        'badge': f"{discount_percent}% OFF" if discount_percent > 15 else "Like New",
                        # Add a random rating
                        'rating': round(random.uniform(4.5, 5.0), 1),
                        'review_count': random.randint(10, 60),
                        # Add a random "posted time"
                        'posted_time': random.choice(["Posted 1 day ago", "Posted 2 days ago", "Posted 3 days ago", "Posted 1 week ago"])
                    }
                    
                    featured_products.append(product)
                    count += 1
    except FileNotFoundError:
        # If the file doesn't exist, we'll just show empty featured products
        pass
    
    return render_template('main.html', featured_products=featured_products)

@app.route('/products')
@login_required
def products():
    products = []
    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 15:
                    products.append({
                        'id': parts[0],
                        'seller': parts[1],
                        'category': parts[2],
                        'status': parts[3],
                        'title': parts[4],
                        'brand': parts[5],
                        'model': parts[6],
                        'year': parts[7],
                        'description': parts[8].strip('"'),
                        'price': parts[9],
                        'main_photo': parts[13]
                    })
    except FileNotFoundError:
        pass

    # Filter by category
    selected_category = request.args.get('category')
    if selected_category:
        products = [p for p in products if p['category'] == selected_category]

    # Search functionality
    search_query = request.args.get('search', '').lower()
    if search_query:
        products = [p for p in products 
                   if search_query in p['title'].lower() or 
                      search_query in p['description'].lower()]

    # Sorting functionality
    sort = request.args.get('sort', 'newest')
    if sort == 'newest':
        products.sort(key=lambda x: int(x['id']), reverse=True)
    elif sort == 'oldest':
        products.sort(key=lambda x: int(x['id']))
    elif sort == 'price_low':
        products.sort(key=lambda x: float(x['price']))
    elif sort == 'price_high':
        products.sort(key=lambda x: float(x['price']), reverse=True)

    return render_template('products.html', 
                         products=products,
                         selected_category=selected_category)

@app.route('/product/<product_id>')
@login_required
def product_details(product_id):
    product = None
    with open("databases/products.txt", "r") as file:
        for line in file:
            parts = line.strip().split('||')
            if parts[0] == product_id:
                # Convert prices to floats
                try:
                    price = float(parts[9])
                    original_price = price * 1.15  # 15% markup for demo
                except ValueError:
                    price = 0.0
                    original_price = 0.0
                
                product = {
                    'id': parts[0],
                    'seller': parts[1],
                    'category': parts[2],
                    'status': parts[3],
                    'title': parts[4],
                    'brand': parts[5],
                    'model': parts[6],
                    'year': parts[7],
                    'description': parts[8].strip('"'),
                    'price': "{:,.2f}".format(price),
                    'original_price': "{:,.2f}".format(original_price),
                    'discount_percent': round((1 - (price / original_price)) * 100),
                    'shipping_method': parts[10].replace('_', ' ').title(),
                    'shipping_cost': parts[11] if len(parts) > 11 else 'Free',
                    'shipping_paid_by': parts[12] if len(parts) > 12 else 'Seller',
                    'main_photo': parts[13],
                    'additional_photos': parts[14:] if len(parts) > 14 else [],
                    'quantity': parts[15] if len(parts) > 15 else '1',
                    'ratings': random.randint(1000, 5000),
                    'sold': random.randint(500, 2000),
                    'favorites': random.randint(100, 1000)
                }
                break
                
    if not product:
        abort(404)
        
    return render_template('product_details.html', product=product)

@app.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    if request.method == 'POST':
        # Get form data
        category = request.form.get('category')
        title = request.form.get('title')
        brand = request.form.get('brand')
        model = request.form.get('model')
        year = request.form.get('year')
        description = request.form.get('description')
        price = request.form.get('price')
        shipping_method = request.form.get('shipping_method')
        shipping_cost = request.form.get('shipping_cost', 0)
        shipping_paid_by = request.form.get('shipping_paid_by', 'buyer')
        status = "pending"

        # Ensure the database directory exists
        database_dir = "databases"
        os.makedirs(database_dir, exist_ok=True)

        # Increment ID
        products_file = os.path.join(database_dir, "products.txt")
        
        # If file doesn't exist, start with ID 1
        if not os.path.exists(products_file):
            listing_id = "1"
        else:
            # Read the file to find the highest existing ID
            highest_id = 0
            try:
                with open(products_file, "r") as file:
                    for line in file:
                        parts = line.strip().split('||')
                        if parts and parts[0].isdigit():
                            current_id = int(parts[0])
                            if current_id > highest_id:
                                highest_id = current_id
                
                # Next ID is highest + 1
                listing_id = str(highest_id + 1)
            except Exception as e:
                print(f"Error reading products file: {e}")
                # If there's an issue, start with ID 1
                listing_id = "1"

        # Ensure the upload directory exists
        upload_dir = os.path.join('static/uploads/product_images')
        os.makedirs(upload_dir, exist_ok=True)

        # Process main photo
        main_photo = request.files.get('main_photo')
        main_photo_filename = None
        if main_photo and main_photo.filename:
            # Generate a unique filename
            main_photo_filename = f"{current_user.id}_{int(time.time())}_main.jpg"
            # Save the file
            main_photo.save(os.path.join(upload_dir, main_photo_filename))
        
        # Process additional photos
        additional_photos = request.files.getlist('additional_photos')
        additional_photo_filenames = []
        for i, photo in enumerate(additional_photos):
            if photo and photo.filename:
                # Generate a unique filename
                photo_filename = f"{current_user.id}_{int(time.time())}_{i}.jpg"
                # Save the file
                photo.save(os.path.join(upload_dir, photo_filename))
                additional_photo_filenames.append(photo_filename)
    
        with open("databases/products.txt", "a") as file:
            file.write(f'{listing_id}||{current_user.id}||{category}||{status}||{title}||{brand}||{model}||{year}||'
                    f'"{description}"||{price}||{shipping_method}||{shipping_cost}||{shipping_paid_by}||'
                    f'{main_photo_filename}||{"||".join(additional_photo_filenames)}\n')

        # Flash a success message
        flash("Your listing has been submitted for review!")
        
        return redirect(url_for('account_posts', tab='pending'))
    
    # If GET request, just render the template
    return render_template('sell.html')

@app.route('/messages')
@login_required
def messages():
    return render_template('messages.html')

'''
@app.route('/account')
@login_required
def account():
    return render_template('account/account.html')
'''

@app.route('/account')
@login_required
def account():
    return render_template('account/account.html', active_page='profile')

@app.route('/account/profile')
@login_required
def account_profile():
    return render_template('account/account.html', active_page='profile')

@app.route('/account/listings')
@login_required
def account_listings():
    return render_template('account/account.html', active_page='listings')

'''
@app.route('/account/posts')
@login_required
def account_posts():
    # Get the active tab from query parameters, default to 'posted'
    active_tab = request.args.get('tab', 'posted')
    
    # Get user's posted products
    posted_products = []
    pending_products = []
    
    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 15 and parts[1] == current_user.id:
                    product = {
                        'id': parts[0],
                        'seller': parts[1],
                        'category': parts[2],
                        'status': parts[3],
                        'title': parts[4],
                        'brand': parts[5],
                        'model': parts[6],
                        'year': parts[7],
                        'description': parts[8].strip('"'),
                        'price': parts[9],
                        'shipping_method': parts[10],
                        'main_photo': f"/static/uploads/product_images/{parts[13]}" if parts[13] else "/static/images/default-product.jpg"
                    }
                    
                    if parts[3] == 'approved':
                        posted_products.append(product)
                    elif parts[3] == 'pending':
                        pending_products.append(product)
    except FileNotFoundError:
        pass
    
    # Sort products by ID in reverse order (newest first)
    posted_products.sort(key=lambda x: int(x['id']), reverse=True)
    pending_products.sort(key=lambda x: int(x['id']), reverse=True)

    posted_count = len(posted_products)
    pending_count = len(pending_products)
    
    return render_template('account/account.html', 
                          active_page='posts',
                          active_tab=active_tab,
                          posted_products=posted_products,
                          pending_products=pending_products,
                          posted_count=posted_count,
                          pending_count=pending_count)

                          
'''

# Define the context to hold product lists
class ProductContext:
    def __init__(self):
        self.posted_products = []
        self.pending_products = []

# Abstract strategy class
class ProductStrategy(ABC):
    @abstractmethod
    def process(self, product, context: ProductContext):
        pass

# Concrete strategies for each product status
class ApprovedStrategy(ProductStrategy):
    def process(self, product, context: ProductContext):
        context.posted_products.append(product)

class PendingStrategy(ProductStrategy):
    def process(self, product, context: ProductContext):
        context.pending_products.append(product)

# Strategy factory to map statuses to strategies
class ProductStrategyFactory:
    _strategies = {
        'approved': ApprovedStrategy(),
        'pending': PendingStrategy()
    }

    @classmethod
    def get_strategy(cls, status):
        return cls._strategies.get(status)

# Flask route using the Strategy Pattern
@app.route('/account/posts')
@login_required
def account_posts():
    active_tab = request.args.get('tab', 'posted')
    context = ProductContext()

    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 15 and parts[1] == current_user.id:
                    product = {
                        'id': parts[0],
                        'seller': parts[1],
                        'category': parts[2],
                        'status': parts[3],
                        'title': parts[4],
                        'brand': parts[5],
                        'model': parts[6],
                        'year': parts[7],
                        'description': parts[8].strip('"'),
                        'price': parts[9],
                        'shipping_method': parts[10],
                        'main_photo': f"/static/uploads/product_images/{parts[13]}" if parts[13] else "/static/images/default-product.jpg"
                    }
                    # Select and execute the appropriate strategy
                    strategy = ProductStrategyFactory.get_strategy(product['status'])
                    if strategy:
                        strategy.process(product, context)
    except FileNotFoundError:
        pass

    # Sort products by ID in reverse order
    context.posted_products.sort(key=lambda x: int(x['id']), reverse=True)
    context.pending_products.sort(key=lambda x: int(x['id']), reverse=True)

    posted_count = len(context.posted_products)
    pending_count = len(context.pending_products)
    
    return render_template('account/account.html', 
                          active_page='posts',
                          active_tab=active_tab,
                          posted_products=context.posted_products,
                          pending_products=context.pending_products,
                          posted_count=posted_count,
                          pending_count=pending_count)

@app.route('/account/sold')
@login_required
def account_sold():
    return render_template('account/account.html', active_page='sold')

@app.route('/account/favorites')
@login_required
def account_favorites():
    return render_template('account/account.html', active_page='favorites')

@app.route('/account/purchases')
@login_required
def account_purchases():
    return render_template('account/account.html', active_page='purchases')

@app.route('/account/settings')
@login_required
def account_settings():
    return render_template('account/account.html', active_page='settings')
    
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