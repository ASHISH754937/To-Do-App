import os
import pymysql
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import urllib.parse
from dotenv import load_dotenv  
from sqlalchemy.sql import func 

load_dotenv()

app = Flask(__name__)

DB_HOST = os.getenv("MYSQLHOST", "mysql.railway.internal")
DB_USER = os.getenv("MYSQLUSER", "root")
DB_PASSWORD = os.getenv("MYSQLPASSWORD")  
DB_NAME = os.getenv("MYSQLDATABASE", "railway")
DB_PORT = os.getenv("MYSQLPORT", "3306")

# ✅ Secure password encoding
password = urllib.parse.quote_plus(DB_PASSWORD)


app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Todo(db.Model):
    SrNo = db.Column(db.Integer, primary_key=True)
    Task = db.Column(db.String(250), nullable=False)
    Date = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.String(50), default='Pending')
    CompletedDate = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"{self.SrNo}, {self.Task}, {self.Status}"

    

@app.route("/", methods=['GET', 'POST'])
@app.route("/Home", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        task_content = request.form.get('task')  # Get task from form
        if task_content:
            todo = Todo(Task=task_content)  # Create new task
            db.session.add(todo)
            db.session.commit()
            return redirect(url_for('home'))  # Refresh page after submission

    alltodo = Todo.query.all()  # Fetch all tasks
    return render_template('index.html', title='Home', alltodo=alltodo)


@app.route("/complete/<int:srno>", methods=['POST'])
def complete_task(srno):
    todo = Todo.query.get_or_404(srno)
    
    if todo.Status == "Pending":  
        todo.Status = "Completed"
        todo.CompletedDate = datetime.utcnow() 
        db.session.commit()

    return redirect(url_for('home'))


@app.route("/delete/<int:srno>", methods=['POST'])
def delete_task(srno):
    todo = Todo.query.get_or_404(srno)
    if todo.Status == 'Completed':  # ✅ Fixed here
        return "Completed tasks cannot be deleted.", 403  # Prevent deletion
    
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('home'))  


@app.route("/Completed", methods=['GET'])
def showhistory():
    filter_date = request.args.get('date')
    selected_date = request.args.get('date', '')

    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()  
            completed_tasks = Todo.query.filter(
                Todo.Status == "Completed",
                func.date(Todo.CompletedDate) == selected_date
            ).all()
        except ValueError:
            completed_tasks = []
    else:
        completed_tasks = Todo.query.filter(Todo.Status == "Completed").all()
        
    return render_template('completed.html', completed_tasks=completed_tasks, selected_date=filter_date)


@app.route("/About")
def aboutsection():
    return render_template("about.html")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
