from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Define the Alumni model
class Alumni(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    info = db.Column(db.String(200), nullable=False)
    linkedin = db.Column(db.String(200), nullable=True)


# Define the AlumniConnection model for alumni connections
class AlumniConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company1 = db.Column(db.String(100), nullable=False)
    company2 = db.Column(db.String(100), nullable=False)


# Initialize the database
with app.app_context():
    db.create_all()  # Create the database tables if they don't exist


@app.route('/')
def login():
    return render_template('login.html')


@app.route('/select', methods=['POST'])
def select():
    user_type = request.form['user_type']
    if user_type == 'alumni':
        return redirect(url_for('alumni'))
    elif user_type == 'student':
        return redirect(url_for('student_select'))
    return redirect(url_for('login'))


@app.route('/student_select')
def student_select():
    companies = [company[0] for company in db.session.query(Alumni.company).distinct()]
    return render_template('student_select.html', companies=companies)


@app.route('/alumni', methods=['GET', 'POST'])
def alumni():
    companies = db.session.query(Alumni.company).distinct().all()  # Always initialize companies list
    if request.method == 'POST':
        name = request.form['name']
        company = request.form['company']
        role = request.form['role']
        info = request.form['info']
        linkedin = request.form['linkedin']
        new_alumni = Alumni(name=name, company=company, role=role, info=info, linkedin=linkedin)
        db.session.add(new_alumni)
        db.session.commit()

        # Refresh the companies list after adding a new alumni
        companies = db.session.query(Alumni.company).distinct().all()

    return render_template('alumni.html', companies=companies)


@app.route('/student', methods=['POST'])
def student():
    selected_company = request.form['company']
    alumni_at_company = Alumni.query.filter_by(company=selected_company).all()

    # Check if placement is possible
    placement_possible = is_placement_possible(selected_company)

    influential_alumni = get_influential_alumni(selected_company)
    return render_template('student.html', alumni=alumni_at_company, placement_possible=placement_possible,
                           influencers=influential_alumni)


@app.route('/gain_from_alumni', methods=['POST'])
def gain_from_alumni():
    alumni_name = request.form['alumni_name']
    alumni = Alumni.query.filter_by(name=alumni_name).first()
    if alumni:
        return redirect(alumni.linkedin)
    return "Alumni LinkedIn URL not found."


# Function to check if placement is possible
def is_placement_possible(student_company):
    # Fetch all alumni connections from the database
    connections = db.session.query(AlumniConnection).filter(
        (AlumniConnection.company1 == student_company) | (AlumniConnection.company2 == student_company)
    ).all()

    visited = set()
    visited.add(student_company)

    def dfs(company):
        if company == 'CIT':  # You can replace 'CIT' with your target company
            return True
        for conn in connections:
            next_company = conn.company2 if conn.company1 == company else conn.company1
            if next_company not in visited:
                visited.add(next_company)
                if dfs(next_company):
                    return True
        return False

    return dfs(student_company)


# Function to get influential alumni for a company
def get_influential_alumni(company):
    alumni_in_company = Alumni.query.filter_by(company=company).all()
    influencers = {}
    for alumnus in alumni_in_company:
        # Count connections based on company (this can be more sophisticated)
        connections_count = db.session.query(AlumniConnection).filter(
            (AlumniConnection.company1 == alumnus.company) | (AlumniConnection.company2 == alumnus.company)
        ).count()
        influencers[alumnus.name] = connections_count
    return influencers


if __name__ == '__main__':
    app.run(debug=True)
