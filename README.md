# **RoSa Shop – Telegram Store with YooKassa Payments**

### **🚀 About the Project**
**RoSa Shop** is a modern e-commerce platform integrated into a Telegram bot! Customers can:
- Browse products via an intuitive bot interface.
- Pay securely **online (YooKassa)**.
- Receive real-time order updates.

Perfect for small businesses, dropshipping, or digital goods.

---

### **⚙️ Tech Stack**
| Category          | Technologies                  |
|-------------------|-------------------------------|
| **Backend**       | Python, Django, Django REST   |
| **Payments**      | YooKassa SDK                  |
| **Delivery**      | Telegram Bot API              |
| **Deployment**    | Docker, Docker-compose        |

---

### **🛠️ Quick Start**

#### **1. Install Docker**
Ensure your server has:
- [Docker](https://docs.docker.com/engine/install/)
- [Docker-compose](https://docs.docker.com/compose/install/)

#### **2. Clone & Configure**
```bash
git clone https://github.com/Dushnilo/shop-project-django.git
cd shop-project-django
cp docker-compose-debug.yml docker-compose.yml
```

#### **3. Set Environment Variables**
Edit `docker-compose.yml` with your credentials:
```yaml
environment:
  SECRET_KEY: "your_django_secret_key"
  YOOKASSA_SHOP_ID: "your_shop_id"
  YOOKASSA_SECRET_KEY: "your_yookassa_key"
  TELEGRAM_BOT_TOKEN: "your_bot_token"
```

#### **4. Launch**
```bash
docker-compose up --build -d  # Run in background
```

#### **5. Access**
- Website: [http://localhost](http://localhost)
- Admin panel: [http://localhost/admin](http://localhost/admin)

---

### **🔐 Security**
Pre-configured protections against XSS, CSRF, and clickjacking:
```python
SECURE_HSTS_SECONDS = 31536000  # HTTPS enforcement (1 year)
X_FRAME_OPTIONS = 'DENY'        # Anti-iframe hijacking
```

---

### **🎯 Why Choose This?**
- **For businesses**: Telegram sales + secure payments.
- **For devs**: Production-ready Docker setup.



---



# **RoSa Shop – Telegram-магазин с оплатой через ЮKassa**

### **🚀 О проекте**
**RoSa Shop** – это современный интернет-магазин, встроенный прямо в Telegram-бота! Покупатели могут:
- Выбирать товары через удобный бот.
- Оплачивать заказы **онлайн (ЮKassa)**.
- Получать уведомления о статусе заказа.

Идеально для малого бизнеса, дропшиппинга или продажи цифровых товаров.

---

### **⚙️ Технологии**
| Категория       | Технологии                     |
|-----------------|--------------------------------|
| **Backend**     | Python, Django, Django REST    |
| **Платежи**     | Yookassa SDK                   |
| **Доставка**    | Telegram Bot API               |
| **Развертывание** | Docker, Docker-compose       |

---

### **🛠️ Быстрый старт**

#### **1. Установка Docker**
Убедитесь, что на сервере есть:
- [Docker](https://docs.docker.com/engine/install/)
- [Docker-compose](https://docs.docker.com/compose/install/)

#### **2. Клонирование и настройка**
```bash
git clone https://github.com/Dushnilo/shop-project-django.git
cd shop-project-django
cp docker-compose-debug.yml docker-compose.yml
```

#### **3. Настройка переменных**
Отредактируйте `docker-compose.yml`, заполнив **обязательные** поля:
```yaml
environment:
  SECRET_KEY: "ваш_секретный_ключ"
  YOOKASSA_SHOP_ID: "идентификатор_магазина"
  YOOKASSA_SECRET_KEY: "секретный_ключ_ЮKassa"
  TELEGRAM_BOT_TOKEN: "токен_бота"
```

#### **4. Запуск**
```bash
docker-compose up --build -d  # Запуск в фоновом режиме
```

#### **5. Доступ к проекту**
- Сайт: [http://localhost](http://localhost)
- Админка: [http://localhost/admin](http://localhost/admin)

---

### **🔐 Безопасность**
Проект включает настройки для защиты от XSS, CSRF и clickjacking:
```python
SECURE_HSTS_SECONDS = 31536000  # HTTPS на год для всех поддоменов
X_FRAME_OPTIONS = 'DENY'        # Блокировка встраивания в iframe
```

---

### **🎯 Почему это удобно?**
- **Для бизнеса**: Продажи через Telegram + безопасные платежи.
- **Для разработчиков**: Готовый Docker-образ с продуманной структурой.

---
