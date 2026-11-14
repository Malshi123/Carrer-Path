import os
import mysql.connector
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

def get_db():
    # Opens a new connection to the MySQL database
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",          # XAMPP default is an empty password
        database="career_platform",
    )

app = Flask(__name__)
app.secret_key = "any-secret-text"

# Temporary user list (will be replaced by MySQL later)
users = {
    "nethsarani": {"password": generate_password_hash("1234"), "role": "Student"},
    "mentor1": {"password": "1234", "role": "Mentor"},
}

# Skills required for each career
careers = {
    "Software Engineer": ["Python", "HTML/CSS", "SQL", "Java"],
    "Data Scientist": ["Python", "SQL", "Machine Learning"],
    "UI/UX Designer": ["Figma", "HTML/CSS"],
}

# Recommended course for each skill
courses = {
    "Python": "Python for Beginners",
    "HTML/CSS": "HTML & CSS Basics",
    "SQL": "SQL Fundamentals",
    "Machine Learning": "Intro to Machine Learning",
    "Figma": "Figma UI Design",
    "Java": "Java Programming Basics",
}

# Quiz questions (2 per category)
questions = [
    {"question": "What is the output of print(len('abc')) in Python?",
     "options": ["2", "3", "4", "Error"], "answer": "3", "category": "coding"},
    {"question": "Which keyword is used to repeat code many times?",
     "options": ["if", "for", "def", "import"], "answer": "for", "category": "coding"},
    {"question": "What is the average of 4, 6 and 8?",
     "options": ["4", "6", "8", "18"], "answer": "6", "category": "maths"},
    {"question": "What is 25% of 200?",
     "options": ["25", "40", "50", "75"], "answer": "50", "category": "maths"},
    {"question": "What does UI stand for?",
     "options": ["User Interface", "Unique Input", "Universal Integration", "User Idea"],
     "answer": "User Interface", "category": "design"},
    {"question": "Which tool is commonly used to design app screens?",
     "options": ["MySQL", "Figma", "Git", "Excel"], "answer": "Figma", "category": "design"},
]

# Which quiz category matches which career
career_category = {
    "Software Engineer": "coding",
    "Data Scientist": "maths",
    "UI/UX Designer": "design",
}


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        #Look for this user in the database
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND role = %s",
            (username, role),
        )
        user = cursor.fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):

            session["username"] = user["username"]
            return redirect("/student")

        return render_template("login.html", error="Incorrect username or password!")

    return render_template("login.html")


@app.route("/student", methods=["GET", "POST"])
def student():
    # Redirect to login if the user is not logged in
    if "username" not in session:
        return redirect("/login")

    data = {"username": session["username"]}

    if request.method == "POST":
        # When the Analyze button is clicked
        if "analyze_btn" in request.form:
            my_skills = request.form.getlist("skills")

            # Find the career with the highest skill match percentage
            quiz_scores = session.get("quiz")

            best_career = None
            best_percent = -1
            for career, needed in careers.items():
                have = [s for s in needed if s in my_skills]
                skill_percent = len(have) / len(needed) * 100

                if quiz_scores:
                    # Each category has 2 questions, so score / 2 * 100
                    quiz_percent = quiz_scores[career_category[career]] / 2 * 100
                    percent = skill_percent * 0.6 + quiz_percent * 0.4
                else:
                    percent = skill_percent

                if percent > best_percent:
                    best_percent = percent
                    best_career = career

            # Skills the student is missing for the best career
            gaps = [s for s in careers[best_career] if s not in my_skills]

            data["career"] = best_career
            data["user_skills"] = my_skills
            data["skill_gaps"] = gaps
            data["roadmap"] = {g: courses[g] for g in gaps}

        # When the Book button is clicked
        if "book_btn" in request.form:
            mentor = request.form["mentor"]
            date = request.form["date"]
            data["booking_msg"] = f"Booked! Session with {mentor} on {date}."

    return render_template("student.html", **data)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm"]
        role = request.form["role"]
        
        if password != confirm:
            return render_template("register.html", error="Passwords do not match.")

        db = get_db()
        cursor = db.cursor()

        # Check if the username is already taken
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            db.close()
            return render_template("register.html", error="That username is already taken.")
        
    
        # Save the new user permanently
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, password_hash, role),
        )
        db.commit()
        db.close()
        
        return redirect("/login")

    return render_template("register.html")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":
        scores = {"coding": 0, "maths": 0, "design": 0}
        for i, q in enumerate(questions):
            # Compare the chosen answer with the correct one
            if request.form.get(f"q{i}") == q["answer"]:
                scores[q["category"]] += 1
        session["quiz"] = scores
        return redirect("/student")

    return render_template("quiz.html", questions=questions)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True, port=5001)