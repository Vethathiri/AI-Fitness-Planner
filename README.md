# 🏋️ FitAI – Personalized Fitness & Diet Planner for Students

FitAI is an AI-powered fitness and diet planning web application built with **Streamlit**.  
It generates **personalized 7-day workout and diet plans** tailored for Indian students, considering **budget, location, diet preference, workout place (Home/Gym), and weekly progress**.

The app supports **weekly plan evolution**, **progress tracking**, **PDF export**, and an **admin dashboard** for monitoring users.

---

## ✨ Features

### 👤 User Features
- 🔐 Login & Signup (secure password hashing)
- 🧠 AI-generated **7-day workout + diet plan**
- 🇮🇳 Indian food–focused diet plans
- 🏠 Home or 🏋️ Gym-based workouts
- 💸 Budget-aware meal planning
- 📈 Weekly progress tracking (weight-based)
- 🔄 Automatic plan evolution every week
- 📝 User preferences (injuries, food dislikes, lifestyle)
- 💬 Chat-based plan modification
- 📄 Download plans as **PDF**
- 📱 Works on **mobile & desktop browsers**

---

### 🛠️ Admin Features
- 🔐 Admin login
- 👥 View all users
- 📊 View user profiles & progress trends
- 📜 View plan history
- 🗑️ Delete plans (auto-removes corresponding progress)
- ❌ Delete users safely

---

## 🧱 Tech Stack

| Layer | Technology |
|-----|-----------|
| Frontend | Streamlit |
| Backend | Python |
| Database | PostgreSQL (Supabase / Cloud-hosted) |
| AI | Google Generative AI |
| PDF | fpdf2 |
| Auth | SHA-256 password hashing |
| OCR (optional) | pytesseract |
| Deployment | Streamlit Cloud |

---

## 📂 Project Structure
ai-fitness-planner/
│
├── app.py # Main Streamlit app
├── auth.py # Login / Signup logic
├── database.py # Database connection & queries
├── ai_api.py # AI prompt handling
├── pdf_utils.py # PDF generation
├── DejaVuSans.ttf # Unicode font for PDF (₹, Indian text)
├── requirements.txt
├── .env # Local secrets (NOT pushed)
│
├── pages/
│ └── admin.py # Admin dashboard
│
└── README.md

## ⚙️ Environment Variables

Create a `.env` file (local) or add secrets in Streamlit Cloud:

```env
DB_HOST=your_db_host
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_PORT=5432

GOOGLE_API_KEY=your_google_genai_key

ADMIN_USER=admin
ADMIN_PASS=admin_password

🗄️ Database Tables (Core)
-users
-user_profile
-plans
-progress
-preferences

The app automatically keeps profile weight updated from weekly progress.

▶️ Run Locally
1️⃣ Clone the repo
git clone https://github.com/your-username/ai-fitness-planner.git
cd ai-fitness-planner
2️⃣ Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
3️⃣ Install dependencies
pip install -r requirements.txt
4️⃣ Run the app
streamlit run app.py

☁️ Deploy on Streamlit Cloud
1.Push project to GitHub
2.Go to https://share.streamlit.io
3.Select repository & app.py
4.Add secrets in Settings → Secrets
5.Deploy 🚀

📱 Mobile Support

✅ Fully responsive
✅ Can login from phone
✅ Continue Week 2, Week 3 plans seamlessly

🧠 AI Safety & Validation

❌ Prevents saving AI error responses
✅ Saves only complete 7-day plans
🔁 Auto-regenerates incomplete plans
🛑 Protects existing plans from partial overwrite

🚀 Future Improvements

1.Wearable integration
2.Calorie breakdown
3.Multi-language support
4.Push notifications
5.Exercise demo videos

👨‍🎓 Ideal For
1.College mini / major projects
2.AI + Full Stack portfolios
3.Resume projects
4.Startup MVPs

🧑‍💻 Author

Vethathiri Kumarasamy
AI Fitness Planner Project
India 🇮🇳

⭐ If you like this project
Give it a ⭐ on GitHub and feel free to fork!
