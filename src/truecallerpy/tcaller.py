#/usr/bin/env python

import os
import sys
import json
import argparse
import colorama
from colorama import Fore, Style
import asyncio
from flask import  jsonify
from truecallerpy.login import login
from truecallerpy.verify_otp import verify_otp
from truecallerpy.search import search_phonenumber, bulk_search
import phonenumbers
from phonenumbers import format_number, PhoneNumberFormat

#gl
homePath = os.path.expanduser("~")
truecallerpyAuthDirPath = os.path.join(homePath, ".config", "truecallerpy")
requestFilePath = os.path.join(truecallerpyAuthDirPath, "request.json")
authKeyFilePath = os.path.join(truecallerpyAuthDirPath, "authkey.json")

# init Function
def tcaller_initFunction():
# Initialize colorama
    colorama.init()

    homePath = os.path.expanduser("~")
    truecallerpyAuthDirPath = os.path.join(homePath, ".config", "truecallerpy")
    requestFilePath = os.path.join(truecallerpyAuthDirPath, "request.json")
    authKeyFilePath = os.path.join(truecallerpyAuthDirPath, "authkey.json")

    if not os.path.exists(truecallerpyAuthDirPath):
        try:
            os.makedirs(truecallerpyAuthDirPath, exist_ok=True)
        except OSError as error:
            print(error)
            exit(1)

# Function to validate phone number


def validate_phone_number(input):
    try:
        pn = phonenumbers.parse(input, None)
        if not phonenumbers.is_valid_number(pn):
            return "Invalid Phone Number"
        return True
    except phonenumbers.NumberParseException:
        return "Enter a valid phone number in International Format"

# Function to validate OTP


def validate_otp(input):
    if len(input) != 6 or not input.isdigit():
        return "Enter a valid 6-digit OTP."
    return True


def check_for_file():
    if not os.path.isfile(authKeyFilePath):
        return False

    try:
        with open(authKeyFilePath) as file:
            json.load(file)
        return True
    except (ValueError, IOError):
        return False

# Function to perform the login process

def doLogin(input):
    try:
        pn = phonenumbers.parse(input, None)
    except phonenumbers.NumberParseException:
        return jsonify({"error":"Enter a valid phone number in International Format"})

    response = None
    response = asyncio.run(login(str(input)))
    print (response)
    if (
        response["data"]["status"] == 1
        or response["data"]["status"] == 9
        or response["data"]["message"] == "Sent"
    ):
        with open(requestFilePath, "w") as file:
            json.dump(response["data"], file, indent=4)
        return jsonify({"status":"OTP sent successfully.","data":response["data"]})
    elif "status" in response and response["data"]["status"] == 6 or response["data"]["status"] == 5:
        if os.path.exists(requestFilePath):
            os.remove(requestFilePath)
        return jsonify({"status":"error", "errorMsg":"You have exceeded the limit of verification attempts.\nPlease try again after some time."})
    else:
        return jsonify({"status":"error", "data":response, "error":"Error occured","message":response["data"]["message"]})


def doVerifyOtp(phone,token,data):

    response1 = asyncio.run(verify_otp(
            str(phone),
             data,
            token,
        ))
    print (response1)
    if "status" in response1["data"] and response1["data"]["status"] == 2 and "suspended" in response1["data"] and not response1["data"]["suspended"]:
            with open(authKeyFilePath, "w") as file:
                json.dump(response1["data"], file, indent=3)
            os.remove(requestFilePath)
            return jsonify(
                {"status":"Logged in successfully","Msg":"Your installationId"+ response1['data']['installationId']}
            )

    elif "status" in response1['data'] and response1["data"]["status"] == 11 or response1["data"]["status"] == 40101:
           return jsonify ({"error": "Invalid OTP","errorMsg":"OTP not valid. Enter the 6-digit OTP received on {phone}."})
    elif "status" in response1["data"] and response1["data"]["status"] == 7:
            return jsonify({"error": "Retries limit exceeded","errorMsg":"Retries on secret code reached for {phone}."})
    elif "suspended" in response1["data"] and response1["data"]["suspended"] == True:
            return jsonify({"error": "Oops... Your account is suspended","errorMsg":"Your account has been suspended by Truecaller."})
    elif "message" in response1["data"]:
            return jsonify({"message":response1['data']['message']})
    else:
            return jsonify({"response":json.dumps(response1, indent=4)})

def searchFunction(args):
    if not check_for_file():
        return jsonify({"status":"error","errorMsg":"Please login to your account."})
    try:
        with open(authKeyFilePath, "r") as auth_key_file:
            data = auth_key_file.read()
            json_auth_key = json.loads(data)
            country_code = json_auth_key["phones"][0]["countryCode"]
            installation_id = json_auth_key["installationId"]

        # Perform the search operation
        search_result = asyncio.run(search_phonenumber(
            args.search, country_code, installation_id))

        if args.name and not args.email:
            try:
                name = search_result["data"]['data'][0]['name']
            except (AttributeError, IndexError, KeyError):
                name = "Unknown Name"

            return jsonify({"status":"error","errorMsg":  name if args.raw else name})

        elif not args.name and args.email:
            try:
                data = search_result["data"].get("data")
                if data and len(data) > 0:
                    internet_addresses = data[0].get("internetAddresses")
                    if internet_addresses and len(internet_addresses) > 0:
                        email = internet_addresses[0].get("id")
                    else:
                        email = "Unknown Email"
                else:
                    email = "Unknown Email"

            except (AttributeError, IndexError, KeyError):
                email = "Unknown Email"

            return jsonify({"status":"error","errorMsg":
                email if args.raw else "Email:"+ email})
        else:
            return jsonify({"status":"ok","searchResult":search_result if args.raw else json.dumps(
                search_result, indent=2)})
    except Exception as error:
        return jsonify({"status":"error","errorMsg": str(error)})
