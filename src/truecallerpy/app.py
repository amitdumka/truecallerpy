
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, jsonify, request
import tcaller
from tcaller import doLogin, doVerifyOtp, searchFunction, tcaller_initFunction

app = Flask(__name__)

tcaller_initFunction()

@app.route('/')
def hello_world():
    return 'AKS Caller Server is running!'

@app.route('/s', methods=['GET'])
def helloWorld():
   if request.method == 'GET':
      return jsonify({"status": "Server is running!"})

@app.route('/status',methods=['GET'])
def sever_status():
    return jsonify({"status":"Server is running","ServerName":"AKS Caller Server"})

@app.route('/getotp',methods=['POST'])
def get_otp():
  return doLogin(request["phoneNumber"])
@app.route('/verifyotp',methods=['POST'])
def get_verify_otp():
  return doVerifyOtp(request["phoneNumber"], request["data"], request["token"])

@app.route('/verifyotps/<string:phoneNumber>/<string:data>/<string:token>',methods=['GET'])
def get_verify_otp_get(phoneNumber,data,token):
    
    return doVerifyOtp(phoneNumber,token,data)
@app.route('/getotps/<string:phoneNumber>',methods=['GET'])
def get_otp_get(phoneNumber):
    print(phoneNumber)
    return doLogin(phoneNumber)
@app.route('/search',methods=['POST'])
def get_search():
    return searchFunction(request)
@app.route('/searchs/<string:search>',methods=['GET'])
def get_search_get(search):
    return searchFunction(search)
if __name__ == "__main__":
   app.run(host='0.0.0.0')