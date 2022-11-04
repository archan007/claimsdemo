from . import db
from flask_login import UserMixin


class Claims(db.Model):
    claimid = db.Column(db.Integer, primary_key=True)
    policynumber = db.Column(db.String(50))
    product = db.Column(db.String(50))
    policyenddate = db.Column(db.String(20))
    customer_name = db.Column(db.String(100))
    loss_date = db.Column(db.DateTime)
    loss_amount = db.Column(db.String(20))
    cause_of_damage = db.Column(db.String(255))
    multiparty = db.Column(db.String(5))
    upload_name = db.Column(db.String(100))
    submittedby = db.Column(db.String(50))


class ClaimUpload(db.Model):
    claimid = db.Column(db.Integer, primary_key=True)
    upload_text = db.Column(db.String(10000))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
