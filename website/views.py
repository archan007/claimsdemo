import random
import os
import subprocess

from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, Flask
from flask_login import login_required, current_user

from .models import Claims, ClaimUpload, User
from . import db, conn

UPLOAD_FOLDER = 'C:\\Users\\HP\\Desktop\\Archan\\uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

views = Blueprint('views', __name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@views.route("/claims", methods=['GET', 'POST'])
def claims():
    # create a cursor
    cursor = conn.cursor()

    cursor.execute(
        'select  pl.POLICYID , pr.PRODUCT  from "CLAIMS"."PUBLIC"."POLICY" pl inner join "CLAIMS"."PUBLIC"."PRODUCT" pr on pl.PRODUCT = pr.PRODUCTID where EMAIL = \'' + current_user.email + '\'')

    policylist = cursor.fetch_pandas_all()
    print(policylist.POLICYID)

    data = request.form
    print(data)
    if request.method == 'POST':
        claimid = random.randint(1, 10000)
        policynumber = request.form.get('policynum')
        product = request.form.get('product')
        policyenddate = request.form.get('polenddate')
        customer_name = request.form.get('clientname')
        loss_date = request.form.get('lossdate')
        loss_amount = request.form.get('lossamount')
        cause_of_damage = request.form.get('notes')
        multiparty = request.form.get('multiparty')
        upload_name = request.form.get('imgupload')
        submittedby = current_user.email

        new_claim = Claims(claimid=claimid, policynumber=policynumber, product=product, policyenddate=policyenddate,
                           customer_name=customer_name, loss_date=loss_date,
                           loss_amount=loss_amount, cause_of_damage=cause_of_damage, multiparty=multiparty,
                           upload_name=upload_name, submittedby=submittedby)
        db.session.add(new_claim)
        db.session.flush()
        db.session.commit()

        updimage = request.files["imgupload"]

        updimage.save(os.path.join(app.config['UPLOAD_FOLDER'], updimage.filename))

        print(updimage)

        if updimage.filename.rsplit('.', 1)[1].lower() == "jpg" or updimage.filename.rsplit('.', 1)[1].lower() == "png":

            uploadcursor = conn.cursor()
            uploadcursor.execute("put file://" + app.config[
                'UPLOAD_FOLDER'] + '\\' + updimage.filename + " @KEYRUS_STAGE auto_compress=false overwrite=true")
            uploadcursor.close()

            x = subprocess.Popen("java -jar /static/tessaract_snowkey.jar" + app.config[
                'UPLOAD_FOLDER'] + '\\' + updimage.filename, stderr=subprocess.PIPE,
                                 stdout=subprocess.PIPE)

            out, err = x.communicate()
            print(out.decode('utf-8'))
            upload_text = out.decode('utf-8')

        else:
            uploadcursor = conn.cursor()
            uploadcursor.execute("put file://" + app.config[
                'UPLOAD_FOLDER'] + '\\' + updimage.filename + " @KEYRUS_STAGE auto_compress=false overwrite=true")
            uploadcursor.close()
            uploadtextcursor = conn.cursor()
            uploadtextcursor.execute("select read_pdf('@keyrus_stage/" + updimage.filename + "') as pdf_text")
            upload_text = str(uploadtextcursor.fetchall())
            uploadtextcursor.close()

        new_claim_upload = ClaimUpload(claimid=claimid, upload_text=upload_text)

        db.session.add(new_claim_upload)
        db.session.flush()
        db.session.commit()
        flash('Claim submitted successfully!', category='success')
    return render_template("home.html", policylist=policylist)
