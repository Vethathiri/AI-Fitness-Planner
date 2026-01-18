import streamlit as st, random
from auth import signup, login
from auth import user_exists
from database import get_cursor
from ai_api import query_ai
from pdf_utils import create_pdf
from database import get_plan_history
from datetime import datetime, timedelta
from database import get_user_profile, upsert_user_profile
from database import get_user_progress
import pandas as pd

def is_valid_plan(text: str) -> bool:
    if not text:
        return False

    t = text.lower()

    # ❌ AI / system error phrases
    blocked_phrases = [
        "ai is busy",
        "high usage",
        "try again",
        "please try again",
        "currently unavailable",
        "service unavailable",
        "rate limit",
        "too many requests",
        "unable to generate",
        "something went wrong",
        "error"
    ]

    if any(p in t for p in blocked_phrases):
        return False

    # ✅ Must contain ALL 7 days
    for i in range(1, 8):
        if f"day {i}:" not in t:
            return False

    # ✅ Length safety (prevents cut-off)
    if len(text) < 800:
        return False

    return True


st.set_page_config(
    page_title="FitAI",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"  # 👈 IMPORTANT
)


st.markdown("""
<style>
.card {
    background-color:#1E1E1E;
    padding:16px;
    border-radius:12px;
    margin-bottom:16px;
}
</style>
""", unsafe_allow_html=True)

def logo(center=True):
    st.markdown(
        f"<h1 style='text-align:{'center' if center else 'left'};'>🏋️ FitAI</h1>",
        unsafe_allow_html=True
    )
    st.caption("Smart Fitness • Smart Diet")

QUOTES = [
    "Consistency beats intensity 💪",
    "Your body adapts when you listen 🧠",
    "Small steps create big results 🔥",
    "Progress, not perfection 🚀",
    "Show up for yourself every day 🏃",
    "Discipline builds freedom 🧩",
    "Strong habits build strong bodies 🏋️",
    "One workout at a time ⏱️",
    "Fuel your body, power your goals 🍎",
    "Your future self will thank you 🙌",
    "Healthy choices add up 📈",
    "Focus on effort, not excuses 🎯",
    "Train your mind as much as your body 🧠",
    "Every rep makes you better 🔁",
    "Consistency is the real transformation 🔥",
    "Start where you are, grow from there 🌱",
    "Small wins matter every day 🏆",
    "Health is your best investment 💚",
    "Build strength, build confidence 💥",
    "Trust the process, stay patient ⏳"
]

if "page" not in st.session_state:
    st.session_state.page="welcome"
if "user_id" not in st.session_state:
    st.session_state.user_id=None
if "show_history" not in st.session_state:
    st.session_state.show_history = False
if "show_progress" not in st.session_state:
    st.session_state.show_progress = False
if "username" not in st.session_state:
    st.session_state.username = ""


# -------- ACCESS GUARD (STEP 3) --------
if st.session_state.page not in ("welcome", "auth", "thankyou") and not st.session_state.user_id:
    st.session_state.page = "welcome"
    st.rerun()
if st.session_state.page == "dashboard":
    pass  # dashboard content already rendered below

# -------- THANK YOU --------
if st.session_state.page=="thankyou":
    logo()
    st.markdown(f"### Thank you, {st.session_state.username} 🙏")
    st.info(random.choice(QUOTES))
    st.info("Thanks for using FitAI. Stay healthy 💙")
    if st.button("🔁 Back to Welcome"):
        st.session_state.clear()
        st.session_state.page="welcome"
        st.rerun()
    st.stop()

# -------- WELCOME --------
if st.session_state.page=="welcome":
    logo()
    st.info(random.choice(QUOTES))
    if st.button("🚀 Get Started", use_container_width=True):
        st.session_state.page="auth"
        st.rerun()
    st.stop()

# -------- AUTH --------
if st.session_state.page == "auth" and not st.session_state.user_id:
    logo()
    t1, t2 = st.tabs(["Login", "Signup"])

    # -------- LOGIN (FORM) --------
    with t1:
        with st.form("login_form", clear_on_submit=True):
            u = st.text_input("Username", key="login_username")
            p = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login")

            if submit:
                if not u or not p:
                    st.warning("Please enter both username and password")
                    st.stop()

                r = login(u, p)
                if r:
                    st.session_state.user_id = r[0]
                    st.session_state.username = u

                    # detect last completed week
                    cursor = get_cursor()
                    cursor.execute(
                        "SELECT COALESCE(MAX(week), 0) FROM plans WHERE user_id=%s",
                        (st.session_state.user_id,)
                    )
                    st.session_state.current_week = cursor.fetchone()[0]

                    st.session_state.page = (
                        "week2" if st.session_state.current_week >= 1 else "dashboard"
                    )
                    st.rerun()
                else:
                    if not user_exists(u):
                        st.warning("⚠️ User not found. Please sign up to continue.")
                    else:
                        st.error("❌ Invalid username or password.")

    # -------- SIGNUP (NORMAL INPUTS) --------
    with t2:
        u=st.text_input("New Username",key="signup_username")
        p=st.text_input("New Password", type="password",key="signup_password")
        if st.button("Signup") and signup(u,p):
            st.session_state.pop("signup_username", None)
            st.session_state.pop("signup_password", None)

            st.success("Signup successful. Please login.")
    st.stop()


STATE_CITY_MAP = {
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool", "Rajahmundry", "Tirupati", "Anantapur"],
    "Arunachal Pradesh": ["Itanagar", "Naharlagun", "Pasighat", "Tawang"],
    "Assam": ["Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Tezpur", "Nagaon"],
    "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga", "Purnia"],
    "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur", "Korba", "Durg"],
    "Goa": ["Panaji", "Margao", "Vasco da Gama", "Mapusa"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Junagadh", "Gandhinagar"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat", "Ambala", "Hisar", "Rohtak"],
    "Himachal Pradesh": ["Shimla", "Solan", "Dharamshala", "Mandi", "Una"],
    "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Hazaribagh"],
    "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi", "Belagavi", "Davangere", "Ballari"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam", "Alappuzha", "Palakkad"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain", "Sagar"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Solapur", "Kolhapur"],
    "Manipur": ["Imphal", "Thoubal", "Bishnupur"],
    "Meghalaya": ["Shillong", "Tura", "Nongpoh"],
    "Mizoram": ["Aizawl", "Lunglei", "Champhai"],
    "Nagaland": ["Kohima", "Dimapur", "Mokokchung"],
    "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Sambalpur", "Balasore"],
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Mohali"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Bikaner", "Ajmer"],
    "Sikkim": ["Gangtok", "Namchi", "Gyalshing"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Trichy", "Salem", "Tirunelveli", "Erode", "Vellore", "Thoothukudi", "Thanjavur"],
    "Telangana": ["Hyderabad", "Warangal", "Karimnagar", "Nizamabad", "Khammam"],
    "Tripura": ["Agartala", "Udaipur", "Dharmanagar"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Prayagraj", "Noida", "Ghaziabad", "Meerut", "Agra"],
    "Uttarakhand": ["Dehradun", "Haridwar", "Roorkee", "Haldwani", "Nainital"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri"],
    "Delhi": ["New Delhi", "Dwarka", "Rohini", "Saket"],
    "Jammu and Kashmir": ["Srinagar", "Jammu", "Anantnag"],
    "Ladakh": ["Leh", "Kargil"],
    "Chandigarh": ["Chandigarh"],
    "Puducherry": ["Puducherry", "Karaikal"],
    "Andaman and Nicobar Islands": ["Port Blair"],
    "Dadra and Nagar Haveli and Daman and Diu": ["Daman", "Silvassa"],
    "Lakshadweep": ["Kavaratti"]
}

profile = get_user_profile(st.session_state.user_id)

if profile:
    (
        age_db, height_db, weight_db,
        state_db, city_db, goal_db,
        diet_db, workout_place_db, budget_db
    ) = profile
else:
    age_db = height_db = weight_db = None
    state_db = city_db = goal_db = diet_db = workout_place_db = None
    budget_db = None

cursor = get_cursor()
cursor.execute("SELECT COUNT(*) FROM plans WHERE user_id=%s",(st.session_state.user_id,))
plan_count=cursor.fetchone()[0]
cursor.close()

# -------- SIDEBAR --------
st.sidebar.title("Profile")
st.sidebar.info("👈 Please fill all details before generating your plan")
age=st.sidebar.number_input("Age",16,40,value=int(age_db) if age_db is not None else 18,step=1)
height=st.sidebar.number_input("Height (cm)",130.0,220.0, value=float(height_db) if height_db is not None else 165.0,step=0.1)
weight=st.sidebar.number_input("Weight (kg)",30.0,200.0, value=float(weight_db) if weight_db is not None else 60.0,step=0.1)
st.sidebar.markdown("### State")

state = st.sidebar.selectbox(
    "Select your state",
    list(STATE_CITY_MAP.keys()),
    index=list(STATE_CITY_MAP.keys()).index(state_db)
    if state_db in STATE_CITY_MAP else 0
)
st.sidebar.markdown("### City")

cities_for_state = STATE_CITY_MAP.get(state, [])

city_suggestion = st.sidebar.selectbox(
    "Select city (optional)",
    [""] + cities_for_state,
    index=(cities_for_state.index(city_db) + 1)
    if city_db in cities_for_state else 0
)

city = st.sidebar.text_input(
    "Type your city",
    value=city_db or city_suggestion
)

goal=st.sidebar.selectbox("Goal",["Fat Loss","Muscle Gain","Maintenance"],
    index=["Fat Loss","Muscle Gain","Maintenance"].index(goal_db)
    if goal_db else 0)
diet=st.sidebar.selectbox("Diet",["Vegetarian","Eggetarian","Non-Vegetarian"],
    index=["Vegetarian","Eggetarian","Non-Vegetarian"].index(diet_db)
    if diet_db else 0)
budget=st.sidebar.slider("Budget ₹",100,1000,
    value=budget_db or 500)
workout_place=st.sidebar.radio("Workout Place",["Home","Gym"],
    index=0 if workout_place_db=="Home"
    else 1 if workout_place_db=="Gym"
    else 0)

if st.sidebar.button("Logout"):
    st.session_state.show_progress = False
    st.session_state.show_history = False

    name=st.session_state.username
    st.session_state.clear()
    st.session_state.page="thankyou"
    st.session_state.username=name
    st.rerun()

# -------- TOP BAR --------
top_left, top_right = st.columns([6, 2])

with top_left:
    logo(False)

with top_right:
    st.markdown(
        f"""
        <div style="text-align:right;">
            👤 <b>{st.session_state.username}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

        # 📜 Plan History (guard)
    if plan_count == 0:
        st.button("📜 Plan History", use_container_width=True, disabled=True)
    else:
        if st.button("📜 Plan History", use_container_width=True):
            st.session_state.show_history = True
            st.session_state.page = "dashboard"
            st.rerun()

    if plan_count == 0:
        st.button("📈 Progress Trends", use_container_width=True, disabled=True)
    else:
        if st.button("📈 Progress Trends", use_container_width=True):
            st.session_state.show_progress = True
            st.session_state.page = "dashboard"   # ✅ ADD THIS
            st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.show_progress = False
        st.session_state.show_history = False

        name = st.session_state.username
        st.session_state.clear()
        st.session_state.page = "thankyou"
        st.session_state.username = name
        st.rerun()

if st.session_state.page == "week2":
    st.session_state.show_history = False
    st.session_state.show_progress = False


# -------- WEEK 2 / NEXT PLAN PAGE --------
if st.session_state.page == "week2":
    # ---- Detect current week number ----
    cursor = get_cursor()
    cursor.execute(
    "SELECT COALESCE(MAX(week), 0) FROM plans WHERE user_id=%s",
    (st.session_state.user_id,)
)
    current_week = cursor.fetchone()[0] + 1
    cursor.close()

    logo()
    st.subheader(f"🔄 Week {current_week} – Update Your Progress")

    new_weight = st.number_input(
        "Current weight (kg)",
        min_value=30.0,
        max_value=200.0,
        step=0.1
    )

    difficulty = st.selectbox(
        "How was last week's plan?",
        ["Too Easy", "Just Right", "Too Hard"]
    )

    notes = st.text_area(
        "Any issues? (pain, schedule, food problems)",
        placeholder="Optional"
    )

    if st.button(f"Generate Week {current_week} Plan"):
        # Save progress
        cursor = get_cursor()
        cursor.execute(
            "INSERT INTO progress(user_id, week, weight, difficulty) VALUES (%s,%s,%s,%s)",
            (st.session_state.user_id, current_week, new_weight, difficulty)
        )
        cursor.close()
        cursor = get_cursor()
        cursor.execute("""
    UPDATE user_profile
    SET weight = %s
    WHERE user_id = %s
""", (new_weight, st.session_state.user_id))
        cursor.close()

        profile = get_user_profile(st.session_state.user_id)
        if profile:
            (
            age_db, height_db, weight_db,
            state_db, city_db, goal_db,
            diet_db, workout_place_db, budget_db
        ) = profile
        cursor = get_cursor()
        # Fetch previous plan
        cursor.execute(
            "SELECT plan FROM plans WHERE user_id=%s ORDER BY timestamp DESC LIMIT 1",
            (st.session_state.user_id,)
        )
        prev_plan = cursor.fetchone()[0]
        cursor.close()
        cursor = get_cursor()
        cursor.execute("""
SELECT value FROM preferences
WHERE user_id=%s AND key='user_preferences'
""", (st.session_state.user_id,))

        row = cursor.fetchone()
        preferences = row[0] if row else ""
        cursor.close()

        if not city or not state:
            st.error("Please select your state and city.")
            st.stop()
        with st.spinner(f"🤖 Adapting your plan for Week {current_week}..."):
            adapted = query_ai(f"""
ROLE:
You are a Certified Indian Fitness Coach & Nutritionist.

TASK:
Generate a COMPLETELY NEW and COMPLETE 7-day workout + diet plan for WEEK {current_week}.

THIS IS A STRICT RE-GENERATION TASK.
The previous plan is provided ONLY for reference to AVOID repetition.

━━━━━━━━━━━━━━━━━━
USER CONTEXT:
- Previous week plan: PROVIDED BELOW
- User feedback: {difficulty}
- Current weight: {new_weight} kg
- User notes / issues: {notes}
- Goal: {goal}
- Diet type: {diet}
- Weekly budget: ₹{budget}
- Location: {city}, {state}
- Workout place: {workout_place}
- User preferences (fixed from Week 1): {preferences}
━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━
ABSOLUTE RULES (NON-NEGOTIABLE):
1. You MUST return a COMPLETE plan (Day 1 to Day 7).
2. Workout AND diet must be present for ALL 7 days.
3. Do NOT stop early.
4. Do NOT summarize.
5. Do NOT explain.
6. Do NOT reuse or slightly modify previous content.
7. Output ONLY the final plan.
━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━
WORKOUT EVOLUTION RULES (VERY IMPORTANT):
- DO NOT repeat exercises from the previous week.
- DO NOT reuse the same exercise with higher reps/sets.
- ALL major exercises must be DIFFERENT from last week.
- You MAY keep the same muscle split, but exercises must change.
- Introduce NEW movement patterns (tempo, unilateral, stability, isometric, compound variations).
- At least 2–3 completely NEW exercises per day.
- If feedback was:
  • "Too Easy" → increase difficulty using harder variations
  • "Just Right" → moderate progression with new exercises
  • "Too Hard" → reduce load but STILL change exercises
- Maintain safety and recovery.
━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━
DIET VARIATION RULES (VERY IMPORTANT):
- DO NOT repeat the same meals from last week.
- DO NOT reuse identical breakfast/lunch/dinner items.
- Rotate protein sources, grains, vegetables.
- Change meals on AT LEAST 5 out of 7 days.
- Calories should remain goal-appropriate.
- Use foods commonly available in {city}, {state}.
- Respect diet type strictly ({diet}).
━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━
PREFERENCE RULES:
- Respect all user preferences strictly.
- If a preference conflicts with safety, replace with the closest safe alternative.
━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━
FORMAT (BULLET POINTS ONLY — FOLLOW EXACTLY):

- Title: Week {current_week} Fitness Plan

- 7-Day Workout Plan
  - Day 1:
    - Exercise: sets × reps
  - Day 2:
    - Exercise: sets × reps
  - Day 3:
    - Exercise: sets × reps
  - Day 4:
    - Exercise: sets × reps
  - Day 5:
    - Exercise: sets × reps
  - Day 6:
    - Exercise: sets × reps
  - Day 7:
    - Active recovery / rest

- 7-Day Diet Plan
  - Day 1:
    - Breakfast:
    - Lunch:
    - Dinner:
  - Day 2:
    - Breakfast:
    - Lunch:
    - Dinner:
  - Day 3:
    - Breakfast:
    - Lunch:
    - Dinner:
  - Day 4:
    - Breakfast:
    - Lunch:
    - Dinner:
  - Day 5:
    - Breakfast:
    - Lunch:
    - Dinner:
  - Day 6:
    - Breakfast:
    - Lunch:
    - Dinner:
  - Day 7:
    - Breakfast:
    - Lunch:
    - Dinner:

- Hydration:
  - Drink 2.5–3 liters of water daily

━━━━━━━━━━━━━━━━━━
PREVIOUS WEEK PLAN (REFERENCE ONLY — DO NOT COPY):
{prev_plan}

FINAL CHECK BEFORE RESPONDING:
- Did you change ALL major exercises? YES / NO
- Are ALL 7 days present? YES / NO
- Is diet different from last week? YES / NO

ONLY RESPOND IF ALL ANSWERS ARE YES.

""")
        
        required_days=[f"Day {i}"for i in range(1,8)]
        if not adapted or adapted.strip().startswith("⚠️"):
            st.error("❌ Failed to generate next week plan. Please try again.")
            st.stop()

        # ⚠️ Incomplete plan → regenerate ONCE
        if not all(day in adapted for day in required_days):
            st.warning("⚠️ Incomplete plan detected. Regenerating...")
            adapted = query_ai(f"""
You are a certified fitness coach.

CRITICAL (NON-NEGOTIABLE):
- Return a COMPLETE 7-day plan
- MUST include Day 1 through Day 7
- Workout + Diet for all days
- Do NOT summarize
- Do NOT stop early
- Do NOT explain

FORMAT:
                              
7-Day Workout Plan
Day 1:
...
Day 7:

                               
7-Day Diet Plan
Day 1:
- Breakfast:
- Lunch:
- Dinner:
...
Day 7:
- Breakfast:
- Lunch:
- Dinner:
                               
""")


        # ❌ Still broken → do NOT save
        if not all(day in adapted for day in required_days):
            st.error("❌ Plan generation failed. Please try again.")
            st.stop()

        
        # ✅ PART 5 — UPDATE USER PROFILE WITH LATEST VALUES
        upsert_user_profile(
    st.session_state.user_id,
    age, height, weight,
    state, city,
    goal, diet,
    workout_place,
    budget
)
        st.session_state.profile_updated = True
        # 🔄 Refresh profile data after saving
        profile = get_user_profile(st.session_state.user_id)
        if profile:
            (
            age_db, height_db, weight_db,
            state_db, city_db, goal_db,
            diet_db, workout_place_db, budget_db
            ) = profile
        # ✅ ISSUE 5 — insert or replace SAME week
        cursor = get_cursor()
        cursor.execute("""
    INSERT INTO plans (user_id, week, plan)
    VALUES (%s, %s, %s)
    ON CONFLICT(user_id, week)
    DO UPDATE SET
        plan = excluded.plan,
        timestamp = CURRENT_TIMESTAMP
""", (
    st.session_state.user_id,
    current_week,
    adapted
))
        cursor.close()

        st.session_state.plan = adapted
        st.session_state.current_week = current_week
        st.session_state.page = "dashboard"
        st.session_state.show_progress = False

        st.success(f"✅ Your Week {current_week} plan is ready!")
        st.rerun()

    if st.button("⬅️ Back"):
        st.session_state.page = "dashboard"
        st.rerun()

    if not (st.session_state.show_history or st.session_state.show_progress):
        st.stop()


# -------- DASHBOARD --------
st.markdown("<div class='card'>", unsafe_allow_html=True)
c1,c2,c3 = st.columns(3)
c1.metric("🤖 AI Confidence","High")
c2.metric("🎯 Goal", goal)
c3.metric("🏋️ Workout", workout_place)
st.markdown("</div>", unsafe_allow_html=True)

st.info(random.choice(QUOTES))

if st.session_state.get("show_progress"):

    # 🚨 NEW USER SAFETY CHECK (ADD HERE)
    if plan_count == 0:
        st.info("📈 You need to generate your first 7-day plan to see progress.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("⬅️ Back to Dashboard"):
                st.session_state.show_progress = False
                st.session_state.page = "dashboard"
                st.rerun()

        with col2:
            
            if st.button("🚀 Generate First Plan"):
                st.session_state.show_progress = False
                st.session_state.page = "dashboard"
                st.rerun()

        st.stop()   # ⛔ VERY IMPORTANT

    st.subheader("📈 Your Progress Trends")

    progress = get_user_progress(st.session_state.user_id)
    
    if len(progress) == 0:
        st.info("📈 Track your weight after Week 2 to see progress trends.")
        st.stop()

    if not progress:
        st.info("📈 Progress trends will appear after generating your next week plan.")
    else:
        dates = []
        weights = []
        # ✅ Week 1 baseline from user profile
        if weight_db is not None:
            dates.append("Week 1")
            weights.append(weight_db)
        
        # Week-based progress (NO ENUMERATE)
        for week,weight,_,ts in progress:
            dates.append(f"Week {week}")
            weights.append(weight)

        df_weight = pd.DataFrame({
        "Date": dates,
        "Weight (kg)": weights
})

        st.line_chart(df_weight, x="Date", y="Weight (kg)")
    
    if st.button("❌ Close Progress"):
        st.session_state.show_progress = False
        st.rerun()


    if st.button("➡️ Generate Next Week Plan", key="from_progress_trends"):
        st.session_state.show_progress = False
        st.session_state.show_history = False
        st.session_state.page = "week2"
        st.rerun()

# -------- HISTORY --------

if st.session_state.get("show_history"):
    st.subheader("📜 Your Plan History")

    history = get_plan_history(st.session_state.user_id)

    if not history:
        st.info("No plans generated yet.")
    else:
        total = len(history)
        for _,week, plan, ts in history:
            ist_time = ts + timedelta(hours=5, minutes=30)
            with st.expander(f"🗓️ Week {week} — {ist_time.strftime('%d %b %Y, %I:%M %p')}"):
                st.markdown(plan)


    if st.button("❌ Close History"):
        st.session_state.show_history = False
        st.rerun()
    
    if st.button("➡️ Generate Next Week Plan", key="from_history"):
        st.session_state.show_progress = False
        st.session_state.show_history = False
        st.session_state.page = "week2"
        st.rerun()

# -------- PLAN --------
if "plan" not in st.session_state and plan_count == 0:
    st.markdown("### 🧠 Personal Preferences (Optional)")

    preferences = st.text_area(
    "Any food, workout, or lifestyle preferences?",
    placeholder="""
Examples:
- I hate burpees
- Prefer South Indian breakfast
- Knee pain – avoid jumping
- Short workouts (30–40 mins)
- Like yoga once a week
""",
    height=120
)
    if preferences and len(preferences) > 300:
        st.warning("Please keep preferences short and clear (1–3 lines).")
        st.stop()
    cursor = get_cursor()
    cursor.execute("""
INSERT INTO preferences (user_id, key, value)
VALUES (%s, 'user_preferences', %s)
ON CONFLICT (user_id, key)
DO UPDATE SET
    value = EXCLUDED.value
""", (st.session_state.user_id, preferences))
    cursor.close()

    if st.button("Generate 7-Day Plan"):
        with st.spinner("🤖 Generating plan..."):
            prompt = f"""
ROLE: Certified Indian fitness coach and nutritionist.

CRITICAL INSTRUCTIONS:
- Generate a COMPLETE 7-day workout plan AND 7-day diet plan
- Diet MUST use foods commonly eaten in {city}, {state}
- Prefer local, seasonal, and culturally common foods of {city}
- If a food is expensive or unavailable in {city}, suggest a cheaper local alternative
- Budget limit: ₹{budget} per week
- Diet preference: {diet}
- User Preferences: {preferences if preferences else "No specific preferences provided"}
- Student-friendly, hostel/home suitable
- No supplements

PREFERENCE RULE (NON-NEGOTIABLE):
- Respect user preferences strictly
- If a preference conflicts with safety, choose a safer alternative

CRITICAL WORKOUT PLACE RULE (NON-NEGOTIABLE):
- Workout place selected: {workout_place}

IF workout place is "Gym":
- Use ONLY gym-based exercises
- MUST include gym equipment such as:
  - Barbell
  - Dumbbells
  - Machines (leg press, lat pulldown, chest press)
- DO NOT include:
  - Brisk walking
  - Jogging
  - Yoga
  - Bodyweight-only workouts
  - Home cardio (jumping jacks, skipping)

IF workout place is "Home":
- Use ONLY bodyweight or minimal equipment exercises
- DO NOT include gym machines or barbells

FORMAT (USE BULLET POINTS):
- Title
- 7-Day Workout Plan (Day 1 to Day 7)
- 7-Day Diet Plan (Day 1 to Day 7)
  - Breakfast
  - Lunch
  - Dinner
- Hydration note

STRICT RULES:
- NO explanations
- NO reviews
- NO suggestions outside the plan
- Do NOT skip Day 7 
- Output ONLY the plan
"""
            if not state or not city:
                st.error("Please select your fill all the details in the sidebar before generating the plan.")
                st.stop()

            raw=query_ai(prompt)

            validated = query_ai(f"""
You are a fitness plan generator.

CRITICAL RULES (NON-NEGOTIABLE):
- BOTH workout AND diet MUST include Day 1 through Day 7
- Do NOT skip Day 7 under any circumstance
- If any day is missing, regenerate the FULL plan

STRICT OUTPUT RULES:
- Output ONLY the final corrected plan
- Do NOT include reviews, explanations, or suggestions
- Do NOT praise the plan
- Do NOT explain changes
- Do NOT add commentary
- Do NOT mention what was fixed

FORMAT REQUIRED (USE BULLET POINTS EXACTLY LIKE THIS):

- Title

- 7-Day Workout Plan
  - Day 1:
    - Exercise: sets × reps
    - Exercise: sets × reps
  - Day 2:
    - Exercise: sets × reps
  - Day 3:
    - Exercise: sets × reps
  - Day 4:
    - Exercise: sets × reps
  - Day 5:
    - Exercise: sets × reps
  - Day 6:
    - Exercise: sets × reps
  - Day 7:
    - Rest / Light activity

- 7-Day Diet Plan
  - Day 1:
    - Breakfast: ...
    - Lunch: ...
    - Dinner: ...
  - Day 2:
    - Breakfast: ...
    - Lunch: ...
    - Dinner: ...
  - Day 3:
    - Breakfast: ...
    - Lunch: ...
    - Dinner: ...
  - Day 4:
    - Breakfast: ...
    - Lunch: ...
    - Dinner: ...
  - Day 5:
    - Breakfast: ...
    - Lunch: ...
    - Dinner: ...
  - Day 6:
    - Breakfast: ...
    - Lunch: ...
    - Dinner: ...
  - Day 7:
    - Breakfast: ...
    - Lunch: ...
    - Dinner: ...

- Hydration:
  - Drink 2.5–3 liters of water daily

PLAN TO FIX:
{raw}
""")
            # ✅ PART 5 — SAVE / UPDATE USER PROFILE
            upsert_user_profile(
    st.session_state.user_id,
    age, height, weight,
    state, city,
    goal, diet,
    workout_place,
    budget
)
            # 🔄 Refresh profile data after saving
            profile = get_user_profile(st.session_state.user_id)
            if profile:
                (
                age_db, height_db, weight_db,
                state_db, city_db, goal_db,
                diet_db, workout_place_db, budget_db
                ) = profile

            st.session_state.plan=validated
            cursor = get_cursor()
            cursor.execute(
    """INSERT INTO plans(user_id, week, plan) VALUES (%s, %s, %s)  ON CONFLICT(user_id, week)
    DO UPDATE SET
        plan = excluded.plan,
        timestamp = CURRENT_TIMESTAMP""" ,
    (st.session_state.user_id, 1, validated)
)
            cursor.close()

            st.session_state.current_week = 1


if "plan" in st.session_state:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(st.session_state.plan)
    st.markdown("</div>", unsafe_allow_html=True)

# -------- CHAT --------
if "plan" in st.session_state:
    st.info(
    "💡 Pro Tip: Ask for small changes like:\n"
    "- Modify Day 3 workout\n"
    "- Change only diet\n"
    "- Replace dinner options\n\n"
    "This helps avoid incomplete updates."
)

    msg=st.chat_input("Modify plan / ask alternatives")
    if msg:
        with st.spinner("🤖 Updating plan..."):
            updated = query_ai(f"""
You are updating an existing fitness plan.

IMPORTANT CONTEXT (DO NOT IGNORE):
- User location: {city}, {state}
- Diet preference: {diet}
- Weekly budget: ₹{budget}
- Use foods commonly eaten and easily available in {city}
- If a food is expensive or uncommon in {city}, replace it with a cheaper local alternative
CRITICAL RULES (NON-NEGOTIABLE):
- You MUST return the COMPLETE plan
- Workout AND diet must include Day 1 through Day 7
- Do NOT return partial plans
- Do NOT stop mid-output
- Do NOT summarize
- Do NOT omit unchanged days
- If content is long, CONTINUE until the full plan is complete

FORMAT (USE BULLET POINTS):
- Title
- 7-Day Workout Plan (Day 1 to Day 7)
- 7-Day Diet Plan (Day 1 to Day 7)
- Hydration note

CURRENT PLAN:
{st.session_state.plan}

USER REQUEST:
{msg}

OUTPUT:
Return the FULL UPDATED PLAN ONLY.
No explanations.
""")
        # ✅ SAFETY CHECK 1 — must contain all 7 days
        required_days = [f"Day {i}:" for i in range(1, 8)]

        if not updated:
            st.error("❌ AI returned empty response. Plan not updated.")
            st.stop()

        if not all(day in updated for day in required_days):
            st.warning("⚠️ Incomplete plan detected. Regenerating full plan...")

            updated = query_ai(f"""
Regenerate the FULL 7-day fitness plan.

CRITICAL RULES:
- Workout AND diet MUST include Day 1 through Day 7
- Do NOT omit any day
- Do NOT summarize
- Do NOT explain
- Return the COMPLETE plan only

CURRENT PLAN:
{st.session_state.plan}
""")

    # 🔐 Final validation after regeneration
            if not updated or not all(day in updated for day in required_days):
                st.error("❌ Failed to regenerate a complete plan. Existing plan kept safe.")
                st.warning("AI is busy now.Please try again later.")
                st.stop()


        # ✅ SAFETY CHECK 2 — prevent shorter/partial overwrite
        if len(updated) < len(st.session_state.plan) * 0.7:
            st.error("⚠️ Response looks incomplete. Existing plan kept safe.")
            st.stop()
        cursor = get_cursor()
        cursor.execute("""
    UPDATE plans
    SET plan = %s, timestamp = CURRENT_TIMESTAMP
    WHERE user_id = %s AND week = %s
""", (
    updated,
    st.session_state.user_id,
    st.session_state.current_week
))
        cursor.close()
        st.session_state.plan=updated
        st.success("✅ Plan updated successfully")
        st.rerun()

# -------- DOWNLOAD --------
if "plan" in st.session_state:
    file=create_pdf(st.session_state.plan)
    with open(file,"rb") as f:
        st.download_button("Download PDF", f, "FitnessPlan.pdf")
