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
    group_name = raw_input("What group would you like to add a new member to? ")
    if not os.path.exists('Groups/'):
        os.makedirs('Groups/')
    else:
        if(os.path.isfile("Groups/"+group_name+".txt")):
            if ((os.path.isfile(group_name+"private_key.pem")) and (os.path.isfile(group_name+"public_key.pem")) and (os.path.isfile(group_name+"key.txt"))):
                email = raw_input("Please enter a valid email: ")
                b = 0
            with open("Groups/"+group_name+".txt") as members:
                emails = [line.strip() for line in members]
            for i in emails:
                if i == email:
                    print("This person is already in your group")
                    members.close()
                    b = 1
            if b == 0:
                for entry in dbx.files_list_folder("").entries:
                    if entry.name == group_name:
                        member_selector = dropbox.sharing.MemberSelector.email(email)
                        add_member =  dropbox.sharing.AddMember(member_selector)
                        members = [add_member] 
                        res = dbx.sharing_add_folder_member(entry.shared_folder_id, members,)
                f = open("Groups/"+group_name+".txt", "a")
                f.write(email+"\n")
                f.close()
                print("Thanks, they've been added to your group.")
        else:
            key = Fernet.generate_key()
            fd = open(group_name+"key.txt", "wb")
            fd.write(key) 
            fd.close()
            new_key = RSA.generate(4096, e=65537)
            private_key = new_key.exportKey("PEM")
            public_key = new_key.publickey().exportKey("PEM")
            fd = open(group_name+"private_key.pem", "wb")
            fd.write(private_key)
            fd.close()
            fd = open(group_name+"public_key.pem", "wb")
            fd.write(public_key)
            fd.close()
            members = open("Groups/"+group_name+".txt", "wb")
            email = raw_input("Please enter a valid email ")
            members.write(email+"\n")
            members.close()
            print("Thanks, they've been added to your group.")

    

#Removing from group
remove = raw_input("Do you want to remove a member? ")
remove = remove.lower()
if remove == "yes":
    group_name = raw_input("Which group would you like to remove a member from? ")
    if(os.path.isfile("Groups/"+group_name+".txt")):
        email = raw_input("Please enter their email: ")
        with open("Groups/"+group_name+".txt", "r") as f:
            lines = f.readlines()
        with open("Groups/"+group_name+".txt", "w") as f:
            for line in lines:
                if line.strip("\n") != email:
                    f.write(line)
        for entry in dbx.files_list_folder("").entries:
                if entry.name == group_name:
                    member_selector = dropbox.sharing.MemberSelector.email(email)
                    res = dbx.sharing_remove_folder_member(entry.shared_folder_id, member_selector, leave_a_copy = False)
        print("The member you have requested has been successfully removed.")
        print("Re-encrypting files...")
        f = open(group_name+"private_key.pem", "r")
        old_private_key = f.read() 
        f.close()
        rsakey = RSA.importKey(old_private_key)
        old_private_key = PKCS1_OAEP.new(rsakey)
        f = open(group_name+"key.txt", "r")
        old_key = f.read() 
        f.close()
        old_key = Fernet(old_key)

        new_key = Fernet.generate_key()
        f = open(group_name+"key.txt", "wb")
        f.write(new_key) 
        f.close()
        n_key = RSA.generate(4096, e=65537)
        new_private_key = n_key.exportKey("PEM")
        new_public_key = n_key.publickey().exportKey("PEM")
        f = open(group_name+"private_key.pem", "wb")
        f.write(new_private_key)
        f.close()
        f = open(group_name+"public_key.pem", "wb")
        f.write(new_public_key)
        f.close()

        response = dbx.files_list_folder("/"+group_name+"/")
        for file in response.entries:
            path = "/"+group_name+"/"+file.name
            if file.name == group_name+"encrypted_key.txt":
                dbx.files_delete(path)
                rsa_key = RSA.importKey(new_public_key)
                rsa_key = PKCS1_OAEP.new(rsa_key)
                encrypted = rsa_key.encrypt(new_key)
                f = open(group_name+"encrypted_key.txt", "wb")
                f.write(encrypted)
                f.close()
                dbx.files_upload(encrypted, path)
            else:
                metadata, f = dbx.files_download(path)
                old_data = open(file.name, 'wb')
                old_data.write(old_key.decrypt(f.content))
                old_data.close()
                dbx.files_delete(path)  
                with open(file.name, "rb") as f:
                    data = f.read()
                    for memberdata in data:
                        fernet = Fernet(new_key)
                        enc_data = fernet.encrypt(data)
                f.close()
                dbx.files_upload(enc_data, path)
        print("Re-encryption successful.")
    else:
        print("You have no group members to remove.")

#Uploading file to group if it exists and creating it otherwise
group_name = raw_input("What group do you want to upload to? ")
upload_file = raw_input("What is the name of the file you'd like to upload? ")
if (os.path.isfile(upload_file)):
    fd2 = open(group_name+"public_key.pem", "r")
    public_key = fd2.read() 
    fd2.close()
    fd3 = open(group_name+"key.txt", "r")
    key = fd3.read() 
    fd3.close()
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
        fd = open(group_name+"encrypted_key.txt", "wb")
        fd.write(encrypted)
        fd.close()
        with open(group_name+"key.txt", "rb") as f:
            data = f.read()
        with open("Groups/"+group_name+".txt", 'r') as f:
            emails = [line.strip() for line in f]
        for i in emails:
            member_select = dropbox.sharing.MemberSelector.email(i)
            access_level = dropbox.sharing.AccessLevel.editor
            add_member = dropbox.sharing.AddMember(member_select, access_level)
            dbx.sharing_add_folder_member(meta_data.shared_folder_id, [add_member])
        print('Folder created for group.')
        dbx.files_upload(enc_data, '/'+group_name+'/' + upload_file)
        dbx.files_upload(encrypted, '/'+group_name+'/' + group_name+"encrypted_key.txt")
        print("File uploaded")
        b = 1
else: print("Sorry, I cannot find that file. Make sure you typed in the path, name, and extension correctly!")

#Downloading file from group specified 
group_name = raw_input("What group do you want to download from? ")
my_email = raw_input("What's your email? ")
if (os.path.isfile("Groups/"+group_name+".txt")):
    b = 0
    with open("Groups/"+group_name+".txt", 'r') as f:
        emails = [line.strip() for line in f]
        for i in emails:
            if my_email == i:
                print("Thanks, you've been authenticated.")
                b = 1
    if b == 1:
        file_name = raw_input("What file would you like to download? ")
        path = "/"+group_name+"/"+file_name
        fd1 = open(group_name+"private_key.pem", "r")
        private_key = fd1.read() 
        fd1.close()
        rsakey = RSA.importKey(private_key)
        rsakey = PKCS1_OAEP.new(rsakey)
        if (os.path.isfile(group_name+"recv_key.txt")):
            f = open(group_name+"recv_key.txt", 'r')
            key = rsakey.decrypt(f.read())
            f.close()
            key = Fernet(key)
            metadata, f = dbx.files_download(path)
            final = open(file_name, 'wb')
            final.write(key.decrypt(f.content))
            final.close()  
            print("File downloaded successfully.")  
        else:
            path = "/"+group_name+"/"+group_name+"encrypted_key.txt"
            metadata, f = dbx.files_download(path)
            new = open(group_name+"recv_key.txt", 'wb')
            new.write(f.content)
            key = rsakey.decrypt(f.content)
            new.close()
            fernet = Fernet(key)
            path = "/"+group_name+"/"+file_name
            metadata, f = dbx.files_download(path)
            final = open(file_name, 'wb')
            final.write(fernet.decrypt(f.content))
            final.close()
            print("File downloaded successfully.")  
    else: 
        print("You aren't a member of that group.")
else:
    print("Sorry, I cannot find that group name, did you type it in correctly?")