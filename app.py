import os
import time
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
        
        return redirect(url_for('sell'))
    
    # If GET request, just render the template
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