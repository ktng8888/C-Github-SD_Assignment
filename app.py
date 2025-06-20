#================================================================================================================
# Group : ChatGPT (TT3L)

# Group Members :
# NG KEAN TIONG 242UC244V5 (Leader)
# WILLIAM SIM WEE LIAN 243UC245RN 
# FOO YAU YUN 1211111966
# TAN ZHE ENN 242UC2451F
#================================================================================================================

import random 
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict #yy

#================================================================================================================
# Strategy Pattern
# Usage : Admin Dashboard Order Bar Chart (Display bar chart based on different display selection)
# Flask Route : @app.route('/admin/admin_dashboard')
class OrderDisplayStrategy(ABC):
    @abstractmethod
    def get_orders_data(self, raw_orders):
        pass

class MonthlyOrderStrategy(OrderDisplayStrategy):
    def get_orders_data(self, raw_orders):
        monthly_counts = [0] * 12
        for order in raw_orders:
            if order['order_time_obj'].month:
                monthly_counts[order['order_time_obj'].month - 1] += 1
        return [{"label": m, "collections": c} for m, c in zip(
            ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            monthly_counts)]

class WeeklyOrderStrategy(OrderDisplayStrategy):
    def get_orders_data(self, raw_orders):
        weekly_counts = [0] * 53
        for order in raw_orders:
            week_num = order['order_time_obj'].isocalendar()[1]
            if 1 <= week_num <= 53:
                weekly_counts[week_num - 1] += 1
        return [{"label": f"Week {i+1}", "collections": c} 
               for i, c in enumerate(weekly_counts)]

class YearlyOrderStrategy(OrderDisplayStrategy):
    def get_orders_data(self, raw_orders):
        yearly_counts = {}
        for order in raw_orders:
            year = order['order_time_obj'].year
            yearly_counts[year] = yearly_counts.get(year, 0) + 1
        return [{"label": str(y), "collections": c} 
               for y, c in sorted(yearly_counts.items())]

class OrderContext:
    def __init__(self):
        self._strategy = MonthlyOrderStrategy()  # Default strategy
    
    def set_strategy(self, strategy):
        self._strategy = strategy
    
    def get_order_data(self, raw_orders):
        return self._strategy.get_orders_data(raw_orders)
#================================================================================================================

#================================================================================================================
# Observer Pattern
# Usage : Notify admin and seller when product status changes
# Flask Route : @app.route('/admin/update_product_status', methods=['POST'])
class ProductStatusSubject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self, product_id, new_status, seller_id):
        for observer in self._observers:
            observer.update(product_id, new_status, seller_id)
    
class ProductStatusObserver(ABC):
    @abstractmethod
    def update(self, product_id, new_status, seller_id):
        pass

'''Notify Admin'''
class AdminNotificationObserver(ProductStatusObserver):
    def update(self, product_id, new_status, seller_id):
        """Only for admin dashboard notifications"""
        
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 11 and parts[0] == product_id:
                    product_title = parts[4]
        
        message = f"Product {product_title} status changed to {new_status}. Notification successfully sent to seller {seller_id}."
        try:
            from flask import flash
            flash(message,"admin_notification")
        except ImportError:
            print("Flask not available for popup notification")
        except RuntimeError:
            print("Outside of Flask application context")
            
'''
Store to notification.txt 
Seller can check notification through notification button
'''
class DatabaseNotificationObserver(ProductStatusObserver):
    def update(self, product_id, new_status, seller_id):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        highest_id = 0
        notification_id = 0;
        # Read existing notification
        try:    
            with open("databases/notification.txt", "r") as file:
                for line in file:
                    parts = line.strip().split('||')
                    if len(parts) >= 6:
                        try:
                            current_id = int(parts[0])
                            if current_id > highest_id:
                                highest_id = current_id
                        except ValueError:
                            pass
        except FileNotFoundError:
            pass
        
        notification_id = str(highest_id + 1)

        try:
            with open("databases/notification.txt", "a") as file:
                file.write(f"{notification_id}||{product_id}||{seller_id}||{new_status}||{timestamp}||False\n")
        except Exception as e:
            print(f"Error saving notification: {e}")

# Global subject instance
product_status_subject = ProductStatusSubject()
product_status_subject.attach(AdminNotificationObserver())
product_status_subject.attach(DatabaseNotificationObserver())
#================================================================================================================


#================================================================================================================
# Factory Pattern
# Usage : Seller sells an Electronic Item (Product Creation)
# Flask Route : @app.route('/sell', methods=['GET', 'POST'])
class ProductFactory:
    @staticmethod
    def create_product(parts):
        """Creates a product with category-specific features from pipe-delimited data"""
            
        main_photo_proxy = ProductImageProxy(parts[11]).display()
        additional_photos_proxies = [
            ProductImageProxy(photo).display() 
            for photo in parts[12:] 
            if photo.strip()
        ] if len(parts) > 12 else []
        
        common_data = {    
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
            'shipping_cost': parts[10],
            'main_photo': main_photo_proxy,
            'additional_photos': additional_photos_proxies
        }

        category_map = {
            'smartphone': Smartphone,
            'laptop': Laptop,
            'tablet': Tablet,
            'camera': Camera,
            'audio': Audio
        }

        return category_map.get(parts[2].lower(), ElectronicProduct)(common_data)

class ElectronicProduct:
    def __init__(self, data):
        self.data = data
    
    def get_recommendation_brands(self):
        return ['Generic Brand']

class Smartphone(ElectronicProduct):
    def get_recommendation_brands(self):
        return ['Apple', 'Samsung', 'Xiaomi', 'Google', 'OnePlus']

class Laptop(ElectronicProduct):
    def get_recommendation_brands(self):
        return ['Apple', 'Dell', 'HP', 'Lenovo', 'Asus']

class Tablet(ElectronicProduct):
    def get_recommendation_brands(self):
        return ['Apple', 'Samsung', 'Microsoft', 'Huawei', 'Lenovo']

class Camera(ElectronicProduct):
    def get_recommendation_brands(self):
        return ['Canon', 'Nikon', 'Sony', 'Fujifilm', 'Panasonic']

class Audio(ElectronicProduct):
    def get_recommendation_brands(self):
        return ['Sony', 'Bose', 'Sennheiser', 'JBL', 'Audio-Technica']
#================================================================================================================


#================================================================================================================
# Proxy Pattern
# Usage : Handle Lazy Loading of Product Images
# Flask Route : 
# - @app.route('/products')
# - @app.route('/product/<product_id>')
# - @app.route('/account/...')

class ImageSubject(ABC):
    @abstractmethod
    def display(self) -> str:
        pass

class RealProductImage(ImageSubject):
    def __init__(self, filename):
        self.filename = filename
        self._verify_image()

    def display(self):
        return f"/static/uploads/product_images/{self.filename}"

    def __str__(self):
        """String representation"""
        return self.display()

    def _verify_image(self):
        if not os.path.exists(f'static/uploads/product_images/{self.filename}'):
            raise FileNotFoundError(f"Image {self.filename} not found")

class ProductImageProxy(ImageSubject):
    def __init__(self, filename):
        self.filename = filename
        self._real_image = None

    def display(self):
        if self._real_image is None:
            try:
                self._real_image = RealProductImage(self.filename)
            except FileNotFoundError:
                return "/static/images/default-product.jpg"
        return self._real_image.display()
    
    def __str__(self):
        return self.display()
#================================================================================================================


#================================================================================================================
# Facade Pattern
# Usage : Handle all authentication logic
# Flask Route : 
# - @app.route('/login', methods=['GET', 'POST'])
# - @app.route('/logout')
# - @app.route('/register', methods=['GET', 'POST'])
# - @app.route('/admin_register', methods=['GET', 'POST'])

class UserAuthFacade:
    def __init__(self):
        pass

    def authenticate_user(self, username, password):
        """Check if the user exists and verify password."""
        with open("databases/member_detail.txt", "r") as file:
            for line in file:
                data = line.strip().split('||')
                if (data[0] == username or data[2] == username) and check_password_hash(data[3], password):
                    return User(
                        username=data[0],
                        phone=data[1],
                        email=data[2],
                        password=data[3],
                        address=data[4],
                        profile_image=data[5],
                        role=data[6]
                    )
        return None

    def login_user(self, user):
        login_user(user)
        return user.role == "admin"  # Returns True if admin, False if regular user

    def logout_user(self):
        logout_user()

    def register_user(self, username, phone, email, password, confirm_password):
        if password != confirm_password:
            return False, "Passwords do not match!"

        # Check if username or email already exists
        with open("databases/member_detail.txt", "r") as file:
            for line in file:
                data = line.strip().split('||')
                if data[0] == username:
                    return False, "Username already exists!"
                if data[2] == email:
                    return False, "Email already registered!"

        # Hash password and store user
        hashed_password = generate_password_hash(password)
        with open("databases/member_detail.txt", "a") as file:
            file.write(f"{username}||{phone}||{email}||{hashed_password}||-||-||user\n")

        return True, "Registration successful! Please login."
    
    def admin_register_user(self, username, phone, email, password, confirm_password):
        """Register a new admin user after validation."""
        if password != confirm_password:
            return False, "Passwords do not match!"

        # Check if username or email exists
        with open("databases/member_detail.txt", "r") as file:
            for line in file:
                data = line.strip().split('||')
                if data[0] == username:
                    return False, "Username already exists!"
                if data[2] == email:
                    return False, "Email already registered!"

        # Hash password and store as admin
        hashed_password = generate_password_hash(password)
        with open("databases/member_detail.txt", "a") as file:
            file.write(f"{username}||{phone}||{email}||{hashed_password}||-||-||admin\n")

        return True, "Admin registration successful! Please login."

user_auth_facade = UserAuthFacade()  # Initialize the facade

#================================================================================================================

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username, phone, email, password, address, profile_image, role): #yy
        self.id = username
        self.username = username
        self.phone = phone
        self.email = email
        self.password = password
        self.address = address
        self.profile_image = profile_image
        self.role = role #yy

def get_feedback_for_seller(seller_id):
    feedbacks = []
    try:
        with open("databases/feedback.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 8 and parts[3] == seller_id: 
                    feedbacks.append({
                        'buyer_username': parts[4],
                        'rating': int(parts[5]),
                        'comment': parts[6],
                        'timestamp': parts[7]
                    })
    except FileNotFoundError:
        pass
    return feedbacks

def get_product_by_id(product_id):
    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 11 and parts[0] == product_id:

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
                        'main_photo': f"/static/uploads/product_images/{parts[11]}" if parts[11] else "/static/images/default-product.jpg"
                    }
                    return product
    except FileNotFoundError:
        return None
    
    return None 

@login_manager.user_loader
def load_user(username):
    with open("databases/member_detail.txt", "r") as file:
        for line in file:
            data = line.strip().split('||')
            if data[0] == username:
                return User(data[0], data[1], data[2], data[3], data[4], data[5], data[6]) #yy
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
                if len(parts) >= 11 : 
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
                        'shipping_cost': parts[10],
                        'main_photo': parts[11],
                        # Add a random rating
                        'rating': round(random.uniform(4.5, 5.0), 1),
                        'review_count': random.randint(10, 60),
                        # Add a random "posted time"
                        'posted_time': random.choice(["Posted 1 day ago", "Posted 2 days ago", "Posted 3 days ago", "Posted 1 week ago"])
                    }
                    
                    if product['status'] == "approved":
                        featured_products.append(product)
                        count += 1
    except FileNotFoundError:
        # If the file doesn't exist, we'll just show empty featured products
        pass

    return render_template('main.html',featured_products=featured_products)

@app.route('/require_login')
def require_login():
    flash("Please login to access this feature")
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == "admin": #yy
            return redirect(url_for('admin_dashboard')) #yy
        else: #yy
            return redirect(url_for('main'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = user_auth_facade.authenticate_user(username, password)
        if user:
            is_admin = user_auth_facade.login_user(user)
            return redirect(url_for('admin_dashboard' if is_admin else 'main'))
        
        flash("Invalid username or password.")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    user_auth_facade.logout_user()
    return redirect(url_for('main'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        success, message = user_auth_facade.register_user(username, phone, email, password, confirm)
        
        flash(message)
        if success:
            return redirect(url_for('login'))

    
    return render_template('register.html')

# yy admin register start
@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        success, message = user_auth_facade.admin_register_user(
            username, phone, email, password, confirm
        )
        flash(message)
        if success:
            return redirect(url_for('login'))
    
    return render_template('admin/admin_register.html')
# yy admin register end


@app.route('/user_notifications')
@login_required
def user_notifications():
    notifications = []
    unseen_count = 0

    try:
        with open("databases/notification.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                
                if len(parts) >= 6 and parts[2] == current_user.id and parts[5] == "False":
                    # Get product title
                    product_title = "Unknown Product"
                    try:
                        with open("databases/products.txt", "r") as pfile:
                            for pline in pfile:
                                pparts = pline.strip().split('||')
                                if len(pparts) >= 11 and pparts[0] == parts[1]:
                                    product_title = pparts[4]
                                    break
                    except FileNotFoundError:
                        pass

                    is_seen = parts[5]

                    if is_seen == "False":
                        unseen_count += 1
                    
                    # Format notification message based on status
                    if parts[3] == 'approved':
                        title = "Product Approved!"
                        message = f'Your "{product_title}" has been approved and is now listed for sale.'
                        icon_type = "approved"
                    elif parts[3] == 'rejected':
                        title = "Product Rejected"
                        message = f'Your "{product_title}" listing was rejected. Please review and try again.'
                        icon_type = "rejected"
                    else:
                        title = "Product Status Updated"
                        message = f'Your "{product_title}" status has been updated to {parts[3]}.'
                        icon_type = "info"
                    
                    notifications.append({
                        'notification_id': parts[0],
                        'product_id': parts[1],
                        'product_title': product_title,
                        'status': parts[3],
                        'timestamp': parts[4],
                        'is_seen': is_seen,
                        'title': title,
                        'message': message,
                        'icon_type': icon_type,
                        'time_ago': get_time_ago(parts[4])
                    })
    except FileNotFoundError:
        pass
    
    # Sort by timestamp (newest first)
    notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        'notifications': notifications,
        'unseen_count': unseen_count
    })

def get_time_ago(timestamp_str):
    """Convert timestamp to 'time ago' format"""
    try:
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    except ValueError:
        return "Unknown"

@app.route('/mark_notifications_seen', methods=['POST'])
@login_required
def mark_notifications_seen():
    try:
        # Read all notifications
        with open("databases/notification.txt", "r") as file:
            lines = file.readlines()
        
        # Update notifications for current user
        updated_lines = []
        for line in lines:
            parts = line.strip().split('||')
            if len(parts) >= 6 and parts[2] == current_user.id:
                parts[5] = "True"  # Mark as seen
                updated_lines.append('||'.join(parts) + '\n')
            else:
                updated_lines.append(line)
        
        # Write back to file
        with open("databases/notification.txt", "w") as file:
            file.writelines(updated_lines)
            
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/products')

def products():
    current_user.id = current_user.id if current_user.is_authenticated else '0'
    products = []
    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 11:
                    main_photo_proxy = ProductImageProxy(parts[11]).display()
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
                        'shipping_cost':parts[10],
                        'main_photo': main_photo_proxy
                    })
    except FileNotFoundError:
        pass

    # Get user's favorites
    user_favorites = []
    try:
        with open("databases/favorites.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 4 and parts[1] == current_user.id:
                    user_favorites.append(parts[2])
    except FileNotFoundError:
        pass

    # Add favorite status to each product
    for product in products:
        product['is_favorite'] = product['id'] in user_favorites

    # Show only approved products
    products = [p for p in products if p['status'] == 'approved']

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

@app.route('/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite():
    from flask import jsonify
    from datetime import datetime
    
    product_id = request.json.get('product_id')
    username = current_user.id
    
    if not product_id or not username:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    favorites = []
    is_favorite = False
    highest_id = 0
    
    # Read existing favorites
    try:
        with open("databases/favorites.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 4:
                    favorites.append(parts)
                    
                    try:
                        current_id = int(parts[0])
                        if current_id > highest_id:
                            highest_id = current_id
                    except ValueError:
                        pass
                    
                    if parts[1] == username and parts[2] == product_id:
                        is_favorite = True
    except FileNotFoundError:
        pass
    
    if is_favorite:
        # Remove from favorites
        favorites = [f for f in favorites if not (f[1] == username and f[2] == product_id)]
        action = 'removed'
    else:
        # Add to favorites
        new_id = str(highest_id + 1)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        favorites.append([new_id, username, product_id, timestamp])
        action = 'added'
    
    # Write back to file
    try:
        with open("databases/favorites.txt", "w") as file:
            for fav in favorites:
                file.write('||'.join(fav) + '\n')
        
        return jsonify({'success': True, 'action': action, 'is_favorite': not is_favorite})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error updating favorites'})

@app.route('/product/<product_id>')

def product_details(product_id):
    
    current_user.id = current_user.id if current_user.is_authenticated else '0'

    user_data = {
        'username': current_user.username if current_user.is_authenticated else 'Guest',
        'email': current_user.email if current_user.is_authenticated else '',
        'phone': current_user.phone if current_user.is_authenticated and current_user.phone != '-' else '',
        'address': current_user.address if current_user.is_authenticated and current_user.address != '-' else '',
        'profile_image': current_user.profile_image if current_user.is_authenticated and current_user.profile_image != '-' else None
    }
    
    product = None
    with open("databases/products.txt", "r") as file:
        for line in file:
            parts = line.strip().split('||')
            if parts[0] == product_id:
                # Convert prices to floats
                try:
                    price = float(parts[9])
                except ValueError:
                    price = 0.0
                try:
                    shipping_cost = float(parts[10])
                except ValueError:
                    shipping_cost = 0.0
            
                # Handle main photo with ProductImageProxy
                main_photo_proxy = ProductImageProxy(parts[11]).display()
                    
                # Handle additional photos (apply proxy to each)
                additional_photos_proxies = [
                    ProductImageProxy(photo).display() 
                    for photo in parts[12:] 
                    if photo.strip()  # Skip empty entries
                ] if len(parts) > 12 else []    
                
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
                    'shipping_cost': "{:,.2f}".format(shipping_cost),
                    'main_photo': main_photo_proxy,
                    'additional_photos': additional_photos_proxies,
                    'favorites': random.randint(100, 1000)
                }
                break
                
    if not product:
        abort(404)
    
    # Get feedback for the seller of this product
    seller_feedbacks = get_feedback_for_seller(product['seller'])
        
    return render_template('product_details.html', 
                         product=product, 
                         user_data=user_data,
                         seller_feedbacks=seller_feedbacks)

@app.route('/order/<product_id>')
@login_required
def product_order(product_id):
    # Get the same product data for the order page
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'phone': current_user.phone if current_user.phone != '-' else '',
        'address': current_user.address if current_user.address != '-' else '',
        'profile_image': current_user.profile_image if current_user.profile_image != '-' else None
    }
    
    product = None
    with open("databases/products.txt", "r") as file:
        for line in file:
            parts = line.strip().split('||')
            if parts[0] == product_id:
                # Convert prices to floats for calculations
                try:
                    price = float(parts[9])
                except ValueError:
                    price = 0.0

                try:
                    shipping_cost = float(parts[10])
                except ValueError:
                    shipping_cost = 0.0
                
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
                    'price': price, 
                    'shipping_cost': shipping_cost,
                    'main_photo': parts[11],
                    'additional_photos': parts[12:] if len(parts) > 12 else []
                }
                break
                
    if not product:
        abort(404)
    
    # CHECK 1: Prevent ordering sold products
    if product['status'].lower() == 'sold':
        flash('This product has already been sold!', 'error')
        return redirect(url_for('product_details', product_id=product_id))
    
    # CHECK 2: Prevent seller from accessing their own product order page
    if user_data.get('username') == product['seller']:
        flash('You cannot order your own product!', 'error')
        return redirect(url_for('product_details', product_id=product_id))
    
    # Get seller's feedback
    seller_feedbacks = get_feedback_for_seller(product['seller'])
    
    return render_template('product_order.html', 
                         product=product, 
                         user_data=user_data,
                         seller_feedbacks=seller_feedbacks)


@app.route('/handle_order/<product_id>', methods=['GET', 'POST'])
@login_required
def handle_order(product_id):
    if request.method == 'POST':
        buyer_username = request.form.get('buyer_username')
        payment_method = request.form.get('payment_method')
        delivery_address = request.form.get('delivery_address')
        
        # Basic validation
        if not payment_method:
            flash('Please select a payment method', 'error')
            return redirect(url_for('product_order', product_id=product_id))
            
        if not delivery_address or not delivery_address.strip():
            flash('Please enter your delivery address', 'error')
            return redirect(url_for('product_order', product_id=product_id))

        # Get product details to calculate total
        product = None
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if parts[0] == product_id:
                    try:
                        price = float(parts[9])
                        shipping_cost = float(parts[10])
                        product = {
                            'id': parts[0],
                            'seller': parts[1],
                            'title': parts[4],
                            'price': price,
                            'shipping_cost': shipping_cost
                        }
                        break
                    except (ValueError, IndexError):
                        flash('Error reading product data', 'error')
                        return redirect(url_for('home'))
        
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('home'))

        # Ensure the database directory exists
        database_dir = "databases"
        os.makedirs(database_dir, exist_ok=True)

        # Generate order ID
        orders_file = os.path.join(database_dir, "orders.txt")
        
        # If file doesn't exist, start with ID 1
        if not os.path.exists(orders_file):
            order_id = "1"
        else:
            # Read the file to find the highest existing ID
            highest_id = 0
            try:
                with open(orders_file, "r") as file:
                    for line in file:
                        parts = line.strip().split('||')
                        if parts and parts[0].isdigit():
                            current_id = int(parts[0])
                            if current_id > highest_id:
                                highest_id = current_id
                
                # Next ID is highest + 1
                order_id = str(highest_id + 1)
            except Exception as e:
                print(f"Error reading orders file: {e}")
                # If there's an issue, start with ID 1
                order_id = "1"

        # Calculate payment amount
        payment_amount = product['price'] + product['shipping_cost']
        
        # Get current timestamp
        from datetime import datetime
        order_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        status = "shipping"
        delivered_date = "-"
        
        # Write order to file
        try:
            with open(orders_file, "a") as file:
                file.write(f'{order_id}||{buyer_username}||{product_id}||{order_time}||{payment_method}||{payment_amount}||{delivery_address}||{status}||{delivered_date}\n')
            
            products_file = "databases/products.txt"
            
            # Read all products
            updated_lines = []
            with open(products_file, "r") as file:
                for line in file:
                    parts = line.strip().split('||')
                    if parts[0] == product_id:
                        # Change status from 'pending' to 'sold' (parts[3])
                        parts[3] = 'sold'
                        updated_lines.append('||'.join(parts) + '\n')
                    else:
                        updated_lines.append(line)
            
            # Write back all products with updated status
            with open(products_file, "w") as file:
                file.writelines(updated_lines)

            
        except Exception as e:
            flash('Error placing order. Please try again.', 'error')
    
    return redirect(url_for('account_orders', tab='shipping'))

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
        shipping_cost = request.form.get('shipping_cost', 0)
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

        # Prepare the data parts for the factory
        product_parts = [
            listing_id,                  # 0: id
            current_user.id,             # 1: seller
            category,                    # 2: category
            status,                      # 3: status
            title,                       # 4: title
            brand,                       # 5: brand
            model,                       # 6: model
            year,                        # 7: year
            description,                 # 8: description
            price,                       # 9: price
            shipping_cost,               # 10: shipping_cost
            main_photo_filename          # 11: main_photo
        ] + additional_photo_filenames   # 12+: additional_photos

        # Use the ProductFactory to create a product object
        product = ProductFactory.create_product(product_parts)
        
        # We can access recommendations if needed
        recommendation_brands = product.get_recommendation_brands()
        print(f"Recommended Brands: {recommendation_brands}")

        # Write the product data to file
        with open("databases/products.txt", "a") as file:
            file.write('||'.join(product_parts) + '\n')

        '''
        with open("databases/products.txt", "a") as file:
            file.write(f'{listing_id}||{current_user.id}||{category}||{status}||{title}||{brand}||{model}||{year}||'
                    f'"{description}"||{price}||{shipping_cost}||'
                    f'{main_photo_filename}||{"||".join(additional_photo_filenames)}\n')         
        '''
        # Flash a success message
        flash("Your listing has been submitted for review!")
        
        return redirect(url_for('account_listings', tab='pending'))
    
    # If GET request, just render the template
    return render_template('sell.html')

@app.route('/term_and_condition')
@login_required
def term_and_condition():
    return render_template('term_and_condition.html')

@app.route('/account')
@login_required
def account():
    feedbacks = []
    try:
        with open("databases/feedback.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 8 and parts[3] == current_user.id: 
                    product_title = "Unknown Product"
                    try:
                        with open("databases/products.txt", "r") as prod_file:
                            for prod_line in prod_file:
                                prod_parts = prod_line.strip().split('||')
                                if len(prod_parts) >= 5 and prod_parts[0] == parts[2]:  
                                    product_title = prod_parts[4]  
                                    break
                    except FileNotFoundError:
                        pass
                    
                    feedbacks.append({
                        'buyer_username': parts[4], 
                        'product_title': product_title,
                        'rating': parts[5],  
                        'comment': parts[6],  
                        'timestamp': parts[7]  
                    })
    except FileNotFoundError:
        print("Feedback file not found")  
        pass
    
    print(f"Found {len(feedbacks)} feedbacks for user {current_user.id}")  
    
    return render_template('account/account.html',
                         active_page='profile',
                         feedbacks=feedbacks)

@app.route('/account/profile')
@login_required
def account_profile():
    active_tab = request.args.get('tab', 'listing')
    user_profile_image = current_user.profile_image if current_user.profile_image != '-' else None
    
    seller_total_products = []
    favorite_products = []
    sold_products = []
    user_favorites = []
    feedbacks = []
    
 
    try:
        with open("databases/favorites.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 4 and parts[1] == current_user.id: 
                    user_favorites.append(parts[2]) 
    except FileNotFoundError:
        pass

    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 11:
                    product_id = parts[0]

                    main_photo_proxy = ProductImageProxy(parts[11]).display()
                    
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
                        'main_photo': main_photo_proxy
                    }

                    if parts[1] == current_user.id:
                        seller_total_products.append(product)
                        if parts[3] == 'sold':
                            sold_products.append(product)
                    
                    if product_id in user_favorites:
                        favorite_products.append(product)
    
    except FileNotFoundError:
        pass
    
    try:
        with open("databases/feedback.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 8 and parts[3] == current_user.id:  # parts[3] is seller username
                    # Get product title
                    product_title = "Unknown Product"
                    try:
                        with open("databases/products.txt", "r") as prod_file:
                            for prod_line in prod_file:
                                prod_parts = prod_line.strip().split('||')
                                if len(prod_parts) >= 5 and prod_parts[0] == parts[2]:  # product ID match
                                    product_title = prod_parts[4]  # product title
                                    break
                    except FileNotFoundError:
                        pass
                    
                    feedbacks.append({
                        'buyer_username': parts[4],
                        'product_title': product_title,
                        'rating': parts[5],
                        'comment': parts[6],
                        'timestamp': parts[7]
                    })
    except FileNotFoundError:
        pass
    
    seller_total_products.sort(key=lambda x: int(x['id']), reverse=True)
    favorite_products.sort(key=lambda x: int(x['id']), reverse=True)
    sold_products.sort(key=lambda x: int(x['id']), reverse=True)

    seller_total_products_count = len(seller_total_products)
    favorite_count = len(favorite_products)
    sold_count = len(sold_products) 

    return render_template('account/account.html', active_page='profile',
                         active_tab=active_tab,
                         user_profile_image=user_profile_image,
                         seller_total_products=seller_total_products,
                         favorite_products=favorite_products,
                         sold_products=sold_products,
                         seller_total_products_count=seller_total_products_count,
                         favorite_count=favorite_count,
                         sold_count=sold_count,
                         feedbacks=feedbacks,  # Add this line
                         feedback_count=len(feedbacks))  # Add this line

# Define the context to hold product lists
class ProductContext:
    def __init__(self):
        self.listing_products = []
        self.pending_products = []

# Abstract strategy class
class ProductStrategy(ABC):
    @abstractmethod
    def process(self, product, context: ProductContext):
        pass

# Concrete strategies for each product status
class ApprovedStrategy(ProductStrategy):
    def process(self, product, context: ProductContext):
        context.listing_products.append(product)

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
@app.route('/account/listings')
@login_required
def account_listings():
    active_tab = request.args.get('tab', 'listing')
    context = ProductContext()

    notifications = []
    unseen_count = 0

    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 11 and parts[1] == current_user.id:
                    
                    main_photo_proxy = ProductImageProxy(parts[11]).display()

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
                        'shipping_cost': parts[10],
                        'main_photo': main_photo_proxy
                    }
                    # Select and execute the appropriate strategy
                    strategy = ProductStrategyFactory.get_strategy(product['status'])
                    if strategy:
                        strategy.process(product, context)
    except FileNotFoundError:
        pass

    # Sort products by ID in reverse order
    context.listing_products.sort(key=lambda x: int(x['id']), reverse=True)
    context.pending_products.sort(key=lambda x: int(x['id']), reverse=True)

    listing_count = len(context.listing_products)
    pending_count = len(context.pending_products)
    
    try:
        with open("databases/notification.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 6 and parts[2] == current_user.id:
                    # Get product title
                    product_title = "Unknown Product"
                    with open("databases/products.txt", "r") as pfile:
                        for pline in pfile:
                            pparts = pline.strip().split('||')
                            if len(pparts) >= 5 and pparts[0] == parts[1]:
                                product_title = pparts[4]
                                break
                    
                    is_seen = parts[5] == "True"
                    if not is_seen:
                        unseen_count += 1
                    
                    notifications.append({
                        'notification_id': parts[0],
                        'product_id': parts[1],
                        'product_title': product_title,
                        'status': parts[3],
                        'timestamp': parts[4],
                        'is_seen': is_seen
                    })
    except FileNotFoundError:
        pass
    
    return render_template('account/account.html', 
                          active_page='listings',
                          active_tab=active_tab,
                          listing_products=context.listing_products,
                          pending_products=context.pending_products,
                          listing_count=listing_count,
                          pending_count=pending_count,

                          notifications=notifications[-5:],  # Show last 5
                          notification_count=len(notifications),
                          unseen_count=unseen_count)

@app.route('/account/sold')
@login_required
def account_sold():
    sold_products = []
    order_record = {}

    try:
        with open("databases/orders.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                order_id = parts[0]
                buyer_username = parts[1] 
                product_id = parts[2]
                order_date = parts[3]
                payment_method = parts[4]
                amount_paid = parts[5]
                delivery_address = parts[6],
                status = parts[7]
                delivered_date = parts[8] if parts[7] else None
                
                order_record[product_id] = {
                    'order_id': order_id,
                    'buyer_username': buyer_username,
                    'order_date': order_date,
                    'payment_method': payment_method,
                    'amount_paid': amount_paid,
                    'delivery_address' : delivery_address,
                    'status': status,
                    'delivered_date': delivered_date
                }
    except FileNotFoundError:
        pass

    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 11 and parts[1] == current_user.id and parts[3] == 'sold':
                    product_id = parts[0]  # Define product_id here
                    
                    if product_id in order_record:
                        order_info = order_record[product_id]

                        main_photo_proxy = ProductImageProxy(parts[11]).display()

                        additional_photos_proxies = [
                            ProductImageProxy(photo).display() 
                            for photo in parts[12:] 
                            if photo.strip()  # Skip empty entries
                        ] if len(parts) > 12 else []
                        
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
                            'shipping_cost': parts[10],
                            'main_photo': main_photo_proxy,
                            'additional_photos': additional_photos_proxies,

                            # Add order information
                            'order_id': order_info['order_id'],
                            'buyer_username': order_info['buyer_username'],
                            'order_date': order_info['order_date'],
                            'payment_method': order_info['payment_method'],
                            'amount_paid': order_info['amount_paid'],
                            'delivery_address' : order_info['delivery_address'],
                            'order_status': order_info['status'],
                            'delivered_date': order_info['delivered_date']
                        }
                        sold_products.append(product)

    except FileNotFoundError:
        pass
    
    sold_products.sort(key=lambda x: (0 if x['order_status'] == 'shipping' else 1, -int(x['id'])))

    sold_products_count = len(sold_products)

    return render_template('account/account.html', active_page='sold',
                            sold_products=sold_products,
                            sold_products_count = sold_products_count)

@app.route('/account/favorites')
@login_required
def account_favorites():
    favorite_products = []
    
    # Get user's favorite product IDs
    user_favorites = []
    try:
        with open("databases/favorites.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 4 and parts[1] == current_user.id:  # Check if user matches
                    user_favorites.append(parts[2])  # Add product_id to favorites list
    except FileNotFoundError:
        pass

    # Get product details for favorited products
    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 11:
                    product_id = parts[0]
                    
                    # Only include products that user has favorited
                    if product_id in user_favorites:
                        
                        main_photo_proxy = ProductImageProxy(parts[11]).display()

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
                            'shipping_cost': parts[10],
                            'main_photo': main_photo_proxy
                        }
                        favorite_products.append(product)
    except FileNotFoundError:
        pass
    
    favorite_products.sort(key=lambda x: int(x['id']), reverse=True)
    favorite_products_count = len(favorite_products)

    return render_template('account/account.html', 
                          active_page='favorites', 
                          favorite_products=favorite_products,
                          favorite_products_count = favorite_products_count)

@app.route('/remove_favorite/<product_id>', methods=['POST'])
@login_required
def remove_favorite(product_id):
    username = current_user.id
    favorites = []
    
    # Read existing favorites
    try:
        with open("databases/favorites.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 4:
                    favorites.append(parts)
    except FileNotFoundError:
        pass
    
    # Remove the specific favorite for this user and product
    favorites = [f for f in favorites if not (f[1] == username and f[2] == product_id)]
    
    # Write back to file
    try:
        with open("databases/favorites.txt", "w") as file:
            for fav in favorites:
                file.write('||'.join(fav) + '\n')
        
        flash("Item removed from favorites!")
        return redirect(url_for('account_favorites'))
    except Exception as e:
        flash("Error removing item from favorites")
        return redirect(url_for('account_favorites'))

@app.route('/account/orders')
@login_required
def account_orders():
    active_tab = request.args.get('tab', 'shipping')
    shipping_orders = []
    delivered_orders = []
    completed_orders = []
    
    # First, get all orders for current user
    user_orders = {}
    try:
        with open("databases/orders.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 8 and parts[1] == current_user.id:  # user_id matches
                    product_id = parts[2]
                    user_orders[product_id] = {
                        'order_id': parts[0],
                        'order_date': parts[3],
                        'payment_method': parts[4],
                        'amount_paid': parts[5],
                        'delivery_address': parts[6],
                        'status': parts[7],
                        'delivered_date': parts[8] if len(parts) >8 and parts[8] else None
                    }
    except FileNotFoundError:
        pass
    
    # Check which orders have feedback
    feedback_exists = set()
    try:
        with open("databases/feedback.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 5 and parts[4] == current_user.id:  # buyer matches
                    feedback_exists.add(parts[1])  # order_id
    except FileNotFoundError:
        pass
    
    # Then get product details and combine with order info
    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 11:
                    product_id = parts[0]
                    
                    # Only include products that current user has ordered
                    if product_id in user_orders:
                        order_info = user_orders[product_id]
                        
                        main_photo_proxy = ProductImageProxy(parts[11]).display()

                        order_product = {
                            'id': parts[0],
                            'seller': parts[1],
                            'category': parts[2],
                            'title': parts[4],
                            'brand': parts[5],
                            'model': parts[6],
                            'year': parts[7],
                            'description': parts[8].strip('"'),
                            'price': parts[9],
                            'shipping_cost': parts[10],
                            'main_photo': main_photo_proxy,
                            
                            # Add order information
                            'order_id': order_info['order_id'],
                            'order_date': order_info['order_date'],
                            'payment_method': order_info['payment_method'],
                            'amount_paid': order_info['amount_paid'],
                            'delivery_address': order_info['delivery_address'],
                            'order_status': order_info['status'],
                            'delivered_date': order_info['delivered_date'],
                            'sold_date': order_info['delivered_date'] if order_info['delivered_date'] else order_info['order_date'],
                            'feedback_submitted': order_info['order_id'] in feedback_exists
                        }
                        
                        # Sort into appropriate lists based on status
                        if order_info['status'] == 'shipping':
                            shipping_orders.append(order_product)
                        elif order_info['status'] == 'delivered':
                            delivered_orders.append(order_product)
                        elif order_info['status'] == 'completed':
                            completed_orders.append(order_product)
    except FileNotFoundError:
        pass
    
    # Sort orders by order date in reverse order (newest first)
    shipping_orders.sort(key=lambda x: x['order_date'], reverse=True)
    delivered_orders.sort(key=lambda x: x['order_date'], reverse=True)
    completed_orders.sort(key=lambda x: x['order_date'], reverse=True)
    
    shipping_orders_count = len(shipping_orders)
    delivered_orders_count = len(delivered_orders)
    completed_orders_count = len(completed_orders)
    
    return render_template('account/account.html', 
                          active_page='orders',
                          active_tab=active_tab,
                          shipping_orders=shipping_orders,
                          delivered_orders=delivered_orders,
                          completed_orders=completed_orders,
                          shipping_orders_count=shipping_orders_count,
                          delivered_orders_count=delivered_orders_count,
                          completed_orders_count=completed_orders_count)

@app.route('/product/details/<product_id>')
@login_required
def product_details_modal(product_id):
    product = None
    order_info = None
    
    # Get product information first
    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 11 and parts[0] == product_id:

                    main_photo_proxy = ProductImageProxy(parts[11]).display()

                    additional_photos_proxies = [
                        ProductImageProxy(photo).display() 
                        for photo in parts[12:] 
                        if photo.strip()  # Skip empty entries
                    ] if len(parts) > 12 else []
                    
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
                        'price': float(parts[9]),
                        'shipping_cost': parts[10],
                        'main_photo': main_photo_proxy,
                        'additional_photos': additional_photos_proxies,
                    }
                    break
    except FileNotFoundError:
        pass
    
    if not product:
        return "Product not found", 404
    
    # Get seller feedbacks
    seller_feedbacks = get_feedback_for_seller(product['seller'])
    
    # Check if product is in user's favorites
    is_favorited = False
    try:
        with open("databases/favorites.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 4 and parts[1] == current_user.id and parts[2] == product_id:
                    is_favorited = True
                    break
    except FileNotFoundError:
        pass
    
    # Get order information if the product is sold OR if current user has ordered it
    try:
        with open("databases/orders.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 8 and parts[2] == product_id:
                    # Check if this is relevant to current user (either as seller or buyer)
                    if parts[1] == current_user.id or product['seller'] == current_user.id:
                        order_info = {
                            'order_id': parts[0],
                            'buyer_username': parts[1],
                            'order_date': parts[3],
                            'payment_method': parts[4],
                            'amount_paid': float(parts[5]),
                            'delivery_address':parts[6],
                            'status': parts[7],
                            'delivered_date': parts[8] if parts[8] else None
                        }
                        break
    except FileNotFoundError:
        pass
    
    # Add order information to product if available
    if order_info:
        product.update({
            'order_id': order_info['order_id'],
            'buyer_username': order_info['buyer_username'],
            'order_date': order_info['order_date'],
            'payment_method': order_info['payment_method'],
            'delivery_address': order_info['delivery_address'],
            'amount_paid': order_info['amount_paid'],
            'order_status': order_info['status'],
            'delivered_date': order_info['delivered_date']
        })
    
    # Determine the context based on product status and user relationship
    context = {
        'is_seller': product['seller'] == current_user.id,
        'is_buyer': order_info and order_info['buyer_username'] == current_user.id,
        'is_sold': product['status'] == 'sold',
        'is_pending': product['status'] == 'pending',
        'is_approved': product['status'] == 'approved',
        'has_order': order_info is not None,
        'is_favorited': is_favorited
    }
    
    return render_template('account/show_details.html', 
                         product=product,
                         context=context,
                         seller_feedbacks=seller_feedbacks)

@app.route('/account/settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    if request.method == 'POST':
        # Get form data - only editable fields
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Username and email remain unchanged
        username = current_user.username
        email = current_user.email
        role = current_user.role
        
        # Handle profile image upload
        profile_image_filename = current_user.profile_image  # Keep existing image by default
        profile_image = request.files.get('profile_image')
        
        if profile_image and profile_image.filename:
            # Validate file type
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            file_extension = profile_image.filename.rsplit('.', 1)[1].lower()
            
            if file_extension not in allowed_extensions:
                flash("Invalid file type! Please upload PNG, JPG, JPEG, or GIF files only.")
                return render_template('account/account.html', active_page='settings')
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join('static/uploads/profile_images')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            profile_image_filename = f"{current_user.id}_{int(time.time())}_profile.{file_extension}"
            
            # Save the file
            try:
                profile_image.save(os.path.join(upload_dir, profile_image_filename))
                
                # Delete old profile image if it exists and is not default
                if (current_user.profile_image and 
                    current_user.profile_image != '-' and 
                    current_user.profile_image != profile_image_filename):
                    old_image_path = os.path.join(upload_dir, current_user.profile_image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
            except Exception as e:
                flash("Error uploading profile image. Please try again.")
                return render_template('account/account.html', active_page='settings')
        
        # Handle profile image removal
        if request.form.get('remove_image') == 'true':
            # Delete current profile image if it exists
            if (current_user.profile_image and 
                current_user.profile_image != '-'):
                upload_dir = os.path.join('static/uploads/profile_images')
                old_image_path = os.path.join(upload_dir, current_user.profile_image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            profile_image_filename = '-'
        
        # Update user data in file (username and email remain unchanged)
        updated_lines = []
        user_found = False
        
        try:
            with open("databases/member_detail.txt", "r") as file:
                for line in file:
                    data = line.strip().split('||')
                    if len(data) >= 6 and data[0] == current_user.id:
                        # Update current user's record - keep original username and email
                        updated_line = f"{username}||{phone}||{email}||{data[3]}||{address}||{profile_image_filename}||{role}\n"
                        updated_lines.append(updated_line)
                        user_found = True
                    else:
                        updated_lines.append(line)
            
            if user_found:
                # Write updated data back to file
                with open("databases/member_detail.txt", "w") as file:
                    file.writelines(updated_lines)
                
                # Update current user object (only editable fields)
                current_user.phone = phone
                current_user.address = address
                current_user.profile_image = profile_image_filename
                
                flash("Profile updated successfully!")
            else:
                flash("Error updating profile. User not found.")
                
        except Exception as e:
            flash("Error updating profile. Please try again.")
        
        return redirect(url_for('account_settings'))
    
    # GET request - display the form with current user data
    user_data = {
        'username': current_user.username,
        'email': current_user.email,
        'phone': current_user.phone if current_user.phone != '-' else '',
        'address': current_user.address if current_user.address != '-' else '',
        'profile_image': current_user.profile_image if current_user.profile_image != '-' else None
    }
    
    return render_template('account/account.html', 
                         active_page='settings', 
                         user_data=user_data)

@app.route('/delivered_order/<order_id>', methods=['POST'])
@login_required
def delivered_order(order_id):

    updated_lines = []
    order_found = False
    
    try:
        with open("databases/orders.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 8 and parts[0] == order_id:
                    # Update status to 'completed' and set delivered date
                    parts[7] = 'delivered'
                    parts[8] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    updated_lines.append('||'.join(parts) + '\n')
                    order_found = True
                else:
                    updated_lines.append(line)
        
        if order_found:
            with open("databases/orders.txt", "w") as file:
                file.writelines(updated_lines)
            
            flash("Order marked as delivered!", "success")
        else:
            flash("Order not found", "error")
            
    except Exception as e:
        flash("Error updating order status", "error")
    
    return redirect(url_for('account_orders', tab='shipping'))

#William function feedback 
@app.route('/complete_order/<order_id>', methods=['POST'])
@login_required
def complete_order(order_id):
    # Update the order status in orders.txt
    updated_lines = []
    order_found = False
    
    try:
        with open("databases/orders.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 8 and parts[0] == order_id:
                    # Update status to 'completed' and set delivered date
                    parts[7] = 'completed'
                    parts[8] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    updated_lines.append('||'.join(parts) + '\n')
                    order_found = True
                else:
                    updated_lines.append(line)
        
        if order_found:
            with open("databases/orders.txt", "w") as file:
                file.writelines(updated_lines)
            
            flash("Order marked as completed!", "success")
        else:
            flash("Order not found", "error")
            
    except Exception as e:
        flash("Error updating order status", "error")
    
    return redirect(url_for('account_orders', tab='shipping'))

@app.route('/leave_feedback/<order_id>')
@login_required
def leave_feedback(order_id):
    order = None
    try:
        with open("databases/orders.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 8 and parts[0] == order_id:
                    # Check if this is relevant to current user (either as seller or buyer)
                    if parts[1] == current_user.id:
                        order = {
                            'order_id': parts[0],
                            'buyer_username': parts[1],
                            'order_date': parts[3],
                            'payment_method': parts[4],
                            'amount_paid': float(parts[5]),
                            'delivery_address':parts[6],
                            'status': parts[7],
                            'delivered_date': parts[8] if parts[8] else None
                        }
                        break
    except FileNotFoundError:
        pass

    return render_template('account/leave_feedback.html', order = order)

@app.route('/submit_feedback/<order_id>', methods=['POST'])
@login_required
def submit_feedback(order_id):
    rating = request.form.get('rating')
    feedback_text = request.form.get('feedback')
    
    if not rating or not feedback_text:
        flash("Please provide both rating and feedback", "error")
        return redirect(url_for('account_orders', tab='completed'))
    
    os.makedirs("databases", exist_ok=True)
    
    order_info = None
    try:
        with open("databases/orders.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 9 and parts[0] == order_id:  # 修复：确保有足够的字段
                    order_info = {
                        'order_id': parts[0],
                        'buyer_username': parts[1],
                        'product_id': parts[2],
                        'seller_username': None
                    }
                    break
    except FileNotFoundError:
        flash("Orders file not found", "error")
        return redirect(url_for('account_orders', tab='completed'))
    
    if not order_info:
        flash("Order not found", "error")
        return redirect(url_for('account_orders', tab='completed'))
    
    # 从产品信息获取卖家用户名
    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 11 and parts[0] == order_info['product_id']:
                    order_info['seller_username'] = parts[1]
                    break
    except FileNotFoundError:
        flash("Products file not found", "error")
        return redirect(url_for('account_orders', tab='completed'))
    
    if not order_info['seller_username']:
        flash("Product seller not found", "error")
        return redirect(url_for('account_orders', tab='completed'))
    
    feedback_id = 1
    try:
        with open("databases/feedback.txt", "r") as file:
            lines = file.readlines()
            if lines:
                for line in reversed(lines):  # 从后往前读，找到最大ID
                    parts = line.strip().split('||')
                    if parts and parts[0].isdigit():
                        feedback_id = int(parts[0]) + 1
                        break
    except FileNotFoundError:
        pass
    
    # format：feedback_id||order_id||product_id||seller_username||buyer_username||rating||comment||timestamp
    feedback_data = [
        str(feedback_id),
        order_info['order_id'],
        order_info['product_id'],
        order_info['seller_username'],
        current_user.id,  # buyer_username
        rating,
        feedback_text,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ]
    
    try:
        with open("databases/feedback.txt", "a") as file:
            file.write('||'.join(feedback_data) + '\n')
        flash("Thank you for your feedback!", "success")
        print(f"Feedback saved: {feedback_data}")  
    except Exception as e:
        flash(f"Error submitting feedback: {str(e)}", "error")
        print(f"Error saving feedback: {e}") 
    
    return redirect(url_for('account_orders', tab='completed'))


@app.route('/debug/feedback')
@login_required
def debug_feedback():
    feedbacks = []
    try:
        with open("databases/feedback.txt", "r") as file:
            for line_num, line in enumerate(file, 1):
                parts = line.strip().split('||')
                feedbacks.append({
                    'line_number': line_num,
                    'raw_data': line.strip(),
                    'parsed_parts': parts,
                    'parts_count': len(parts)
                })
    except FileNotFoundError:
        return "Feedback file not found"
    
    return f"<pre>{feedbacks}</pre>"

@app.route('/get_seller_feedback')
def get_seller_feedback():
    seller = request.args.get('seller')
    if not seller:
        return jsonify({'error': 'Seller username is required'}), 400
    
    feedbacks = []
    try:
        with open("databases/feedback.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 8 and parts[3] == seller:
                    try:
                        feedbacks.append({
                            'buyer_username': parts[4],
                            'rating': int(parts[5]),
                            'comment': parts[6],
                            'timestamp': parts[7]
                        })
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing feedback line: {line}. Error: {e}")
                        continue
    except FileNotFoundError:
        return jsonify({'error': 'Feedback file not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error reading feedback: {str(e)}'}), 500
    
    return jsonify({
        'seller': seller,
        'feedbacks': feedbacks,
        'count': len(feedbacks)
    })


#yy admin user management start
@app.route('/admin/user_management')
@login_required
def user_management():
    active_tab = request.args.get('tab', 'listing')
    role_filter = request.args.get('role', '').lower()
    search_query = request.args.get('search', '').lower()
    user_profile_image = current_user.profile_image if current_user.profile_image != '-' else None

    users = []
    filtered_users = []

    try:
        with open("databases/member_detail.txt", "r") as file:
            for line in file:
                parts = line.strip().split("||")
                if len(parts) >= 7:
                    user = {
                        'username': parts[0],
                        'phone': parts[1],
                        'email': parts[2],
                        'address': parts[4],
                        'role': parts[6]
                    }

                    users.append(user)
    except FileNotFoundError:
        pass

    # Total users (before filtering)
    total_user_count = len(users)

    # Filter
    for user in users:
        matches_role = (role_filter == '' or user['role'] == role_filter)
        matches_search = (search_query in user['username'].lower() or
                          search_query in user['phone'] or
                          search_query in user['email'].lower() or
                          search_query in user['address'].lower() or
                          search_query in user['role'].lower())

        if matches_role and matches_search:
            filtered_users.append(user)

    filtered_user_count = len(filtered_users)

    return render_template('admin/admin_page.html',
                           active_page='user_management',
                           active_tab=active_tab,
                           user_profile_image=user_profile_image,
                           users=filtered_users,
                           filtered_user_count=filtered_user_count,
                           total_user_count=total_user_count)
#yy admin user management end

#yy admin user management edit user start
@app.route('/admin/user_management/edit/<username>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(username):
    user = None

    # Read user data from the text file
    try:
        with open("databases/member_detail.txt", "r") as file:
            for line in file:
                data = line.strip().split("||")
                if len(data) >= 6 and data[0] == username:
                    user = type("User", (object,), {})()  # create simple user-like object
                    user.id = data[0]
                    user.username = data[0]
                    user.phone = data[1]
                    user.email = data[2]
                    user.address = data[4]
                    user.profile_image = data[5]
                    user.role = data[6]
                    break
    except Exception as e:
        flash("Error loading user data.")

    if not user:
        flash("User not found.")
        return redirect(url_for('admin_user_list'))  # or another admin page

    if request.method == 'POST':
        phone = request.form.get('phone')
        address = request.form.get('address')
        role = request.form.get('role')

        # Convert empty strings to '-' before saving
        phone = phone.strip() if phone and phone.strip() else '-'
        address = address.strip() if address and address.strip() else '-'

        # Profile image processing
        profile_image_filename = user.profile_image
        profile_image = request.files.get('profile_image')

        if profile_image and profile_image.filename:
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            file_extension = profile_image.filename.rsplit('.', 1)[1].lower()

            if file_extension not in allowed_extensions:
                flash("Invalid file type! Please upload PNG, JPG, JPEG, or GIF files only.")
                return render_template('admin/admin_edit_user.html', user_data=user)

            upload_dir = os.path.join('static/uploads/profile_images')
            os.makedirs(upload_dir, exist_ok=True)

            profile_image_filename = f"{user.id}_{int(time.time())}_profile.{file_extension}"

            try:
                profile_image.save(os.path.join(upload_dir, profile_image_filename))

                if user.profile_image and user.profile_image != '-' and user.profile_image != profile_image_filename:
                    old_image_path = os.path.join(upload_dir, user.profile_image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
            except Exception as e:
                flash("Error uploading profile image. Please try again.")
                return render_template('admin/admin_edit_user.html', user_data=user)

        if request.form.get('remove_image') == 'true':
            if user.profile_image and user.profile_image != '-':
                upload_dir = os.path.join('static/uploads/profile_images')
                old_image_path = os.path.join(upload_dir, user.profile_image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            profile_image_filename = '-'

        updated_lines = []
        user_found = False

        try:
            with open("databases/member_detail.txt", "r") as file:
                for line in file:
                    data = line.strip().split('||')
                    if len(data) >= 6 and data[0] == user.id:
                        updated_line = f"{user.username}||{phone}||{user.email}||{data[3]}||{address}||{profile_image_filename}||{role}\n"
                        updated_lines.append(updated_line)
                        user_found = True
                    else:
                        updated_lines.append(line)

            if user_found:
                with open("databases/member_detail.txt", "w") as file:
                    file.writelines(updated_lines)

                user.phone = phone
                user.address = address
                user.profile_image = profile_image_filename
                user.role = role

                flash("Profile updated successfully!")
            else:
                flash("Error updating user. User not found.")

        except Exception as e:
            flash("Error updating user profile. Please try again.")

        return redirect(url_for('user_management', username=user.username))

    # GET method: render user data
    user_data = {
        'username': user.username,
        'email': user.email,
        'phone': user.phone if user.phone != '-' else '',
        'address': user.address if user.address != '-' else '',
        'profile_image': user.profile_image if user.profile_image != '-' else None,
        'role': user.role if user.role != '-' else 'user'
    }
    
    return render_template('admin/admin_page.html', 
                           active_page='admin_edit_user',
                           user_data=user_data)
#yy admin user management edit user end

#yy admin user management delete user start
@app.route('/admin/user_management/delete/<username>', methods=['GET'])
@login_required
def admin_delete_user(username):
    lines = []
    user_deleted = False
    try:
        with open("databases/member_detail.txt", "r") as file:
            lines = file.readlines()

        new_lines = []
        for line in lines:
            data = line.strip().split("||")
            if len(data) >= 6 and data[0] != username:
                new_lines.append(line)
            else:
                user_deleted = True
                # Delete profile image if exists
                if data[5] and data[5] != "-":
                    image_path = os.path.join('static/uploads/profile_images', data[5])
                    if os.path.exists(image_path):
                        os.remove(image_path)

        with open("databases/member_detail.txt", "w") as file:
            file.writelines(new_lines)

    except Exception as e:
        flash("Error deleting user.")

    if user_deleted:
        flash(f"User '{username}' has been deleted.")
    else:
        flash("User not found or could not be deleted.")

    return redirect(url_for('user_management'))
#yy admin user management delete user end

#yy admin user management add user start
@app.route('/admin/user_management/add', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    username_exists = False
    password_mismatch = False
    success = False

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        phone = request.form.get('phone', '').strip() or '-'
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        address = request.form.get('address', '').strip() or '-'
        role = request.form.get('role', 'user').strip()

        # Check for existing username
        if username:
            try:
                with open("databases/member_detail.txt", "r") as f:
                    for line in f:
                        parts = line.strip().split("||")
                        if len(parts) > 0 and parts[0] == username:
                            username_exists = True
                            flash("Username already exists!")
                            return redirect(url_for('admin_add_user'))
            except FileNotFoundError:
                pass  # If file doesn't exist, continue as if no users exist

        # Check for password mismatch
        if password != confirm:
            password_mismatch = True
            flash("Password doesn't match!")
            return redirect(url_for('admin_add_user'))

        # Proceed only if no errors
        if not username_exists and not password_mismatch:
            hashed_password = generate_password_hash(password)
            with open("databases/member_detail.txt", "a") as f:
                f.write(f"{username}||{phone}||{email}||{hashed_password}||{address}||-||{role}\n")
            success = True

        return redirect(url_for('user_management'))

    return render_template(
        'admin/admin_page.html',
        active_page='admin_add_user'
    )
#yy admin user management add user end



# yy admin order management start
@app.route('/admin/order_management')
@login_required
def order_management():
    status_filter = request.args.get('status', '').lower()
    search_query = request.args.get('search', '').lower()
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')

    # Convert string to date object
    start_date = None
    end_date = None
    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError:
        pass  # Ignore invalid date input

    # Load product titles into a dictionary
    product_titles = {}
    try:
        with open("databases/products.txt", "r") as pfile:
            for line in pfile:
                parts = line.strip().split("||")
                if len(parts) >= 5:
                    product_id = parts[0].strip()
                    title = parts[4].strip()
                    product_titles[product_id] = title
    except FileNotFoundError:
        pass

    orders = []
    filtered_orders = []

    try:
        with open("databases/orders.txt", "r") as file:
            for line in file:
                parts = line.strip().split("||")
                if len(parts) >= 9:
                    order_time_str = parts[3].strip()
                    try:
                        order_time = datetime.strptime(order_time_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        order_time = None

                    product_id = parts[2].strip()
                    product_title = product_titles.get(product_id, f"Unknown ({product_id})")

                    order = {
                        'order_id': parts[0],
                        'buyer_username': parts[1],
                        'product_id': parts[2],
                        'product_title': product_title,
                        'order_time': order_time_str,
                        'order_time_obj': order_time,  # keep parsed date for comparison
                        'payment_method': parts[4],
                        'payment_amount': parts[5],
                        'delivery_address': parts[6],
                        'status': parts[7].strip().lower(),
                        'delivered_date': parts[8]
                    }
                    orders.append(order)
    except FileNotFoundError:
        pass

    # Apply search and status filter
    for order in orders:
        matches_search = (
            search_query in order['buyer_username'].lower() or
            search_query in order['product_id'].lower() or
            search_query in order['product_title'].lower() or
            search_query in order['order_time'].lower() or
            search_query in order['payment_method'].lower() or
            search_query in order['payment_amount'].lower() or
            search_query in order['delivery_address'].lower() or
            search_query in order['status'].lower() or
            search_query in order['delivered_date'].lower()
        )

        matches_status = (status_filter == '' or order['status'].lower() == status_filter)

        matches_date = True
        if order['order_time_obj']:
            if start_date and order['order_time_obj'] < start_date:
                matches_date = False
            if end_date and order['order_time_obj'] > end_date:
                matches_date = False

        if matches_search and matches_status and matches_date:
            filtered_orders.append(order)

    return render_template('admin/admin_page.html',
                            active_page='order_management',
                            orders=filtered_orders,
                            total_order_count=len(orders),
                            filtered_order_count=len(filtered_orders)
                            )
# yy admin order management end

# yy admin view product start
@app.route('/admin/admin_view_products')
@login_required
def admin_view_products():
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '').lower()

    products = []
    with open('databases/products.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parts = [p.strip() for p in line.strip().split('||')]
            if len(parts) < 13:
                continue  # Skip malformed lines

            main_photo_proxy = ProductImageProxy(parts[11]).display()
                
            additional_photos_proxies = [
                ProductImageProxy(photo).display() 
                for photo in parts[12:] 
                if photo.strip()  # Skip empty entries
            ] if len(parts) > 12 else []    

            product = {
                'product_id': parts[0],
                'seller_username': parts[1],
                'category': parts[2],
                'status': parts[3],
                'title': parts[4],
                'brand': parts[5],
                'model': parts[6],
                'year': parts[7],
                'description': parts[8],
                'price': parts[9],
                'shipping_cost': parts[10],
                'main_photo_filename': main_photo_proxy,
                'additional_photo_filenames': additional_photos_proxies
            }
            

            # Apply filters
            if category_filter and product['category'] != category_filter:
                continue
            if status_filter and product['status'] != status_filter:
                continue

            # Apply search (case insensitive across selected fields)
            if search_query and not (
                search_query in product['title'].lower() or
                search_query in product['brand'].lower() or
                search_query in product['model'].lower() or
                search_query in product['seller_username'].lower()
            ):
                continue

            products.append(product)

    total_count = sum(1 for _ in open('databases/products.txt', 'r', encoding='utf-8'))
    filtered_count = len(products)

    return render_template('admin/admin_page.html',
                           active_page='admin_view_products',
                           products=products,
                           total_product_count=total_count,
                           filtered_product_count=filtered_count)

# yy admin view product end

# yy admin view product modal window start
@app.route('/product/details/<product_id>')
@login_required
def product_details_partial(product_id):
    product = None
    with open("databases/products.txt", "r") as file:
        for line in file:
            parts = line.strip().split('||')
            if parts[0] == product_id:
                main_photo_proxy = ProductImageProxy(parts[11]).display()
                product = {
                    'id': parts[0],
                    'title': parts[4],
                    'brand': parts[5],
                    'model': parts[6],
                    'year': parts[7],
                    'description': parts[8].strip('"'),
                    'price': float(parts[9]) if parts[9].replace('.', '', 1).isdigit() else 0,
                    'shipping_cost': float(parts[10]) if parts[10].replace('.', '', 1).isdigit() else 0,
                    'main_photo': main_photo_proxy,
                    'category': parts[2],
                    'status': parts[3],
                    'seller': parts[1]
                }
                break
    if not product:
        return "<p>Product not found</p>"

    return render_template("partials/product_modal_content.html", product=product)
# yy admin view product modal window end


# yy admin_product_upload_approval start
@app.route('/admin/admin_product_upload_approval')
@login_required
def admin_product_upload_approval():
    active_tab = request.args.get('tab', 'pending')

    # Initialize lists for different statuses
    pending_products = []
    approved_products = []
    rejected_products = []
    sold_products = []

    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 12:
                    status = parts[3].lower()
                    
                    main_photo_proxy = ProductImageProxy(parts[11]).display()

                    additional_photos_proxies = [
                        ProductImageProxy(photo).display() 
                        for photo in parts[12:] 
                        if photo.strip()  # Skip empty entries
                    ] if len(parts) > 12 else []   
                    
                    product = {
                        'id': parts[0],
                        'seller': parts[1],
                        'category': parts[2],
                        'status': status,
                        'title': parts[4],
                        'brand': parts[5],
                        'model': parts[6],
                        'year': parts[7],
                        'description': parts[8].strip('"'),
                        'price': parts[9],
                        'shipping_cost': parts[10],
                        'main_photo': main_photo_proxy,
                        'additional_photos': additional_photos_proxies
                    }

                    if status == 'pending':
                        pending_products.append(product)
                    elif status == 'approved':
                        approved_products.append(product)
                    elif status == 'rejected':
                        rejected_products.append(product)
                    elif status == 'sold':
                        sold_products.append(product)

    except FileNotFoundError:
        pass

    # Count for each category
    pending_products_count = len(pending_products)
    approved_products_count = len(approved_products)
    rejected_products_count = len(rejected_products)
    sold_products_count = len(sold_products)

    return render_template('admin/admin_page.html',
                           active_page='admin_product_upload_approval',
                           active_tab=active_tab,
                           pending_products=pending_products,
                           pending_products_count=pending_products_count,
                           approved_products=approved_products,
                           approved_products_count=approved_products_count,
                           rejected_products=rejected_products,
                           rejected_products_count=rejected_products_count,
                           sold_products=sold_products,
                           sold_products_count=sold_products_count)
# yy admin_product_upload_approval end

# yy update_product_status start
@app.route('/admin/update_product_status', methods=['POST'])
@login_required
def update_product_status():
    product_id = request.form.get('product_id')
    new_status = request.form.get('status')
    
    updated_lines = []
    product_updated = False
    seller_id = None

    try:
        with open("databases/products.txt", "r") as file:
            for line in file:
                parts = line.strip().split('||')
                if len(parts) >= 12 and parts[0] == product_id:
                    seller_id = parts[1]  # Get seller ID before updating
                    parts[3] = new_status  # update status
                    product_updated = True
                    updated_lines.append('||'.join(parts) + '\n')
                else:
                    updated_lines.append(line)

        if product_updated:
            with open("databases/products.txt", "w") as file:
                file.writelines(updated_lines)

            # NOTIFY ALL OBSERVERS
            product_status_subject.notify(product_id, new_status, seller_id)
            
            return jsonify({'success': True, 'message': 'Status updated'})
        else:
            return jsonify({'success': False, 'message': 'Product not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500 

  
# yy update_product_status end

# yy admin dashboard start
@app.route('/admin/admin_dashboard')
@login_required
def admin_dashboard():
    # Initialize metrics containers
    metrics = {
        "profit": 0,          # sum of completed order payments
        "customer": 0,        # count users with role 'user'
        "orders": 0,          # count all orders
        "request": 0          # count pending products
    }

    # Initialize data structures
    raw_orders = []
    products_dict = {}
    user_details = []
    status_counts = {
        "pending": 0,
        "approved": 0,
        "rejected": 0,
        "sold": 0
    }
    category_counts = {}

    # Get view type from request (default to monthly)
    view_type = request.args.get('view', 'monthly')

    # 1. Load User Data
    try:
        with open('databases/member_detail.txt', 'r') as f:
            for line in f:
                parts = line.strip().split("||")
                if len(parts) >= 7:
                    user_details.append({
                        "username": parts[0],
                        "phone": parts[1],
                        "email": parts[2],
                        "role": parts[6]
                    })
                    if parts[6] == 'user':
                        metrics["customer"] += 1
    except FileNotFoundError:
        flash('Member data file not found', 'error')

    # 2. Load Product Data
    try:
        with open('databases/products.txt', 'r') as f:
            for line in f:
                parts = line.strip().split("||")
                if len(parts) >= 5:
                    product_id = parts[0].strip()
                    category = parts[2].strip().lower()
                    status = parts[3].strip().lower()
                    
                    products_dict[product_id] = {
                        'title': parts[4].strip(),
                        'category': category,
                        'status': status
                    }

                    # Count by status
                    if status in status_counts:
                        status_counts[status] += 1
                    
                    # Count pending products
                    if status == 'pending':
                        metrics["request"] += 1
                    
                    # Count by category
                    if category in ['smartphone', 'laptop', 'tablet', 'camera', 'audio']:
                        category_counts[category] = category_counts.get(category, 0) + 1
    except FileNotFoundError:
        flash('Product data file not found', 'error')

    # 3. Load Order Data
    try:
        with open('databases/orders.txt', 'r') as f:
            for line in f:
                parts = line.strip().split("||")
                if len(parts) >= 8:
                    metrics["orders"] += 1
                    
                    # Calculate profit from completed orders
                    if "complete" in parts[7].lower():
                        try:
                            metrics["profit"] += float(parts[5].strip())
                        except (ValueError, IndexError):
                            pass
                    
                    # Parse order time
                    try:
                        order_time = datetime.strptime(parts[3], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
                    
                    # Get product title
                    product_id = parts[2].strip()
                    product_title = products_dict.get(product_id, {}).get('title', 'Unknown Product')
                    
                    raw_orders.append({
                        'order_id': parts[0],
                        'buyer': parts[1],
                        'product_id': product_id,
                        'product_title': product_title,
                        'order_time_str': parts[3],
                        'order_time_obj': order_time,
                        'payment_method': parts[4],
                        'amount_paid': parts[5],
                        'status': parts[7].lower(),
                        'delivered_date': parts[8] if len(parts) > 8 else None
                    })

    except FileNotFoundError:
        flash('Order data file not found', 'error')

    # STRATEGY PATTERN IMPLEMENTATION FOR ORDER DATA
    order_context = OrderContext()
    
    # Set strategy based on view type
    if view_type == 'weekly':
        order_context.set_strategy(WeeklyOrderStrategy())
    elif view_type == 'yearly':
        order_context.set_strategy(YearlyOrderStrategy())
    else:  # default monthly
        order_context.set_strategy(MonthlyOrderStrategy())
    
    # Process order data using selected strategy
    order_chart_data = order_context.get_order_data(raw_orders)

    # Prepare product category data for pie chart
    category_labels = []
    category_data = []
    colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']
    
    for i, (category, count) in enumerate(sorted(category_counts.items())):
        category_labels.append(category.capitalize())
        category_data.append(count)
        if i >= len(colors):
            colors.append(colors[i % len(colors)])

    # Prepare product status data for doughnut chart
    status_labels = ['Pending', 'Approved', 'Rejected', 'Sold']
    status_data = [
        status_counts['pending'],
        status_counts['approved'],
        status_counts['rejected'],
        status_counts['sold']
    ]
    status_colors = ['#f59e0b', '#10b981', '#ef4444', '#3b82f6']

    # Prepare product chart data
    product_chart_data = {
        "categories": {
            "labels": category_labels,
            "data": category_data,
            "colors": colors
        },
        "status": {
            "labels": status_labels,
            "data": status_data,
            "colors": status_colors
        }
    }

    # Load feedback data for dashboard
    feedback_data = []
    try:
        with open('databases/feedback.txt', 'r') as file:
            for line in file:
                parts = [part.strip() for part in line.split('||')]
                if len(parts) >= 8:
                    feedback_data.append({
                        'rating': int(parts[5]),
                        'comment': parts[6],
                        'timestamp': parts[7]
                    })
    except FileNotFoundError:
        pass

    # Calculate feedback statistics
    feedback_stats = {
        'total': len(feedback_data),
        'positive': sum(1 for f in feedback_data if f['rating'] >= 4),
        'negative': len(feedback_data) - sum(1 for f in feedback_data if f['rating'] >= 4),
        'average': round(sum(f['rating'] for f in feedback_data) / len(feedback_data), 1) if feedback_data else 0
    }

    return render_template('admin/admin_page.html',
                        active_page='admin_dashboard',
                        order_chart_data=order_chart_data,
                        product_chart_data=product_chart_data,
                        user_details=user_details,
                        order_details = raw_orders,
                        metrics=metrics,
                        feedback_data=feedback_data,
                        current_view=view_type)

#yy admin profile start
@app.route('/admin/admin_profile/<username>', methods=['GET', 'POST'])
@login_required
def admin_profile(username):
    user = None

    # Read user data from the text file
    try:
        with open("databases/member_detail.txt", "r") as file:
            for line in file:
                data = line.strip().split("||")
                if len(data) >= 6 and data[0] == username:
                    user = type("User", (object,), {})()  # create simple user-like object
                    user.id = data[0]
                    user.username = data[0]
                    user.phone = data[1]
                    user.email = data[2]
                    user.address = data[4]
                    user.profile_image = data[5]
                    user.role = data[6]
                    break
    except Exception as e:
        flash("Error loading user data.")

    if not user:
        flash("User not found.")
        return redirect(url_for('admin_user_list'))  # or another admin page

    if request.method == 'POST':
        phone = request.form.get('phone')
        address = request.form.get('address')
        role = request.form.get('role')

        # Convert empty strings to '-' before saving
        phone = phone.strip() if phone and phone.strip() else '-'
        address = address.strip() if address and address.strip() else '-'

        # Profile image processing
        profile_image_filename = user.profile_image
        profile_image = request.files.get('profile_image')

        if profile_image and profile_image.filename:
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            file_extension = profile_image.filename.rsplit('.', 1)[1].lower()

            if file_extension not in allowed_extensions:
                flash("Invalid file type! Please upload PNG, JPG, JPEG, or GIF files only.")
                return render_template('admin/admin_profile.html', user_data=user)

            upload_dir = os.path.join('static/uploads/profile_images')
            os.makedirs(upload_dir, exist_ok=True)

            profile_image_filename = f"{user.id}_{int(time.time())}_profile.{file_extension}"

            try:
                profile_image.save(os.path.join(upload_dir, profile_image_filename))

                if user.profile_image and user.profile_image != '-' and user.profile_image != profile_image_filename:
                    old_image_path = os.path.join(upload_dir, user.profile_image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
            except Exception as e:
                flash("Error uploading profile image. Please try again.")
                return render_template('admin/admin_profile.html', user_data=user)

        if request.form.get('remove_image') == 'true':
            if user.profile_image and user.profile_image != '-':
                upload_dir = os.path.join('static/uploads/profile_images')
                old_image_path = os.path.join(upload_dir, user.profile_image)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            profile_image_filename = '-'

        updated_lines = []
        user_found = False

        try:
            with open("databases/member_detail.txt", "r") as file:
                for line in file:
                    data = line.strip().split('||')
                    if len(data) >= 6 and data[0] == user.id:
                        updated_line = f"{user.username}||{phone}||{user.email}||{data[3]}||{address}||{profile_image_filename}||{role}\n"
                        updated_lines.append(updated_line)
                        user_found = True
                    else:
                        updated_lines.append(line)

            if user_found:
                with open("databases/member_detail.txt", "w") as file:
                    file.writelines(updated_lines)

                user.phone = phone
                user.address = address
                user.profile_image = profile_image_filename
                user.role = role

                flash("User profile updated successfully!")
            else:
                flash("Error updating user. User not found.")

        except Exception as e:
            flash("Error updating user profile. Please try again.")

        return redirect(url_for('admin_profile', username=user.username))

    # GET method: render user data
    user_data = {
        'username': user.username,
        'email': user.email,
        'phone': user.phone if user.phone != '-' else '',
        'address': user.address if user.address != '-' else '',
        'profile_image': user.profile_image if user.profile_image != '-' else None,
        'role': user.role if user.role != '-' else 'user'
    }
    
    return render_template('admin/admin_page.html', 
                           active_page='admin_profile',
                           user_data=user_data)
#yy admin profile end
    
if __name__ == '__main__':
    app.run(debug=True)
    
