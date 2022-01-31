#!/usr/bin/python3
from datetime import datetime, timedelta
from flask import Flask, request, flash, url_for, redirect, render_template, session, g, send_from_directory
from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager, login_required, login_user, current_user, logout_user, UserMixin
from flask_qrcode import QRcode
import os
from bitcoinlib.wallets import wallet_create_or_open, wallet_delete, wallet_delete_if_exists, WalletError
# from werkzeug.exceptions import abort
import getopt
import sys
import dcgenerator
import logging

import helpers
import mailer

_logger = logging.getLogger(__name__)
# default path
global_datastore_path = "../data"

app = Flask(__name__)
app.config['WALLET_NAME'] = 'lemonadestand_v2'

# Always reset the info when they land here
price_one_point_day_USD = float(os.getenv("AMOUNT_USD_POINT_DAY", 0.35))
price_start_min_points = 90

# 15 minutes session time to store the pricing info
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)

qrcode = QRcode(app)

try:
    # -d handy for running in a container etc
    opts, args = getopt.getopt(sys.argv[1:], "d:")
except getopt.GetoptError:
    print('app.py -d [datastore path]')
    sys.exit(2)

for opt, arg in opts:
    if opt == '-d':
        print("Datastore:", arg)
        global_datastore_path = arg

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}/lemonade-stand.db'.format(global_datastore_path)
app.config['SECRET_KEY'] = helpers.init_app_secret(global_datastore_path)
db = SQLAlchemy(app)

# @todo
#class LemonadeCreditsBalance(db.Model):
#    id = db.Column('id', db.Integer, primary_key=True)
#    instance_id = db.Column('instance_id', db.Integer)
#    event_date = db.Column(db.DateTime())
#    event_text = db.Column(db.String(50))
#    points = db.Column('points', db.Integer)


class PaidInstance(db.Model):
    # https://docs.sqlalchemy.org/en/14/core/type_basics.html
    id = db.Column('instance_id', db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    instance_name = db.Column(db.String(100))
    instance_image = db.Column(db.String(255))
    date_start = db.Column(db.DateTime())
    btc_address = db.Column(db.String(50))
    is_active = db.Column(db.Boolean(), default=False)
    network = db.Column(db.String(100))
    salted_pass = db.Column(db.String(100))

    # If not zero, use this rate satoshis/USD
    # After payment, unset this rate and use the market rate going forwards
    # Also can be used as a discount rate
    hold_rate = db.Column(db.BigInteger())

    # bitcoinlib and others store transactions as total units, smarter this way
    # 1 btc=100 million satoshis, 100,000,000
    requested_amount_btc = db.Column(db.BigInteger())
    requested_amount_usd = db.Column(db.BigInteger())

    def __init__(self, id=0, email="", btc_address="", hold_rate=0, network="", date_start=0, instance_name="", is_active=False,
                 instance_image="", salted_pass="", requested_amount_btc=0, requested_amount_usd=0):
        self.name = id
        self.email = email
        self.instance_name = instance_name
        self.date_start = date_start
        self.is_active = is_active
        self.requested_amount_btc = requested_amount_btc
        self.requested_amount_usd = requested_amount_usd
        self.hold_rate = hold_rate
        self.instance_image = instance_image
        self.btc_address = btc_address
        self.network = network
        self.salted_pass = salted_pass

db.create_all()


def convert_usd_to_bitcoin_satoshis(amount_usd=0.0):
    # @todo cache this for a few minutes
    import requests
    response = requests.get('https://blockchain.info/ticker')
    info = response.json()
    converted = round(amount_usd / info["USD"]["15m"], 8)
    # I think this is right, 100,000,000 satoshi in 1 BTC
    satoshis = int(converted * 100000000)
    return {'satoshi': satoshis, 'bitcoin': converted, 'rate': info["USD"]["15m"]}

# on submit we create the payment address and send them the request for payment
@app.route('/start', methods=['GET', 'POST'])
def letsgo():
    import forms

    btc_amount = convert_usd_to_bitcoin_satoshis(price_one_point_day_USD * price_start_min_points)

    session['btc_payment_amount'] = btc_amount
    if 'btc_payment_address' in session:
        del session['btc_payment_address']

    form = forms.StartForm(request.form)
    if request.method == 'GET' or not form.validate():
        btc_amount_str = "{:.8f}".format(session['btc_payment_amount']['bitcoin'])
        return render_template('start.html', form=form, btc_amount=btc_amount_str)

    if request.method == 'POST' and form.validate():

        if not 'btc_payment_amount' in session:
            flash("Sorry, BTC quoted amount timed out after 15 minutes, please try again.")
            return redirect(url_for('letsgo'))

        # @todo BTC_NETWORK "bitcoin" for production

        instance_name = helpers.generate_random_instance_name()
        btc_keyname = "{} - {}".format(form.data['email'], instance_name)

        wallet = wallet_create_or_open(name=app.config['WALLET_NAME'],
                                       network=os.getenv("BTC_NETWORK", "testnet"),
                                       db_uri=os.getenv("BTC_WALLET_URI", "sqlite:///{}/wallet-{}.db".format(global_datastore_path, os.getenv("BTC_NETWORK", "testnet"))))

        btc_key = wallet.new_key(network=os.getenv("BTC_NETWORK", "testnet"), name=btc_keyname)
        session['btc_payment_address'] = btc_key.address
        session['instance_name'] = instance_name

        # @todo and private key?
        # In the future they could choose what payment method they want in a dropdown/icons/etc
        instance = PaidInstance(id=0,
                                email=request.form['email'],
                                date_start=datetime.now(),
                                is_active=False,
                                instance_name=instance_name,
                                network=os.getenv("BTC_NETWORK", "testnet"),
                                btc_address=session['btc_payment_address'],
                                requested_amount_btc=session['btc_payment_amount']['bitcoin'],
                                instance_image=os.getenv("HOSTED_IMAGE", "dgtlmoon/changedetection.io:latest"))

        email_body = """
You're almost there!

Please pay {} BTC to {} .

This covers you for 90 days of credits (1 day = 1 lemonade fresh credit)

We will send a confirmation email once payment is received.

Then your instance will be available at https://lemonade.changedetection.io/{}

Your super fresh crew

    """.format(session['btc_payment_amount']['bitcoin'], session['btc_payment_address'], instance_name)

        mailer.send_email(to=request.form['email'], subject="Your LemonadeFresh changedetection.io instance payment info",
                          message_body=email_body)
        db.session.add(instance)
        db.session.commit()

        # Send the email
        # flash('Please check your email address for further instructions')
        return redirect(url_for('pay', btc_address=btc_key.address))

@app.route('/contact', methods=['GET','POST'])
def contact():
    import forms
    form = forms.ContactForm(request.form)
    if request.method == 'GET' or not form.validate():

        return render_template('contact.html', form=form)

    if request.method == 'POST' and form.validate():

        mailer.send_email(to="leigh@morresi.net",
                          subject="Lemonfresh contact",
                          message_body="""
sender address: {}

text:
{}
--
""".format(form.email.data, form.body.data))

        # Send the email
        # flash('Please check your email address for further instructions')
        flash("Message received! thank you!")
        return redirect(url_for('letsgo'))

# they clicked the link in the email, now this shows the QR code and loops to see if its paid
# if its paid (is_active=1), redirect to their instance name
@app.route('/pay', methods=['GET'])
def pay():
    # Show the QR code with the amount
    # ajax callback to check
    # .scan() the btc address for payments
    # when it changes from active=0 to active=1, then rebuild docker compose, run docker-compose up -d
    # a note to say 'keep this page open'
    # request.args.get('uuid')

    if not 'btc_payment_amount' in session:
        flash("Sorry, BTC quoted amount timed out after 15 minutes, please try again.")
        return redirect(url_for('letsgo'))

    instance = db.session.query(PaidInstance).filter_by(btc_address=request.args.get('btc_address')).first()

    if instance.is_active:
        return redirect("/" + instance.instance_name)

    # extra check, if get.btc_address is_active then redirect to their instance
    qr_code_string = "bitcoin:{}?amount={}&message={}".format(session['btc_payment_address'], session['btc_payment_amount']['bitcoin'],
                                                              "https://changedetection.io/lemonade/" + instance.instance_name)
    btc_amount_str = "{:.8f}".format(session['btc_payment_amount']['bitcoin'])

    return render_template('btc_payment.html',
                           qr_code_string=qr_code_string,
                           btc_amount=btc_amount_str,
                           instance_name=session['instance_name'],
                           btc_payment_address=session['btc_payment_address'])


# I bet in the future, some external pay system would call in with an API to say that it's paid for
# Process instances made less than 2 hours ago to be safe, we allow 1 hour of payment window.
# move to its own file.py ? I was going to have this callable via AJAX, but better for one thread to via crontab+flock
@app.route('/sync', methods=['GET'])
def sync_unpaid_accounts():
    import datetime
    import mailer
    import secrets

    output = "Nothing new"

    forward_fee = int(os.getenv("BTC_FORWARD_FEE", 1024))
    current_time = datetime.datetime.now()
    two_hours_ago = current_time - datetime.timedelta(hours=2)

    wallet = wallet_create_or_open(name=app.config['WALLET_NAME'],
                                   network=os.getenv("BTC_NETWORK", "testnet"),
                                   db_uri=os.getenv("BTC_WALLET_URI", "sqlite:///{}/wallet-{}.db".format(global_datastore_path, os.getenv("BTC_NETWORK", "testnet"))))

    # Find keys for instances, that are zero balance and the instance is not active
    for key in wallet.keys(network=os.getenv("BTC_NETWORK", "testnet")):
        instance = PaidInstance.query.filter(PaidInstance.btc_address == key.address,
                                             PaidInstance.is_active == False,
                                             PaidInstance.date_start >= two_hours_ago).first()
        if instance:
            # Scan for keys with unspent outputs, apparently this is the fastest way ?
            # wallet.utxos_update(networks=os.getenv("BTC_NETWORK", "testnet"), key_id=key.id)
            # Or..
            wallet.transactions_update(network=os.getenv("BTC_NETWORK", "testnet"), key_id=key.id)

    # .key above wont be set by reference, so run the loop again and update instances
    for key in wallet.keys(network=os.getenv("BTC_NETWORK", "testnet")):
        instance = PaidInstance.query.filter(PaidInstance.btc_address == key.address,
                                             PaidInstance.is_active == False,
                                             PaidInstance.date_start >= two_hours_ago).first()
        if instance and key.balance > 0:
            _logger.info("Payment found for instance name %s on %s" % (instance.instance_name, key.address))

            instance.is_active = True
            plain_pass = secrets.token_urlsafe(8)
            instance.salted_pass = helpers.salted_password(password=plain_pass)

            # Record the payment
            db.session.commit()

            email_body = """Awesome!

Payment received!

Your instance is available at https://lemonade.changedetection.io/{} and your password is {}


Your super fresh crew!
            """.format(str(instance.instance_name), plain_pass)

            mailer.send_email(to=instance.email,
                              subject="Your LemonadeFresh changedetection.io instance is READY!",
                              message_body=email_body)

            output = "new customer"

    # Always rebuild
    dcgenerator.rebuild_docker_compose(PaidInstance, path_to_docker_compose_file=global_datastore_path)

    # forward any new unspent inputs out somewhere, dont keep them on the server
    # seems to be more reliable than send of total wallet
    # wallet.transactions_update(network=os.getenv("BTC_NETWORK", "testnet"), key_id=608)

    for key in wallet.keys(network=os.getenv("BTC_NETWORK", "testnet")):
        if key.balance:

            try:
                t = wallet.send_to(to_address=os.getenv("BTC_FORWARD_ADDRESS", "tb1q4fzu384ffu70js67h7vvcq837pvqe97kgv306q"),
                                   network=os.getenv("BTC_NETWORK", "testnet"),
                                   amount=int(key.balance - forward_fee),
                                   fee=forward_fee)
            except WalletError:
                # https://github.com/1200wd/bitcoinlib/issues/186 ?
                _logger.error(
                    "Trying to send %s but got WalletError, maybe spending unconfirmed ouputs https://github.com/1200wd/bitcoinlib/issues/186" % (
                        key.address))
                pass

    # Just for debugging https://githuob.com/1200wd/bitcoinlib/issues/186
    # wallet_balance = wallet.balance(network=os.getenv("BTC_NETWORK", "testnet"))

    return output


if __name__ == '__main__':

    import eventlet.wsgi

    # for running in proxy_pass subdirs
    if os.getenv('USE_X_SETTINGS'):
        print("USE_X_SETTINGS is ENABLED\n")
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1, x_host=1)

    eventlet.wsgi.server(eventlet.listen(('', 10000)), app)
