## 📦 README for Telegram Bot (OCR-Powered)

# 🖼️ Telegram OCR Bot

**Your private OCR assistant on Telegram – optimized for reading text from images in `.jpg`, `.jpeg`, or `.png` formats.**

---

## 🚀 Features

* ✅ Supports `.jpg`, `.jpeg`, and `.png` files
* 📖 Extracts text from image using [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
* 🕒 Fast, accurate, and multilingual text recognition
* 🔒 Works directly on Telegram — no data storage
* 🛠️ Modular, easy-to-extend Python codebase

---

## 🔧 Tech Stack

* 🐍 Python 3.10+
* 🤖 `python-telegram-bot`
* 🧠 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
* 🗂️ `Pillow`, `OpenCV`, `numpy`, `os`, etc.

---

## 💻 Local Setup

```bash
git clone https://github.com/your-username/telegram-ocr-bot.git
cd telegram-ocr-bot
pip install -r requirements.txt
```

Create a `.env` file and add your Telegram Bot Token:

```env
BOT_TOKEN=your_telegram_bot_token_here
```

Then run:

```bash
python app.py
```

---

## ☁️ Server Deployment (Railway/AWS)

1. Create environment variable `BOT_TOKEN` on the server.
2. Deploy the `app.py` entry point using a Procfile:

   ```
   web: python app.py
   ```
3. Make sure your instance has internet access and supports Python and PaddleOCR dependencies.

---

## 🔐 License

* 🔸 **Free for personal use**
* 🔸 Commercial use requires written permission or license purchase
* 🔸 Attribution is appreciated but not mandatory

---

## 🔐 License

This project is licensed under a **proprietary license**.

- ❌ No redistribution or resale allowed
- ✅ Personal use allowed with attribution
- 🛠️ Commercial use requires a license

For licensing inquiries, [contact me](mailto:gourabanandadatta@gmail.com).




