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


@views.route("/getPolicy/<policyid>", methods=['GET'])
def policy(policyid):
    ctx = conn.cursor()
    ctx.execute(
        """select pol.product, prd.productname, pol.policy_end_date from CLAIMS.PUBLIC.POLICY POL left 
        join CLAIMS.PUBLIC.PRODUCT prd on POL.product = prd.productid where pol.policyid = '%s' """ % policyid)

    policydetails = ctx.fetchall()
    print(policydetails[0])

    policyArray = []

    for policyitem in policydetails:
        policyObj = {}
        policyObj['product_id'] = policyitem[0]
        policyObj['product_name'] = policyitem[1]
        policyObj['pol_end_date'] = policyitem[2]
        policyArray.append(policyObj)

    return jsonify({'policyDetails': policyArray})


@views.route("/claims", methods=['GET', 'POST'])
def claims():
    if request.method == 'GET':
        # create a cursor
        cnx = conn.cursor()

        cnx.execute(
            """select distinct pl.POLICYID , pr.PRODUCTNAME, nvl(cus.address,'') as address, nvl(cus.address2,'') as address2, nvl(cus.zipcode,'') as  zipcode from 
            "CLAIMS"."PUBLIC"."POLICY" pl inner join "CLAIMS"."PUBLIC"."PRODUCT" pr on pl.PRODUCT = pr.PRODUCTID 
            inner join CLAIMS.PUBLIC.CUSTOMER cus on cus.PARTY_ID = pl.partyid where pl.EMAIL = '%s' """
            % current_user.email)

        policylistDB = cnx.fetchall()

        policylist = []
        for policylistitem in policylistDB:
            itemObj = {}
            itemObj['Policy_ID'] = policylistitem[0]
            itemObj['Policy_desc'] = policylistitem[0] + ' - ' + policylistitem[1] + ' - ' + policylistitem[2] + ' - ' + \
                                     policylistitem[3] + ' - ' + policylistitem[4]
            policylist.append(itemObj)

        return render_template("home.html", policylist=policylist)

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

        updimage = request.files["imgupload"]

        updimage.save(os.path.join(app.config['UPLOAD_FOLDER'], updimage.filename))

        print(updimage)

        new_claim = Claims(claimid=claimid, policynumber=policynumber, product=product, policyenddate=policyenddate,
                           customer_name=customer_name, loss_date=loss_date,
                           loss_amount=loss_amount, cause_of_damage=cause_of_damage, multiparty=multiparty,
                           upload_name=updimage.filename, submittedby=submittedby)
        db.session.add(new_claim)
        db.session.flush()
        db.session.commit()

        if updimage.filename.rsplit('.', 1)[1].lower() == "jpg" or updimage.filename.rsplit('.', 1)[1].lower() == "png":

            uploadcursor = conn.cursor()
            uploadcursor.execute("put file://" + app.config[
                'UPLOAD_FOLDER'] + '\\' + updimage.filename + " @CLAIMSDEMO_DATA auto_compress=false overwrite=true")
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
                'UPLOAD_FOLDER'] + '\\' + updimage.filename + " @CLAIMSDEMO_DATA auto_compress=false overwrite=true")
            uploadcursor.close()
            uploadtextcursor = conn.cursor()
            uploadtextcursor.execute("select read_pdf('@CLAIMSDEMO_DATA/" + updimage.filename + "') as pdf_text")
            upload_text = str(uploadtextcursor.fetchall())
            uploadtextcursor.close()

        new_claim_upload = ClaimUpload(claimid=claimid, upload_text=upload_text)

        db.session.add(new_claim_upload)
        db.session.flush()
        db.session.commit()
        flash('Claim submitted successfully!', category='success')

        stagerefresh = conn.cursor()
        stagerefresh.execute("alter stage claimsdemo_data refresh")
        stagerefresh.close()

        stagingload = conn.cursor()
        stagingload.execute("""insert into CLAIMS.PUBLIC.CLAIMS_UPLOAD_STAGING (claimid, upload_text) select claimid,
        parse_json(ner(UPLOAD_TEXT)) from 
        CLAIMS.PUBLIC.CLAIM_UPLOAD where claimid = '%s' """ % claimid)
        stagingload.close()

    return redirect(url_for('views.claims'))
