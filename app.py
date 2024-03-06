#Imports
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, login_required, login_user, LoginManager, logout_user, current_user

app= Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

login_manager = LoginManager()
db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
CORS(app)

#Models
class User (db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=True)
    cart = db.relationship('CartItem', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

#Routes    
    #Authentication
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

    
    #ROUTES OF PRODUCT

@app.route('/api/products', methods=['GET'])
def get_all_products():
    products = Product.query.all()
    products_list = []
    if products:
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'description': product.description
            }
            products_list.append(product_data)
        return jsonify(products_list)
    return jsonify({'message': 'Product not found'}), 404

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_id(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id, 
            'name': product.name,
            'price': product.price, 
            'description': product.description})
    return jsonify({'message': 'Product not found'}), 404

@app.route('/api/products/add', methods=['POST'])
@login_required
def add_product():
    data = request.json
    if 'name' in data and 'price' in data:
        product = Product(name=data['name'], price=data['price'], description=data.get('description', ''))
        db.session.add(product)
        db.session.commit()
        return jsonify({'message': 'Product added successfully'}), 201
    return jsonify({'message': 'Invalid request data'}), 400

@app.route('/api/products/update/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404
    
    data = request.json
    if 'name' in data: 
        product.name=data['name']

    if 'price' in data:
       product.price=data['price']
    
    if 'description' in data:
        product.description=data['description']

    db.session.commit()
    return jsonify({'message': 'Product updated successfully'})

@app.route('/api/products/delete/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'})
    return jsonify({'message': 'Product not found'}), 404

 #ROUTES OF CART

@app.route('/api/cart', methods=['GET'])
@login_required
def get_all_carts():
    carts = CartItem.query.all()
    cart_list = []
    if carts:
        for cart in carts:
            product = Product.query.get(cart.product_id)
            cart_data = {
                'id': cart.id,
                'user_id': cart.user_id,
                'product_id': cart.product_id,
                'product_name': product.name,
                'product_price': product.price
            }
            cart_list.append(cart_data)
        return jsonify(cart_list)
    return jsonify({'message': 'Product not found'}), 404

@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_product_to_cart(product_id):
    user = User.query.get(int(current_user.id))

    product = Product.query.get(product_id)
    if user and product:
         cart_item = CartItem(user_id=user.id, product_id=product.id)
         db.session.add(cart_item)
         db.session.commit()
         return jsonify({'message': 'Item added to the cart successfully'})
    return jsonify({'message': 'Failed to add item to the cart'}), 400

@app.route('/api/cart/remove/<int:item_id>', methods=['DELETE'])
@login_required
def remove_product_from_cart(item_id):
    cartItem = CartItem.query.get(item_id)
    if cartItem:
        db.session.delete(cartItem)
        db.session.commit()
        return jsonify({'message': 'Item removed from the cart successfully'})
    return jsonify({'message': 'Failed  to remove item from the cart'}), 404

@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout_cart():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.commit()
    return jsonify({'message': 'Checkout successful. Cart has been cleared'})

#ROUTES OF USER

@app.route('/api/user/add', methods=['POST'])
def add_user():
    data = request.json
    if 'username' in data and 'password' in data:
        user = User(username=data['username'], password=data.get('password', ''))
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User added successfully'}), 201
    return jsonify({'message': 'Invalid request data'}), 400


    #AUTHENTICATION

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if 'username' in data and 'password' in data:
        user = User.query.filter_by(username=data['username']).first()
        if user and user.password == data['password']:
            login_user(user)
            return jsonify({'message': 'Login successful'})
        return jsonify({'message': 'Invalid username or password'}), 401
    return jsonify({'message': 'Invalid request data'}), 400

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'})



if __name__ == '__main__':
    app.run(debug=True)