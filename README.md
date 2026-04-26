# Virtus Fit AI 🤖💪 | Smart Fitness & Nutrition Assistant

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green.svg)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-success.svg)
![Gemini AI](https://img.shields.io/badge/Gemini_1.5_Vision-AI-orange.svg)
![CryptoPay](https://img.shields.io/badge/CryptoPay-Web3-lightgrey.svg)

**Virtus Fit AI** is a next-generation Telegram bot designed to automate fitness tracking, nutrition analysis, and premium subscription management. Built with modern asynchronous Python architecture, it leverages LLM vision models to provide users with a seamless, AI-driven healthy lifestyle experience.

##  Comprehensive Feature Set

### 🧠 AI-Powered Nutritionist (Google Gemini Vision)
* **Computer Vision Analysis:** Users can send a photo of their meal, and the bot instantly identifies the food.
* **Automated Macros Calculation:** Calculates estimated Calories, Protein, Fats, and Carbohydrates purely from image data.
* **Contextual Dialogue:** Maintains context for follow-up questions regarding diet and health advice.

### 💳 Web3 Crypto Billing & Premium Access
* **CryptoPay API Integration:** Fully automated payment gateway supporting major cryptocurrencies (USDT, TON, SOL).
* **Telegram Stars Support:** Integrated with native Telegram Stars for fiat-equivalent in-app purchases.
* **Automated Subscription Logic:** Real-time balance updates, tier unlocking, and premium feature distribution without manual intervention.

### 🛡 Robust Database Architecture (Supabase / PostgreSQL)
* **Persistent Storage:** Securely stores user profiles, biometric data (age, weight, goals), and financial balances.
* **Fast I/O Operations:** Optimized database queries ensuring high-speed data retrieval even under heavy bot load.

### 🔗 Gamified Referral System
* **Dynamic Deep Linking:** Generates unique invite links for every user.
* **Reward Distribution:** Automatically credits internal balance/premium points when new users join via a referral link, driving organic growth.

### 🖥 Telegram Web App Integration (Mini App)
* **Rich UI/UX:** Utilizes standard HTML/CSS/JS (`index.html`) to render beautiful, responsive Web Apps directly inside Telegram for complex interactions and visual dashboards.

## ⚙️ Architecture & Under the Hood
* **Asynchronous Design:** Built on `aiogram 3.x`, ensuring non-blocking execution and the ability to handle thousands of concurrent users efficiently.
* **State Management (FSM):** Implements Finite State Machines for complex user flows (e.g., registration, goal setting, payment processing).
* **Modular Codebase:** Clean separation of concerns (keyboards, handlers, database routers, external API calls) for high maintainability and easy scaling.
* **Secure Configuration:** Strict usage of Environment Variables (`.env`) for all sensitive tokens and API keys.

## 🚀 Installation & Local Development

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/dima584/virtus-fit-app.git](https://github.com/dima584/virtus-fit-app.git)
   cd virtus-fit-app
