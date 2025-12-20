from flask import Flask, request, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import yagmail
from typing import ClassVar
from functools import wraps
from datetime import datetime
app = Flask(__name__)
app.secret_key = "secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# ====== DB model ======
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False, unique=True)
    surname = db.Column(db.String(50), nullable=True)
    phone_number = db.Column(db.String(19), nullable=True)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_info = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
class EditText(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text_new = db.Column(db.Text, nullable=False) # Ограничение на текст можно поменять db.String(тут ваше значние сколько хотите)
class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
# ====== Email ======
SENDER_EMAIL: ClassVar[str] = "someadress@gmail.com"
SENDER_PASSWORD: ClassVar[str] = "YOUR_SEC_PASSWORD"
RECEIVER_EMAIL: ClassVar[str] = "receiverADRESS@example.com"
# ====== Decorators ======
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_name" not in session:
            return redirect("/register")
        return f(*args, **kwargs)

    return decorated_function
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_name" not in session:
            return redirect("/register")
        user = User.query.filter_by(user_name=session["user_name"]).first()
        if not user or not user.is_admin:
            return "Доступ запрещен. Только для администраторов.", 403
        return f(*args, **kwargs)

    return decorated_function

class Email_receive:
    @staticmethod
    def send_data_to_email(username: str) -> bool:
        if not username:
            print("Ошибка: юзернэйм не может быть пустым")
            return False
        subject = f"Новая регистрация: {username}"
        contents = [f"<h2>Новые данные с сайта</h2>", f"<p>@{username}</p>"]
        try:
            yag = yagmail.SMTP(user=SENDER_EMAIL, password=SENDER_PASSWORD)
            yag.send(to=RECEIVER_EMAIL, subject=subject, contents=contents)
            print(f"Сообщение о юзернейме '{username}' успешно отправлено.")
            return True
        except Exception as e:
            print(f"Ошибка при отправке почты: {e}")
            return False


# ====== Routes ======
@app.route("/")
def index():
    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        action = request.form.get("action")
        user_name = request.form.get("user_name")
        password = request.form.get("password")
        if not user_name or not password:
            return render_template(
                "register.html", error="Все поля должны быть заполнены", action=action
            )
        user = User.query.filter_by(user_name=user_name).first()
        if action == "register":
            if user:
                return render_template(
                    "register.html",
                    error="Пользователь уже существует, попробуйте сделать другой никнейм.",
                    action="register",
                )
            surname = request.form.get("surname")
            phone_number = request.form.get("phone_number")
            hashed_password = generate_password_hash(password)
            new_user = User(
                user_name=user_name,
                password=hashed_password,
                surname=surname,
                phone_number=phone_number,
            )
            db.session.add(new_user)
            db.session.commit()
            session["user_name"] = user_name
            Email_receive.send_data_to_email(user_name)
            return redirect("/about_product")
        elif action == "login":
            if not user or not check_password_hash(user.password, password):
                return render_template(
                    "register.html", error="Неверное имя или пароль", action="login"
                )
            session["user_name"] = user_name
            return redirect("/about_product")
    return render_template("register.html", error=None, action="login")
@app.route("/admin/edit_page/<string:page_name>", methods=["GET", "POST"])
@admin_required
def edit_page(page_name):
    page = Page.query.filter_by(name=page_name).first_or_404()
    if request.method == "POST":
        page.title = request.form.get("title")
        page.content = request.form.get("content")
        db.session.commit()
        return redirect("/admin")
    return render_template("edit_page.html", page=page)


@app.route("/about_product")
def about_product():
    if "user_name" in session:
        user = User.query.filter_by(user_name=session["user_name"]).first()
        is_admin = user.is_admin if user else False

     
        db.session.expire_all()
        page_text = EditText.query.get(1)


        if page_text:
            print(f"🔍 [about_product] ID: {page_text.id}")
            print(
                f"📝 [about_product] Текст (первые 100 символов): {page_text.text_new[:100]}"
            )
            print(f"📏 [about_product] Полная длина текста: {len(page_text.text_new)}")
        else:
            print("❌ [about_product] page_text is None!")

        return render_template(
            "about_product.html",
            user_name=session["user_name"],
            is_admin=is_admin,
            page_text=page_text.text_new if page_text else "Текст не найден",
        )
    return redirect("/register")


@app.route("/drafts")
def drafts():
    if "user_name" in session:
        user = User.query.filter_by(user_name=session["user_name"]).first()
        is_admin = user.is_admin if user else False


        db.session.expire_all()
        page_text = EditText.query.get(2) 

    
        if page_text:
            print(f"🔍 [drafts] ID: {page_text.id}")
            print(
                f"📝 [drafts] Текст (первые 100 символов): {page_text.text_new[:100]}"
            )
        else:
            print("❌ [drafts] page_text is None!")

        return render_template(
            "drafts.html",
            user_name=session["user_name"],
            is_admin=is_admin,
            page_text=page_text.text_new if page_text else "Текст не найден",
        )
    return redirect("/register")
@app.route("/plans")
def plans():
    if "user_name" in session:
        user = User.query.filter_by(user_name=session["user_name"]).first()
        is_admin = user.is_admin if user else False

        db.session.expire_all()
        page_text = EditText.query.get(3)  

        if page_text:
            print(f"🔍 [plans] ID: {page_text.id}")
            print(f"📝 [plans] Текст (первые 100 символов): {page_text.text_new[:100]}")
            print(f"📏 [plans] Полная длина текста: {len(page_text.text_new)}")
        else:
            print("❌ [plans] page_text is None!")

        return render_template(
            "plans.html",
            user_name=session["user_name"],
            is_admin=is_admin,
            page_text=page_text.text_new if page_text else "Текст не найден",
        )
    return redirect("/register")





# Admin panel
@app.route("/admin")
@admin_required
def admin_panel():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    unread_count = ContactMessage.query.filter_by(is_read=False).count()
    texts = {
        1: EditText.query.get(1),
        2: EditText.query.get(2),
        3: EditText.query.get(3),
        4: EditText.query.get(4),
    }
    return render_template(
        "admin.html",
        messages=messages,
        unread_count=unread_count,
        texts=texts,
    )

@app.route("/admin/mark_read/<int:message_id>")
@admin_required
def mark_read(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    return redirect("/admin")


@app.route("/admin/delete/<int:message_id>")
@admin_required
def delete_message(message_id):
    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    return redirect("/admin")


@app.route("/logout")
def logout():
    session.pop("user_name", None)
    return redirect("/register")











@app.route("/edit_text/edit/<int:text_id>", methods=["GET", "POST"])
@admin_required
def edit_text(text_id):
    text_entry = EditText.query.get_or_404(text_id)

    page_names = {1: "О продукте", 2: "Наработки", 3: "Планируем", 4: "Контакты"}

    if request.method == "POST":
        new_text = request.form.get("text_new")

        print(f"📥 Получен POST запрос для ID: {text_id}")
        print(
            f"📝 Новый текст (первые 100 символов): {new_text[:100] if new_text else 'None'}"
        )

        if new_text is not None:
            text_entry.text_new = new_text
            try:
                db.session.commit()
                print(f"✅ Текст ID {text_id} успешно обновлен. Длина: {len(new_text)}")
                return redirect("/admin")
            except Exception as e:
                print(f"❌ Ошибка сохранения: {e}")
                db.session.rollback()
                return f"Ошибка при сохранении: {e}", 500
        else:
            print(f"⚠️ Текст пустой или None")
            return "Текст не может быть пустым", 400

    print(f"📄 Отображение формы редактирования для ID: {text_id}")
    return render_template(
        "edit_text.html",
        text=text_entry,
        page_name=page_names.get(text_id, "Неизвестная страница"),
    )

























@app.route("/contact", methods=["GET", "POST"])
def contact():
    is_admin = False
    if "user_name" in session:
        user = User.query.filter_by(user_name=session["user_name"]).first()
        is_admin = user.is_admin if user else False
    db.session.expire_all()
    page_text = EditText.query.get(4) 
    if page_text:
        print(f"🔍 [contact] ID: {page_text.id}")
        print(f"📝 [contact] Текст (первые 100 символов): {page_text.text_new[:100]}")
    else:
        print("❌ [contact] page_text is None!")
    if request.method == "POST":
        contact_info = request.form.get("contact_info")
        if contact_info and contact_info.strip():
            new_message = ContactMessage(contact_info=contact_info.strip())
            db.session.add(new_message)
            db.session.commit()
            return render_template(
                "contact.html",
                success="Спасибо! Ваши контактные данные отправлены.",
                is_admin=is_admin,
                page_text=page_text.text_new if page_text else "Текст не найден",
            )
        else:
            return render_template(
                "contact.html",
                error="Пожалуйста, заполните поле.",
                is_admin=is_admin,
                page_text=page_text.text_new if page_text else "Текст не найден",
            )

    return render_template(
        "contact.html",
        is_admin=is_admin,
        page_text=page_text.text_new if page_text else "Текст не найден",
    )

# ====== Initialize DB ======
with app.app_context():
    db.create_all()
    admin = User.query.filter_by(user_name="admin").first()
    if not admin:
        admin_user = User(
            user_name="admin",
            password=generate_password_hash("admin123"),
            is_admin=True,
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Админ создан: логин 'admin', пароль 'admin123'")

    if EditText.query.count() == 0:
        pages = [
            EditText(id=1, text_new="Текст для страницы 'О продукте'"),
            EditText(id=2, text_new="Текст для страницы 'Наработки'"),
            EditText(id=3, text_new="Текст для страницы 'Планируем'"),
            EditText(id=4, text_new="Текст для страницы 'Контакты'"),
        ]
        for page in pages:
            db.session.add(page)
        db.session.commit()
        print("✅ Тексты страниц созданы")

if __name__ == "__main__":
    app.run(debug=True)
