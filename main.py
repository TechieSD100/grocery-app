import os
from flask import Flask
from flask import render_template
from flask import request, redirect, url_for, session, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

current_dir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+os.path.join(current_dir, "database.sqlite3")
app.config['SECRET_KEY'] = 'groceryapp'
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()



#maintains the login system
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))





class User(db.Model, UserMixin):
    __tablename__='user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(40))
    password = db.Column(db.String(80), nullable=False)

class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    category_name = db.Column(db.String(40), nullable=False, unique=True)

class Items(db.Model):
    __tablename__='items'
    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.category_id"), nullable=False)
    item_name = db.Column(db.String, nullable=False, unique=True)
    stock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)

class Cart(db.Model):
    __tablename__='cart'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    item_name = db.Column(db.String, db.ForeignKey("items.item_name"), primary_key=True, nullable=False)
    price = db.Column(db.Integer, db.ForeignKey("items.price"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Integer, nullable=False)

class PurchaseTotal(db.Model):
    __tablename__='purchase_total'
    bill_id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    bill_total = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    purchase_bills = db.relationship('PurchaseBill', backref='purchase_total', lazy=True)

class PurchaseBill(db.Model):
    __tablename__='purchase_bill'
    sl_no = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    bill_id = db.Column(db.Integer, db.ForeignKey("purchase_total.bill_id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("items.category_id"), nullable=False)
    item_name = db.Column(db.String, db.ForeignKey("cart.item_name"), nullable=False)
    price = db.Column(db.Integer, db.ForeignKey("cart.price"), nullable=False)
    quantity = db.Column(db.Integer, db.ForeignKey("cart.quantity"), nullable=False)
    total_price = db.Column(db.Integer, db.ForeignKey("cart.total_price"), nullable=False)





@app.route('/')
def index():
    return render_template("index.html")


#The Login function checks for user and manager user authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('Username')
        password = request.form.get('Password')

        managers = User.query.limit(3).all() #only first 3 IDs of the user database will hold the manager login details

        for manager in managers:
            if manager.username == username and manager.password == password:
                login_user(manager)
                return redirect(url_for('manager', managerid=manager.id))

        user = User.query.filter_by(username=username).first()

        if user and user.password==password:
            login_user(user) #Logs in the user
            return redirect(url_for('home', userid=user.id)) #Redirect to home page after successful login
        else:
            error_message = "Invalid username or password. Please try again."
            return render_template("login.html", error_message=error_message)
    return render_template("login.html")





#The register function maintains user registration, it adds new user form entries to the user database.
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('Username')
        name = request.form.get('Name')
        email = request.form.get('Email')
        password = request.form.get('Password')

        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        #checks for already existing user
        if existing_user:
            error_message = "Username already exists. Please choose a different username."
            return render_template("register.html", error_message=error_message)
        #checks for already existing email-ids
        if existing_email:
            error_message = "Email already exists. Please use a different email."
            return render_template("register.html", error_message=error_message)

        new_user = User(username=username, name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template("register.html")




#maintains the manager dashboard
#allows adding new category
#lists the existing categories
#provides option to edit or delete the existing categories
@app.route('/manager', methods=['GET', 'POST'])
@login_required
def manager():
    if request.method == 'POST':
        c_name = request.form.get('category_name')
        
        new_category = Category(category_name = c_name)
        db.session.add(new_category)
        db.session.commit()
        return redirect(url_for('manager'))
    
    categories = Category.query.all()

    return render_template("manager.html", categories=categories)





#maintains the category editing section
#allows editing the category name
#allows adding a new item to the category
#lists the items under that category
#provides option to edit or delete the existing items
@app.route('/manager/category/<category_name>', methods=['GET', 'POST'])
@login_required
def edit_category(category_name):
    category = Category.query.filter_by(category_name=category_name).first()

    if request.method == 'POST':
        new_category_name = request.form.get('new_category_name')
        item_name = request.form.get('item_name')
        stock = request.form.get('stock')
        price = request.form.get('price')

        if new_category_name:
            category.category_name = new_category_name
            db.session.commit()
            return redirect(url_for('manager'))

        if item_name and stock and price:
            new_item = Items(
                category_id = category.category_id,
                item_name = item_name,
                stock = stock,
                price = price
            )
            db.session.add(new_item)
            db.session.commit()

    items = Items.query.filter_by(category_id=category.category_id).all()

    return render_template("edit_category.html", category=category_name, items=items)



#maintains the item editing functionality
#includes a form to update the item name, current stock and price of the item
@app.route('/manager/category/<category_name>/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(category_name, item_id):
    item = Items.query.get(item_id)

    if request.method == 'POST':
        new_item_name = request.form.get('item_name')
        new_stock = request.form.get('stock')
        new_price = request.form.get('price')

        if new_item_name and new_stock and new_price:
            item.item_name = new_item_name
            item.stock = new_stock
            item.price = new_price
            db.session.commit()
            return redirect(url_for('edit_category', category_name=category_name))

    return render_template('edit_item.html', item=item)




#functionality of the delete item button in the category edit section
@app.route('/manager/item/<i_id>/delete')
@login_required
def delete_item(i_id):
    item = Items.query.filter_by(item_id=i_id).first()
    category = Category.query.filter_by(category_id=item.category_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect(url_for('edit_category', category_name=category.category_name))




#functionality of category deletion in the manager dashboard
@app.route('/manager/category/<category_name>/delete', methods=['GET', 'POST'])
@login_required
def delete_category(category_name):
    category = Category.query.filter_by(category_name=category_name).first()
    
    if category:
        # Delete items under the category from the items table
        items_to_delete = Items.query.filter_by(category_id=category.category_id).all()
        for item in items_to_delete:
            db.session.delete(item)

        db.session.delete(category)
        db.session.commit()
    
    return redirect(url_for('manager'))




#User Dashboard screen, where the categories and items are listed
#allows adding items to cart by setting required quantity
#provides functionality to search for items
@app.route('/home/<int:userid>', methods=['GET', 'POST'])
@login_required
def home(userid):
    categories = Category.query.all()
    items = Items.query.all()
    users = User.query.filter_by(id=userid).first()

    search_query = request.args.get('search')
    if search_query:
        items = Items.query.filter(Items.item_name.ilike(f"%{search_query}%")).all()

    return render_template('home.html', userid=userid, name=users.name, categories=categories, items=items)




#sends data of items and quantities added to cart to the cart database
@app.route('/add_to_cart/<int:userid>', methods=['POST'])
@login_required
def add_to_cart(userid):
    if request.method == 'POST':
        item_name = request.form['item_name']
        price = int(request.form['price'])
        quantity = int(request.form['quantity'])
        total_price = price * quantity

        # Check if the item is already in the cart for the user
        existing_cart_item = Cart.query.filter_by(user_id=userid, item_name=item_name).first()

        if existing_cart_item:
            # Update the quantity and total price of the existing cart item
            existing_cart_item.quantity += quantity
            existing_cart_item.total_price += total_price
        else:
            # Add a new cart item if it doesn't exist in the cart
            cart_item = Cart(user_id=userid, item_name=item_name, price=price, quantity=quantity, total_price=total_price)
            db.session.add(cart_item)

        db.session.commit()

    return redirect(url_for('home', userid=userid))  # Redirect back to the home page




#lists the cart items under cart section
@app.route('/cart/<int:userid>')
@login_required
def cart(userid):
    cart_items = Cart.query.filter_by(user_id=userid).all()
    total_cart_price = sum(item.total_price for item in cart_items)
    
    return render_template('cart.html', userid=userid, cart_items=cart_items, total_cart_price=total_cart_price)




#allows editing the quantity of the cart items
@app.route('/cart/<int:userid>/update-quantity', methods=['POST'])
@login_required
def update_cart_quantity(userid):
    if request.method == 'POST':
        item_name = request.form['item_name']
        new_quantity = int(request.form['new_quantity'])

        cart_item = Cart.query.filter_by(user_id=userid, item_name=item_name).first()
        if cart_item:
            if new_quantity > 0:
                cart_item.quantity = new_quantity
                cart_item.total_price = cart_item.price * new_quantity
            else:
                db.session.delete(cart_item)
            db.session.commit()

    return redirect(url_for('cart', userid=userid))




#allows deleting items from the cart
@app.route('/cart/<int:userid>/delete-item', methods=['GET', 'POST'])
@login_required
def delete_cart_item(userid):
    if request.method == 'POST':
        item_name = request.form['item_name']
        cart_item = Cart.query.filter_by(user_id=userid, item_name=item_name).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()

    cart_items = Cart.query.filter_by(user_id=userid).all()
    total_cart_price = sum(item.total_price for item in cart_items)

    return redirect(url_for('cart', userid=userid, cart_items=cart_items, total_cart_price=total_cart_price))





#final buy option
#sends items bought to purchases section of manager by updating to purchase_bill and purchase_total tables
#decrements the stock of items bought from the items list
@app.route('/proceed_to_buy/<int:userid>', methods=['POST'])
@login_required
def proceed_to_buy(userid):
    cart_items = Cart.query.filter_by(user_id=userid).all()

    total_cart_price = sum(item.total_price for item in cart_items)

    # Create a new entry in the purchase_total table
    new_purchase_total = PurchaseTotal(bill_total=total_cart_price, user_id=current_user.id)  # Pass user_id
    db.session.add(new_purchase_total)
    db.session.commit()

    # Get the generated bill_id
    generated_bill_id = new_purchase_total.bill_id

    # Create entries in the purchase_bill table for each item in the cart
    for item in cart_items:
        item_in_db = Items.query.filter_by(item_name=item.item_name).first()
        if item_in_db:
            new_purchase_bill = PurchaseBill(
                bill_id=generated_bill_id,
                category_id=item_in_db.category_id,
                item_name=item.item_name,
                price=item.price,
                quantity=item.quantity,
                total_price=item.total_price
            )
            db.session.add(new_purchase_bill)

            new_stock = item_in_db.stock - item.quantity
            item_in_db.stock = new_stock

        db.session.delete(item)

    db.session.commit()

    return redirect(url_for('home', userid=userid))



#allows the user to view its past orders
@app.route('/orders/<int:userid>')
@login_required
def orders(userid):
    if current_user.id != userid:
        return redirect(url_for('home', userid=userid))

    user_purchase_totals = PurchaseTotal.query.filter_by(user_id=userid).all()

    return render_template('orders.html', userid=userid, user_purchase_totals=user_purchase_totals)





#displays the purchases by the users in the manager section
@app.route('/manager/purchases/<int:managerid>')
@login_required
def purchases(managerid):
    if current_user.id != managerid:
        return redirect(url_for('manager'))

    purchase_bills = PurchaseTotal.query.options(db.joinedload('purchase_bills')).all()
    users = User.query.all()  # Fetch all users to pass them to the template
    return render_template('purchases.html', managerid=managerid, purchase_bills=purchase_bills, users=users)



#allows deleting all the purchases displayed, from the database itself
@app.route('/manager/purchases/clear', methods=['POST'])
@login_required
def clear_purchases():
    # Delete all records from purchase_bill and purchase_total tables
    PurchaseBill.query.delete()
    PurchaseTotal.query.delete()
    db.session.commit()

    return redirect(url_for('purchases', managerid=current_user.id))





#filters out the top purchased products and sorts them in descending order
#the limit is set to show only the top 8 products, since there a number of products
def get_top_products(limit):
    top_products = db.session.query(PurchaseBill.item_name, db.func.sum(PurchaseBill.quantity).label('total_quantity')).\
        group_by(PurchaseBill.item_name).\
        order_by(db.desc('total_quantity')).\
        limit(limit).all()
    return top_products

#filters out the top purchased categories and sorts them in descending order
def get_top_categories():
    top_categories = db.session.query(Category.category_name, db.func.sum(PurchaseBill.quantity).label('total_quantity')).\
        join(Items, Items.category_id == Category.category_id).\
        join(PurchaseBill, PurchaseBill.item_name == Items.item_name).\
        group_by(Category.category_name).\
        order_by(db.desc('total_quantity')).all()
    return top_categories

#manages the summary section by displaying the top purchases
@app.route('/manager/summary/<int:managerid>')
@login_required
def summary(managerid):
    if current_user.id != managerid:
        return redirect(url_for('manager'))

    # Retrieve data for the summary
    top_products = get_top_products(8)
    top_categories = get_top_categories()

    return render_template('summary.html', managerid=managerid, top_products=top_products, top_categories=top_categories)





#logs out the user or manager
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)

