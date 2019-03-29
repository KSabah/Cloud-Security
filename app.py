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

add_to_group = raw_input("Do you want to add a member? ")
add_to_group = add_to_group.lower()
if add_to_group == "yes":
    if(os.path.isfile("memberlist.txt")):
        email = raw_input("Please enter a valid email: ")
        b = 0
        with open('memberlist.txt', 'r') as members:
            emails = [line.strip() for line in members]
        for i in emails:
            if i == email:
                print("This person is already in your group")
                members.close()
                b = 1
        if b == 0:
            f = open("memberlist.txt", "a")
            f.write(email+"\n")
            f.close()
            print("Thanks, they've been added to your group.")
    else:
        members = open("memberlist.txt", "wb")
        email = raw_input("Please enter a valid email ")
        members.write(email+"\n")
        members.close()
        print("Thanks, they've been added to your group.")

upload_file = raw_input("What is the name of the file you'd like to upload? ")
if (os.path.isfile(upload_file)):
    with open(upload_file, "rb") as f:
        folders = dbx.files_list_folder("")
        data = f.read()
        for memberdata in data:
            fernet = Fernet(key)
            enc_data = fernet.encrypt(data)
    b = 0
    for f in folders.entries:
        if f.name == "group":
            dbx.files_upload(enc_data, '/group/' + upload_file)
            print("File uploaded")
            b = 1
    if b == 0:
        launch = dbx.sharing_share_folder('/group/')
        meta_data = launch.get_complete()
        with open('memberlist.txt', 'r') as f:
            emails = [line.strip() for line in f]
        for i in emails:
            member_select = dropbox.sharing.MemberSelector.email(i)
            access_level = dropbox.sharing.AccessLevel.editor
            add_member = dropbox.sharing.AddMember(member_select, access_level)
            dbx.sharing_add_folder_member(meta_data.shared_folder_id, [add_member])
        print('Folder created for group.')
        dbx.files_upload(enc_data, '/group/' + upload_file)
        print("File uploaded")
        b = 1
else: print("Sorry, I cannot find that file. Make sure you typed in the path, name, and extension correctly!")

