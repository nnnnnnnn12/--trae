from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Shop, Product, Order, OrderItem, Review
import os
import random
import urllib.parse

app = Flask(__name__)

# Use environment variables for production
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or \
    'sqlite:///' + os.path.join(basedir, 'instance', 'delivery_v4.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-placeholder-123')

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'merchant':
            return redirect(url_for('merchant_dashboard'))
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'merchant':
                return redirect(url_for('merchant_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'customer')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            user = User(username=username, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # If merchant, create a dummy shop for them immediately
            if role == 'merchant':
                shop = Shop(name=f"{username}'s Shop", description="New shop", owner=user)
                db.session.add(shop)
                db.session.commit()
                
            login_user(user)
            if role == 'merchant':
                return redirect(url_for('merchant_dashboard'))
            return redirect(url_for('index'))
            
    return render_template('register.html')

# --- Public Routes ---
@app.route('/')
def index():
    # Only show active shops
    shops = Shop.query.filter_by(is_active=True).all()
    return render_template('index.html', shops=shops)

@app.route('/shop/<int:shop_id>')
def shop_detail(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if not shop.is_active:
        abort(404)
    # Filter only active products
    active_products = [p for p in shop.products if p.is_active]
    return render_template('shop.html', shop=shop, products=active_products)

@app.route('/shop/<int:shop_id>/reviews')
def shop_reviews(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    if not shop.is_active:
        abort(404)
    return render_template('reviews.html', shop=shop)

@app.route('/order/<int:shop_id>', methods=['POST'])
@login_required
def place_order(shop_id):
    product_ids = request.form.getlist('product_id')
    if not product_ids:
        return redirect(url_for('shop_detail', shop_id=shop_id))
        
    order = Order(user_id=current_user.id, shop_id=shop_id, status='Pending')
    db.session.add(order)
    db.session.commit()
    
    for pid in product_ids:
        item = OrderItem(order_id=order.id, product_id=int(pid), quantity=1)
        db.session.add(item)
    
    db.session.commit()
    return redirect(url_for('user_profile'))

@app.route('/user/profile')
@login_required
def user_profile():
    return render_template('user.html', user=current_user)

@app.route('/order/<int:order_id>/review', methods=['POST'])
@login_required
def add_review(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    
    # Check if order is completed
    if order.status != 'Completed':
        flash('只有已完成的订单才能评价')
        return redirect(url_for('user_profile'))

    content = request.form.get('content')
    rating = request.form.get('rating')
    
    if content and rating:
        review = Review(user_id=current_user.id, shop_id=order.shop_id, order_id=order.id, content=content, rating=int(rating))
        db.session.add(review)
        db.session.commit()
        flash('评价成功！')
        
    return redirect(url_for('user_profile'))

@app.route('/order/<int:order_id>/refund', methods=['POST'])
@login_required
def refund_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    
    if order.status == 'Pending':
        order.status = 'Refunded'
        db.session.commit()
        flash('退款成功！')
    else:
        flash('当前订单状态无法退款')
        
    return redirect(url_for('user_profile'))

@app.route('/order/<int:order_id>/complain', methods=['POST'])
@login_required
def complain_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        abort(403)
    
    if order.status != 'Complained':
        order.status = 'Complained'
        shop = order.shop
        shop.complaint_count += 1
        
        # Check if shop should be deactivated
        if shop.complaint_count >= 3:
            shop.is_active = False
            flash(f'投诉成功！该店铺累计投诉已达{shop.complaint_count}次，已被注销。')
        else:
            flash(f'投诉成功！该店铺累计投诉次数：{shop.complaint_count}')
            
        db.session.commit()
    else:
        flash('该订单已投诉过')
        
    return redirect(url_for('user_profile'))

# --- Merchant Routes ---
@app.route('/merchant/dashboard')
@login_required
def merchant_dashboard():
    if current_user.role != 'merchant':
        abort(403)
    
    shop = current_user.shop
    if not shop:
        return "No shop assigned to this merchant", 404
        
    # Stats
    orders = Order.query.filter_by(shop_id=shop.id).all()
    total_orders = len(orders)
    pending_orders = len([o for o in orders if o.status == 'Pending'])
    
    # Calculate revenue
    revenue = 0
    for order in orders:
        for item in order.items:
            revenue += item.product.price * item.quantity
            
    return render_template('merchant/dashboard.html', shop=shop, orders=orders, 
                           total_orders=total_orders, pending_orders=pending_orders, revenue=revenue)

@app.route('/merchant/products')
@login_required
def merchant_products():
    if current_user.role != 'merchant':
        abort(403)
    shop = current_user.shop
    return render_template('merchant/products.html', shop=shop)

@app.route('/merchant/product/add', methods=['POST'])
@login_required
def add_product():
    if current_user.role != 'merchant':
        abort(403)
        
    name = request.form.get('name')
    price = request.form.get('price')
    image_url = request.form.get('image_url')
    
    if not image_url:
        # Default placeholder if empty
        image_url = f"https://placehold.co/400x300?text={name}"
        
    if name and price:
        product = Product(name=name, price=float(price), image_url=image_url, shop_id=current_user.shop.id)
        db.session.add(product)
        db.session.commit()
        
    return redirect(url_for('merchant_products'))

@app.route('/merchant/product/<int:product_id>/toggle', methods=['POST'])
@login_required
def toggle_product(product_id):
    if current_user.role != 'merchant':
        abort(403)
        
    product = Product.query.get_or_404(product_id)
    if product.shop_id != current_user.shop.id:
        abort(403)
        
    product.is_active = not product.is_active
    db.session.commit()
    return redirect(url_for('merchant_products'))

@app.route('/merchant/order/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_order(order_id):
    if current_user.role != 'merchant':
        abort(403)
    
    order = Order.query.get_or_404(order_id)
    if order.shop_id != current_user.shop.id:
        abort(403)
        
    order.status = 'Completed'
    db.session.commit()
    return redirect(url_for('merchant_dashboard'))

# --- Init Data ---
def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.first():
            print("Initializing dummy data...")
            
            # Create Customer
            customer = User(username='customer', role='customer')
            customer.set_password('123456')
            db.session.add(customer)
            
            # Create 20+ Merchants and Shops
            shop_data = [
                ('Pizza', ['Margherita', 'Pepperoni', 'Hawaiian', 'Veggie']),
                ('Burger', ['Cheeseburger', 'Bacon Burger', 'Chicken Burger', 'Fries']),
                ('Sushi', ['Salmon Roll', 'Tuna Nigiri', 'California Roll', 'Miso Soup']),
                ('Chinese', ['Kung Pao Chicken', 'Dumplings', 'Fried Rice', 'Noodles']),
                ('Indian', ['Butter Chicken', 'Naan', 'Samosa', 'Biryani']),
                ('Dessert', ['Cheesecake', 'Brownie', 'Ice Cream', 'Donut']),
                ('Coffee', ['Latte', 'Espresso', 'Cappuccino', 'Mocha']),
                ('Mexican', ['Taco', 'Burrito', 'Quesadilla', 'Nachos'])
            ]
            
            # Map products to specific search keywords for better images
            keyword_map = {
                'Margherita': 'pizza,margherita',
                'Pepperoni': 'pizza,pepperoni',
                'Hawaiian': 'pizza,hawaiian',
                'Veggie': 'pizza,vegetable',
                'Cheeseburger': 'burger,cheese',
                'Bacon Burger': 'burger,bacon',
                'Chicken Burger': 'burger,chicken',
                'Fries': 'frenchfries',
                'Salmon Roll': 'sushi,salmon',
                'Tuna Nigiri': 'sushi,tuna',
                'California Roll': 'sushi,california',
                'Miso Soup': 'misosoup',
                'Kung Pao Chicken': 'kungpaochicken',
                'Dumplings': 'dumplings,food',
                'Fried Rice': 'friedrice',
                'Noodles': 'noodles,food',
                'Butter Chicken': 'butterchicken,curry',
                'Naan': 'naan,bread',
                'Samosa': 'samosa,food',
                'Biryani': 'biryani,food',
                'Cheesecake': 'cheesecake',
                'Brownie': 'brownie,chocolate',
                'Ice Cream': 'icecream',
                'Donut': 'donut',
                'Latte': 'latte,coffee',
                'Espresso': 'espresso,coffee',
                'Cappuccino': 'cappuccino,coffee',
                'Mocha': 'mocha,coffee',
                'Taco': 'taco,mexican',
                'Burrito': 'burrito,mexican',
                'Quesadilla': 'quesadilla,mexican',
                'Nachos': 'nachos,food'
            }

            for i in range(1, 25):
                m_username = f"merchant{i}"
                merchant = User(username=m_username, role='merchant')
                merchant.set_password('123456')
                db.session.add(merchant)
                
                s_type, s_products = shop_data[(i - 1) % len(shop_data)]
                shop_name = f"{s_type} Shop {i}"
                shop = Shop(name=shop_name, description=f"The best {s_type} in town!", owner=merchant)
                db.session.add(shop)
                db.session.commit() # Commit to get IDs
                
                # Add Products
                for p_idx, p_name in enumerate(s_products):
                    price = round(random.uniform(5.0, 25.0), 2)
                    
                    # 使用极高可用性的图库源
                    # Pixsum (Unsplash 镜像) 或者直接使用特定的图片 ID
                    # 这里我们使用 Pixum，它是目前最稳定的占位图/真实图片混合服务
                    # 同时也提供了一些预定义的食物图片 ID 范围
                    
                    # 方案：使用 picsum.photos，它在国内外的加载成功率极高
                    # 虽然它不是完全根据关键词，但我们可以通过 seed 确保每个商品图片不同且稳定
                    # 另外，我们增加一个 food 标签尝试让它返回更相关的图片
                    img_url = f"https://picsum.photos/seed/food-{i}-{p_idx}/400/300"
                    
                    # 如果需要更精准的食物图片，改用支持更好的 API
                    # 发现之前的 loremflickr 和 unsplash 在某些环境下确实不稳定
                    # 尝试使用 foodish-api (专门的美食图片 API) 或者直接使用稳定的静态 CDN
                    food_keywords = {
                        'Pizza': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop',
                        'Burger': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop',
                        'Sushi': 'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=400&h=300&fit=crop',
                        'Chinese': 'https://images.unsplash.com/photo-1525755662778-989d0524087e?w=400&h=300&fit=crop',
                        'Indian': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400&h=300&fit=crop',
                        'Dessert': 'https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=400&h=300&fit=crop',
                        'Coffee': 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&h=300&fit=crop',
                        'Mexican': 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400&h=300&fit=crop'
                    }
                    
                    # 获取该店铺类型的预设稳定图片链接
                    base_url = food_keywords.get(s_type, 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop')
                    # 通过给 unsplash 链接添加随机参数，使同一类型的图片略有不同（虽然主要还是那一张，但能保证显示）
                    img_url = f"{base_url}&sig={random.randint(1, 1000)}"
                    
                    prod = Product(name=p_name, price=price, shop=shop, image_url=img_url)
                    db.session.add(prod)
                
                # Add a dummy completed order so we can have a review
                order = Order(user=customer, shop=shop, status='Completed')
                db.session.add(order)
                db.session.flush() # Get order ID
                
                # Add a random review for this order
                review = Review(user=customer, shop=shop, order_id=order.id, content="Great food!", rating=random.randint(3, 5))
                db.session.add(review)
                
        db.session.commit()
    print("Dummy data created.")

    # Create dummy orders for merchant1 to show dashboard features
    with app.app_context():
        if not Order.query.first():
            print("Creating dummy orders...")
            # Order 1: Completed with review
            order1 = Order(user_id=1, shop_id=1, status='Completed')
            db.session.add(order1)
            db.session.flush()
            item1 = OrderItem(order_id=order1.id, product_id=1, quantity=2)
            db.session.add(item1)
            review1 = Review(user_id=1, shop_id=1, order_id=order1.id, content="味道很棒，配送也很快！", rating=5)
            db.session.add(review1)

            # Order 2: Pending for refund demo
            order2 = Order(user_id=1, shop_id=1, status='Pending')
            db.session.add(order2)
            db.session.flush()
            item2 = OrderItem(order_id=order2.id, product_id=2, quantity=1)
            db.session.add(item2)

            # Order 3: Completed for review demo
            order3 = Order(user_id=1, shop_id=2, status='Completed')
            db.session.add(order3)
            db.session.flush()
            item3 = OrderItem(order_id=order3.id, product_id=5, quantity=1)
            db.session.add(item3)

            db.session.commit()

    print(f"Login as 'customer'/'123456' or 'merchant1'/'123456'")

# Automatically initialize database when the app starts
# This ensures tables are created and dummy data is seeded on platforms like Render
try:
    with app.app_context():
        db.create_all()
        # Only seed if no users exist
        if not User.query.first():
            init_db()
except Exception as e:
    print(f"Database initialization error: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
