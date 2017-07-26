1.  Run `virtualbox`.
2.  Click `New`, then `Expert Mode` (if not already active).
3.  Fill out the form:
    
    -   **Name:** WebSLAT
    -   **Type:** Linux
    -   **Version:** Debian (64-bit)
    -   **Memory Size:** 1024 MB
    -   'Create a virtual hard disk now'
    
    Then click `Create`
4.  Specify:
    
    -   **File Location:** `/home/mag109/VirtualBox VMs/WebSLAT/WebSLAT.vdi`
    -   **File size:** `8.00 GB`
    -   **Hard disk file type:** `VDI (VirtualBox Disk Image)`
    -   **Storage on physical hard disk:** `Dynamically allocated`
    
    Then click `Create`
5.  Enable port forwarding:
    -   host port 3022 to VM port 22    # For ssh
    -   host port 3080 to VM port 8000  # For server
6.  Power on the VM. Boot from `~/Downloads/debian-9.0.0-amd64-netinst.iso`. Run
    the graphical installer.
    
    -   **hostname:** WebSLAT
    -   **domain:** webslat.org
    -   **root password:** webslat-admin
    -   **user name & password:** webslat-user
    
    Install standard system utilities and SSH server, but no desktop environment.
7.  Set up a key for ssh logins:
    
        # Create an ssh key, without a password, for 
        # communicating with the VM:
        if [[ ! -e ~/.ssh/vm ]]; then
            ssh-keygen -f ~/.ssh/vm -N ''
        fi
        
        # If we've used the key with an earlier VM,
        # remove it:
        ssh-keygen -f "/home/mag109/.ssh/known_hosts" \
        	   -R [127.0.0.1]:3022
        
        # Install the key in the VM:
        ssh-copy-id -o "StrictHostKeyChecking no" \
        	    -i ~/.ssh/vm \
        	    -p 3022 webslat-user@127.0.0.1

1.  Run the C++ example2 binary:
    
        echo "cd SLAT/parser/example2
        	 ../../linux/bin/example2
        " | ssh -i ~/.ssh/vm -p 3022 \
        	webslat-user@127.0.0.1 2>&1 | tail -5
2.  Run the example2 Python script:
    
        echo "cd SLAT/parser/example2
        	 ./example2.py
        " | ssh -i ~/.ssh/vm -p 3022 \
        	webslat-user@127.0.0.1 2>&1 | tail -5

1.  Run the example2 SLAT script:
    
        echo "cd SLAT/parser/example2
        	 ../../linux/scripts/SlatInterpreter.py \
        	      example2.slat
        " | ssh -i ~/.ssh/vm -p 3022 \
        	webslat-user@127.0.0.1 2>&1 | tail -10

2.  Run these commands on the VM as root. (I can't figure out how to do this from
    a script on the host machine).
    
    This will install the packages needed for `WebSLAT`:
    
        apt-get -y install gfortran \
        	gsl-bin \
        	liblapack-dev \
        	libfreetype6-dev \
        	python3-tk \
        	links2
        pip3 install virtualenv
3.  Set up a virtual python environment
    
        echo "virtualenv webslat-env
        	 source webslat-env/bin/activate
        	 pip3 install numpy \
        	     matplotlib \
        	     scipy \
        	     django \
        	     django-graphos
        	 deactivate
        " | ssh -i ~/.ssh/vm -p 3022 \
        	webslat-user@127.0.0.1 2>&1 | tail -10

4.  Copy the `webslat` files to the VM, since they aren't yet on `github`:
    
        #scp -i ~/.ssh/vm -P 3022 -r \
        #    -q /home/mag109/webslat webslat-user@127.0.0.1: 
    
        echo "git clone \
        	  http://github.com/mikelygee/webslat
        " | ssh -i ~/.ssh/vm -p 3022 \
        	webslat-user@127.0.0.1 2>&1 | tail -10
5.  Test the `django` server:
    As `webslat-user` on the VM, run:
    
        source webslat-env/bin/activate
        cd webslat/webslat
        python3 manage.py migrate
        python3 manage.py runserver 0:8000
    
    In a separate session, run:
    
        links2 127.0.0.1:8000/slat
    
    to confirm the server is working.
    
    Quit `links2` and kill the server.
6.  User `apache2` to serve `webslat`. First, as `root` on the VM, run:
    
        apt-get -y install apache2 \
            libapache2-mod-wsgi-py3
7.  Make sure the `apache2` process can read the database file.
    1.  Assign appropriate permissions:
        
            echo "chmod 664 webslat/webslat/db.sqlite3
                  chmod 775 webslat/webslat
            " | ssh -i ~/.ssh/vm -p 3022 webslat-user@127.0.0.1 2>&1 | tail -10
    
    2.  Assign the files to the `www-data` group. As root on the VM, run:
        
            chown :www-data /home/webslat-user/webslat/webslat/db.sqlite3
            chown :www-data /home/webslat-user/webslat/webslat
8.  Edit `webslat/webslat/webslat/settings.py`
    1.  Set:
        
            ALLOWED_HOSTS = ['localhost', '127.0.0.1', '127.0.1.1']
    2.  Set:
        
            STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
9.  Create the static files:
    
        echo "source webslat-env/bin/activate
              cd webslat/webslat
             ./manage.py collectstatic
        " | ssh -i ~/.ssh/vm -p 3022 webslat-user@127.0.0.1 2>&1 | tail -10
10. As `root` on the VM, edit `/etc/apache2/sites-available/000-default.conf`, by
    adding, inside the `<VirtualHost...>` tag:
    
          Alias /static /home/webslat-user/webslat/webslat/static
          <Directory /home/webslat-user/webslat/webslat/static>
            Require all granted
          </Directory>
        
          <Directory /home/webslat-user/webslat/webslat/webslat>
            <Files wsgi.py>
        	Require all granted
            </Files>
        </Directory>
        
        WSGIDaemonProcess webslat python-home=/home/webslat-user/webslat-env python-path=/home/webslat-user/webslat/webslat:/home/webslat-user/SLAT/linux/lib
        WSGIProcessGroup webslat
        WSGIScriptAlias / /home/webslat-user/webslat/webslat/webslat/wsgi.py
    
    As `root`, run:
    
        apache2ctl configtest
    
    to check the configuration file.
11. Install `libslat` where `apache2` can find it. As `root`, on the VM, run:
    
        ln -s /home/webslat-user/SLAT/linux/lib/libslat.so /usr/local/lib
        ldconfig
12. Restart the server. As `root`, on the VM, run:
    
        systemctl restart apache2

