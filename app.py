#!/usr/bin/env python
import sys
import os  
import dropbox
import cryptography
from Token import TOKEN
from Crypto.PublicKey import RSA
from cryptography.fernet import Fernet
dbx = dropbox.Dropbox(TOKEN)

if ((os.path.isfile("private_key.pem")) and (os.path.isfile("public_key.pem")) and (os.path.isfile("key.txt"))):
    fd1 = open("private_key.pem", "r")
    private_key = fd1.read() 
    fd1.close()
    fd2 = open("public_key.pem", "r")
    public_key = fd2.read() 
    fd2.close()
    fd3 = open("key.txt", "r")
    key = fd3.read() 
    fd3.close()
else:
    key = Fernet.generate_key()
    fd = open("key.txt", "wb")
    fd.write(key) 
    fd.close()
    new_key = RSA.generate(4096, e=65537)
    private_key = new_key.exportKey("PEM")
    public_key = new_key.publickey().exportKey("PEM")
    fd = open("private_key.pem", "wb")
    fd.write(private_key)
    fd.close()
    fd = open("public_key.pem", "wb")
    fd.write(public_key)
    fd.close()

upload_file = raw_input("What is the name of the file you'd like to upload? ")
if (os.path.isfile(upload_file)):
    with open(upload_file, "rb") as f:
        data = f.read()
        fernet = Fernet(key)
        enc_data = fernet.encrypt(data)
        dbx.files_upload(enc_data, '/T-comms testing/' + upload_file)
        print("File uploaded")
else: print("Sorry, I cannot find that file. Make sure you typed in the path, name, and extension correctly!")

