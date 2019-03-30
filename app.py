#!/usr/bin/env python
import sys
import os  
import dropbox
import cryptography
from Token import TOKEN
from Crypto.PublicKey import RSA
from cryptography.fernet import Fernet
from Crypto.Cipher import PKCS1_OAEP
dbx = dropbox.Dropbox(TOKEN)

#Adding members to group
add_to_group = raw_input("Do you want to add a member? ")
add_to_group = add_to_group.lower()
if add_to_group == "yes":
    group_choice = raw_input("What group would you like to add a new member to? ")
    if(os.path.isfile(group_choice+".txt")):
        if ((os.path.isfile(group_choice+"private_key.pem")) and (os.path.isfile(group_choice+"public_key.pem")) and (os.path.isfile(group_choice+"key.txt"))):
            fd1 = open(group_choice+"private_key.pem", "r")
            private_key = fd1.read() 
            fd1.close()
            fd2 = open(group_choice+"public_key.pem", "r")
            public_key = fd2.read() 
            fd2.close()
            fd3 = open(group_choice+"key.txt", "r")
            key = fd3.read() 
            fd3.close()
            email = raw_input("Please enter a valid email: ")
            b = 0
        else: print("Could not find group keys")
        with open(group_choice+".txt", 'r') as members:
            emails = [line.strip() for line in members]
        for i in emails:
            if i == email:
                print("This person is already in your group")
                members.close()
                b = 1
        if b == 0:
            for entry in dbx.files_list_folder("").entries:
                if entry.name == group_choice:
                    member_selector = dropbox.sharing.MemberSelector.email(email)
                    add_member =  dropbox.sharing.AddMember(member_selector)
                    members = [add_member] 
                    res = dbx.sharing_add_folder_member(entry.shared_folder_id, members,)
            f = open(group_choice+".txt", "a")
            f.write(email+"\n")
            f.close()
            print("Thanks, they've been added to your group.")
    else:
        key = Fernet.generate_key()
        fd = open(group_choice+"key.txt", "wb")
        fd.write(key) 
        fd.close()
        new_key = RSA.generate(4096, e=65537)
        private_key = new_key.exportKey("PEM")
        public_key = new_key.publickey().exportKey("PEM")
        fd = open(group_choice+"private_key.pem", "wb")
        fd.write(private_key)
        fd.close()
        fd = open(group_choice+"public_key.pem", "wb")
        fd.write(public_key)
        fd.close()
        members = open(group_choice+".txt", "wb")
        email = raw_input("Please enter a valid email ")
        members.write(email+"\n")
        members.close()
        print("Thanks, they've been added to your group.")

#Removing from group
remove = raw_input("Do you want to remove a member? ")
remove = remove.lower()
if remove == "yes":
    group_choice = raw_input("Which group would you like to remove a member from? ")
    if(os.path.isfile(group_choice+".txt")):
        email = raw_input("Please enter their email: ")
        with open(group_choice+".txt", "r") as f:
            lines = f.readlines()
        with open(group_choice+".txt", "w") as f:
            for line in lines:
                if line.strip("\n") != email:
                    f.write(line)
        for entry in dbx.files_list_folder("").entries:
                if entry.name == group_choice:
                    member_selector = dropbox.sharing.MemberSelector.email(email)
                    res = dbx.sharing_remove_folder_member(entry.shared_folder_id, member_selector, leave_a_copy = False)
        print("The member you have requested has been successfully removed.")
    else:
        print("You have no group members to remove.")

#Uploading file to group if it exists and creating it otherwise
group_name = raw_input("What group do you want to upload to? ")
upload_file = raw_input("What is the name of the file you'd like to upload? ")
if (os.path.isfile(upload_file)):
    with open(upload_file, "rb") as f:
        data = f.read()
        for memberdata in data:
            fernet = Fernet(key)
            enc_data = fernet.encrypt(data)
    f.close()
    b = 0
    folders = dbx.files_list_folder("")
    for f in folders.entries:
        if f.name == group_name:
            dbx.files_upload(enc_data, '/'+group_name+'/' + upload_file)
            print("File uploaded")
            b = 1
    if b == 0:
        launch = dbx.sharing_share_folder('/'+group_name+'/')
        meta_data = launch.get_complete()
        rsa_key = RSA.importKey(public_key)
        rsa_key = PKCS1_OAEP.new(rsa_key)
        encrypted = rsa_key.encrypt(key)
        fd = open(group_choice+"encrypted_key.txt", "wb")
        fd.write(encrypted)
        fd.close()
        with open(group_choice+"key.txt", "rb") as f:
            data = f.read()
        with open(group_name+".txt", 'r') as f:
            emails = [line.strip() for line in f]
        for i in emails:
            member_select = dropbox.sharing.MemberSelector.email(i)
            access_level = dropbox.sharing.AccessLevel.editor
            add_member = dropbox.sharing.AddMember(member_select, access_level)
            dbx.sharing_add_folder_member(meta_data.shared_folder_id, [add_member])
        print('Folder created for group.')
        dbx.files_upload(enc_data, '/'+group_name+'/' + upload_file)
        dbx.files_upload(encrypted, '/'+group_name+'/' + group_choice+"encrypted_key.txt")
        print("File uploaded")
        b = 1
else: print("Sorry, I cannot find that file. Make sure you typed in the path, name, and extension correctly!")

