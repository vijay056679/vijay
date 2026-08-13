import os
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "recovery.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "case-file-dev-key"

db = SQLAlchemy(app)

STATUS_ACTIVE = "Active"
STATUS_OVERDUE = "Overdue"
STATUS_RECOVERED = "Recovered"
STATUS_DEFAULTED = "Defaulted"
ALL_STATUSES = [STATUS_ACTIVE, STATUS_OVERDUE, STATUS_RECOVERED, STATUS_DEFAULTED]


class Borrower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    address = db.Column(db.String(250))
    loans = db.relationship("Loan", backref="borrower", cascade="all, delete-orphan")


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(20), unique=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey("borrower.id"), nullable=False)
    principal_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=0)
    outstanding_amount = db.Column(db.Float, nullable=False)
    loan_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default=STATUS_ACTIVE)
    payments = db.relationship("Payment", backref="loan", cascade="all, delete-orphan")
    notes = db.relationship("CollectionNote", backref="loan", cascade="all, delete-orphan")

    def refresh_status(self):
        if self.outstanding_amount <= 0:
            self.status = STATUS_RECOVERED
        elif self.status == STATUS_DEFAULTED:
            pass
        elif self.due_date < date.today():
            self.status = STATUS_OVERDUE
        else:
            self.status = STATUS_ACTIVE

    def days_overdue(self):
        if self.due_date < date.today() and self.outstanding_amount > 0:
            return (date.today() - self.due_date).days
        return 0


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loan.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, default=date.today)
    method = db.Column(db.String(40))
    note = db.Column(db.String(250))


class CollectionNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loan.id"), nullable=False)
    agent_name = db.Column(db.String(80))
    action = db.Column(db.String(60))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def next_case_number():
    count = Loan.query.count() + 1
    return f"CF-{datetime.now().year}-{count:04d}"


def sync_all_statuses():
    changed = False
    for loan in Loan.query.all():
        prev = loan.status
        loan.refresh_status()
        if loan.status != prev:
            changed = True
    if changed:
        db.session.commit()


@app.route("/")
def dashboard():
    sync_all_statuses()
    loans = Loan.query.all()
    total_outstanding = sum(l.outstanding_amount for l in loans)
    total_recovered = db.session.query(func.coalesce(func.sum(Payment.amount), 0.0)).scalar() or 0
    overdue_loans = [l for l in loans if l.status == STATUS_OVERDUE]
    active_count = len([l for l in loans if l.status == STATUS_ACTIVE])
    recovered_count = len([l for l in loans if l.status == STATUS_RECOVERED])
    defaulted_count = len([l for l in loans if l.status == STATUS_DEFAULTED])
    recent_payments = Payment.query.order_by(Payment.payment_date.desc(), Payment.id.desc()).limit(6).all()
    top_overdue = sorted(overdue_loans, key=lambda l: l.days_overdue(), reverse=True)[:5]
    recovery_rate = 0
    total_principal = sum(l.principal_amount for l in loans)
    if total_principal > 0:
        recovery_rate = round((total_recovered / total_principal) * 100, 1)

    return render_template(
        "dashboard.html",
        total_loans=len(loans),
        total_outstanding=total_outstanding,
        total_recovered=total_recovered,
        overdue_count=len(overdue_loans),
        active_count=active_count,
        recovered_count=recovered_count,
        defaulted_count=defaulted_count,
        recent_payments=recent_payments,
        top_overdue=top_overdue,
        recovery_rate=recovery_rate,
    )


@app.route("/loans")
def loans_list():
    sync_all_statuses()
    status_filter = request.args.get("status", "All")
    query = Loan.query
    if status_filter in ALL_STATUSES:
        query = query.filter_by(status=status_filter)
    loans = query.order_by(Loan.due_date.asc()).all()
    return render_template("loans.html", loans=loans, statuses=ALL_STATUSES, active_filter=status_filter)


@app.route("/loans/new", methods=["GET", "POST"])
def add_loan():
    borrowers = Borrower.query.order_by(Borrower.name).all()
    if request.method == "POST":
        borrower_choice = request.form.get("borrower_id")
        if borrower_choice == "new":
            name = request.form.get("new_name", "").strip()
            if not name:
                flash("Borrower name is required to open a new case.", "error")
                return redirect(url_for("add_loan"))
            borrower = Borrower(
                name=name,
                email=request.form.get("new_email", "").strip(),
                phone=request.form.get("new_phone", "").strip(),
                address=request.form.get("new_address", "").strip(),
            )
            db.session.add(borrower)
            db.session.flush()
        else:
            borrower = Borrower.query.get(int(borrower_choice))

        try:
            principal = float(request.form.get("principal_amount", 0))
            rate = float(request.form.get("interest_rate", 0) or 0)
            due = datetime.strptime(request.form.get("due_date"), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Please provide valid loan figures and a due date.", "error")
            return redirect(url_for("add_loan"))

        loan = Loan(
            case_number=next_case_number(),
            borrower=borrower,
            principal_amount=principal,
            interest_rate=rate,
            outstanding_amount=principal,
            due_date=due,
        )
        loan.refresh_status()
        db.session.add(loan)
        db.session.commit()
        flash(f"Case {loan.case_number} opened for {borrower.name}.", "success")
        return redirect(url_for("loan_detail", loan_id=loan.id))

    return render_template("add_loan.html", borrowers=borrowers, today=date.today().isoformat())


@app.route("/loans/<int:loan_id>")
def loan_detail(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    loan.refresh_status()
    db.session.commit()
    payments = Payment.query.filter_by(loan_id=loan.id).order_by(Payment.payment_date.desc()).all()
    notes = CollectionNote.query.filter_by(loan_id=loan.id).order_by(CollectionNote.created_at.desc()).all()
    return render_template("loan_detail.html", loan=loan, payments=payments, notes=notes)


@app.route("/loans/<int:loan_id>/payment", methods=["POST"])
def add_payment(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        amount = 0
    if amount <= 0:
        flash("Enter a payment amount greater than zero.", "error")
        return redirect(url_for("loan_detail", loan_id=loan.id))

    amount = min(amount, loan.outstanding_amount)
    payment = Payment(
        loan_id=loan.id,
        amount=amount,
        method=request.form.get("method", "Bank Transfer"),
        note=request.form.get("note", ""),
    )
    loan.outstanding_amount = round(loan.outstanding_amount - amount, 2)
    loan.refresh_status()
    db.session.add(payment)
    db.session.commit()
    flash(f"Payment of ₹{amount:,.2f} logged against {loan.case_number}.", "success")
    return redirect(url_for("loan_detail", loan_id=loan.id))


@app.route("/loans/<int:loan_id>/note", methods=["POST"])
def add_note(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    note = CollectionNote(
        loan_id=loan.id,
        agent_name=request.form.get("agent_name", "Unassigned"),
        action=request.form.get("action", "Call"),
        note=request.form.get("note", ""),
    )
    db.session.add(note)
    db.session.commit()
    flash("Collection activity recorded.", "success")
    return redirect(url_for("loan_detail", loan_id=loan.id))


@app.route("/loans/<int:loan_id>/status", methods=["POST"])
def update_status(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    new_status = request.form.get("status")
    if new_status in ALL_STATUSES:
        loan.status = new_status
        db.session.commit()
        flash(f"Case {loan.case_number} marked {new_status}.", "success")
    return redirect(url_for("loan_detail", loan_id=loan.id))


@app.route("/borrowers")
def borrowers_list():
    borrowers = Borrower.query.order_by(Borrower.name).all()
    return render_template("borrowers.html", borrowers=borrowers)


@app.route("/borrowers/<int:borrower_id>")
def borrower_detail(borrower_id):
    borrower = Borrower.query.get_or_404(borrower_id)
    return render_template("borrower_detail.html", borrower=borrower)


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)
