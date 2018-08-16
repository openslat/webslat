WebSLAT is a web-based interface to the [OpenSLAT](http://github.com/mikelygee/SLAT) project. The procedure below
will create a VirtualBox image including the OpenSLAT libraries and WebSLAT
served via Apache.

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
    -   host port 3080 to VM port 80    # For server
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
        
            # Add the identity as a default
            ssh-add ~/.ssh/vm
        fi
        
        # If we've used the key with an earlier VM,
        # remove it:
        ssh-keygen -f "$HOME/.ssh/known_hosts" \
                   -R [127.0.0.1]:3022
        
        # Install the key in the VM:
        ssh-copy-id -o "StrictHostKeyChecking no" \
                    -i ~/.ssh/vm \
                    -p 3022 webslat-user@127.0.0.1

8.  Configure `ssh` to use the correct port and user name by default:
    
        if [[ ! -e ~/.ssh/config ]]; then
            touch ~/.ssh/config
        fi
        if [ $(grep -c webslat-vm ~/.ssh/config) == 0 ]; then
            echo "Host webslat-vm
            User     webslat-user
            Port     3022
            Hostname 127.0.0.1" \
                 >> ~/.ssh/config
        fi

9.  Test `ssh`:
    
        whoami

10. Give `webslat-user` `sudo` privileges, without requiring a password. On the
    VM, as `root`, run:
    
        apt-get install sudo
        echo "webslat-user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

11. Test `sudo`:
    
        whoami
        sudo whoami

12. Run these commands:
    
    This will install the packages needed to build and run `OpenSLAT`:
    
        sudo apt-get update
        sudo apt-get -y install  git \
             make \
             pkg-config \
             libgsl-dev \
             python3-dev \
             python3-pip \
             g++ \
             libboost-dev \
             libboost-log-dev \
             libboost-test-dev \
             swig3.0 \
             openjdk-8-jre-headless \
             curl \
             zile
         sudo curl \
             http://www.antlr.org/download/antlr-4.7-complete.jar \
             -o /usr/local/lib/antlr-4.7-complete.jar
        
         sudo ln -s /usr/bin/swig3.0 /usr/bin/swig
        
         sudo pip3 install antlr4-python3-runtime numpy typing

13. Build the libraries:
    
        if [[ -e SLAT ]]; then
            cd SLAT/linux
            git pull
        else
            git clone \
                http://github.com/mikelygee/SLAT
            cd SLAT/linux
        fi;
        make

14. Add the search paths to `.profile`, if they aren't already there;
    
        if ! grep -q PYTHONPATH .profile; then
            echo export LD_LIBRARY_PATH=~/SLAT/linux/lib >> .profile
            echo export PYTHONPATH=~/SLAT/linux/lib >> .profile
        fi

15. Run the unit tests:
    
        source .profile
        cd SLAT/linux/bin
        ./unit_tests

16. Run the C++ example2 binary:
    
        source .profile
        cd SLAT/parser/example2
        ../../linux/bin/example2

17. Run the example2 Python script:
    
        source .profile
        cd SLAT/parser/example2
        ./example2.py

18. Run the example2 SLAT script:
    
        source .profile
        cd SLAT/parser/example2
        ../../linux/scripts/SlatInterpreter.py \
            example2.slat

19. Run these commands:
    
    This will install the packages needed for `WebSLAT`:
    
        sudo apt-get -y install gfortran \
             gsl-bin \
             liblapack-dev \
             libfreetype6-dev \
             python3-tk \
             w3m \
             rabbitmq-server \
             redis-server \
             supervisor
        sudo pip3 install virtualenv

20. Set up a virtual python environment
    
        virtualenv webslat-env
        source webslat-env/bin/activate
        pip3 install numpy \
             matplotlib \
             scipy \
             django \
             django-jchart \
             django-autocomplete-light \
             django-extensions \
             seaborn \
             pyquery \
             xlrd \
             pandas \
             celery \
             django-celery
        pip3 install django-registration
        pip3 install --upgrade django
        deactivate

21. Copy the `webslat` files to the VM:
    
        git clone http://github.com/mikelygee/webslat

22. Create a temporary directory. This is where `WebSLAT` will store temporary
    files, in particular for passing to the `celery` worker when importing
    `ETABS` data.
    
        mkdir webslat/webslat/tmp
        chown :www-data webslat/webslat/tmp
23. Install the config file to allow `supervisord` to start `celery`
    automatically:
    
        echo "[program:webslat-celery]
        command=/home/webslat-user/webslat/start-celery.sh
        user=www-data" > webslat-celery.conf
        sudo mv webslat-celery.conf /etc/supervisor/conf.d

24. Initialise the databse:
    As `webslat-user` on the VM, run:
    
        source .profile
        source webslat-env/bin/activate
        cd webslat/webslat
        python3 manage.py migrate

25. Run the test scripts:
    
        source .profile
        source webslat-env/bin/activate
        cd webslat/webslat
        ./runtests.sh 2>&1

26. Seed the databse:
    
        source .profile
        source webslat-env/bin/activate
        cd webslat/webslat
        python3 manage.py runscript seed_system

This will populate the database with several users and projects:

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-left">User ID</th>
<th scope="col" class="org-left">Password</th>
<th scope="col" class="org-left">Admin?</th>
<th scope="col" class="org-left">Projects</th>
</tr>
</thead>

<tbody>
<tr>
<td class="org-left">slat-admin</td>
<td class="org-left">swordfish</td>
<td class="org-left">X</td>
<td class="org-left">&#xa0;</td>
</tr>
</tbody>

<tbody>
<tr>
<td class="org-left">samspade</td>
<td class="org-left">maltesefalcon</td>
<td class="org-left">&#xa0;</td>
<td class="org-left">Sam Spade's Demo Project</td>
</tr>


<tr>
<td class="org-left">&#xa0;</td>
<td class="org-left">&#xa0;</td>
<td class="org-left">&#xa0;</td>
<td class="org-left">Sam Spade's Other Demo Project</td>
</tr>
</tbody>

<tbody>
<tr>
<td class="org-left">miles</td>
<td class="org-left">samspartner</td>
<td class="org-left">&#xa0;</td>
<td class="org-left">&#xa0;</td>
</tr>
</tbody>

<tbody>
<tr>
<td class="org-left">marlowe</td>
<td class="org-left">thebigsleep</td>
<td class="org-left">&#xa0;</td>
<td class="org-left">Phil Marlowe's First Project</td>
</tr>


<tr>
<td class="org-left">&#xa0;</td>
<td class="org-left">&#xa0;</td>
<td class="org-left">&#xa0;</td>
<td class="org-left">Phil Marlowe's Second Project</td>
</tr>
</tbody>

<tbody>
<tr>
<td class="org-left">holmes</td>
<td class="org-left">elementary</td>
<td class="org-left">&#xa0;</td>
<td class="org-left">Sherlock's Project</td>
</tr>
</tbody>
</table>

1.  Test the `django` server:
    As `webslat-user` on the VM, run:
    
        # Can't run this from this file, because =runserver= won't return.
        source webslat-env/bin/activate
        cd webslat/webslat
        python3 manage.py runserver 0:8000
    
    In a separate session, run:
    
        w3m http://127.0.0.1:8000
    
    to confirm the server is working.
    
    Quit `w3m` and kill the server.
2.  User `apache2` to serve `webslat`. First, run:
    
        sudo apt-get -y install apache2 \
             libapache2-mod-wsgi-py3

3.  Make sure the `apache2` process can read the database file.
    1.  Assign appropriate permissions:
        
            chmod 664 webslat/webslat/db.sqlite3
            chmod 775 webslat/webslat
            chmod --recursive 744 webslat/webslat/slat/static
    
    2.  Assign the files to the `www-data` group. Run:
        
            sudo chown :www-data /home/webslat-user/webslat/webslat/db.sqlite3
            sudo chown :www-data /home/webslat-user/webslat/webslat
            sudo chown --recursive :www-data /home/webslat-user/webslat/webslat/slat/static

4.  Edit `webslat/webslat/webslat/settings.py`
    1.  Set `ALLOWED_HOSTS`:
        
            sed -ie "s/ALLOWED_HOSTS.*$/ALLOWED_HOSTS=['localhost', '127.0.0.1', '127.0.1.1']/" \
                webslat/webslat/webslat/settings.py
    
    2.  Set `STATIC_ROOT`:
        
            sed -ie "s/STATIC_ROOT.*/STATIC_ROOT = os.path.join(BASE_DIR, 'static\/')/" \
                webslat/webslat/webslat/settings.py

5.  Create the static files:
    
        source .profile
        source webslat-env/bin/activate
        cd webslat/webslat
        ./manage.py collectstatic

6.  As `root` on the VM, edit `/etc/apache2/sites-available/000-default.conf`, by
    adding, inside the `<VirtualHost...>` tag:
    
        if [ $(grep webslat-user -c /etc/apache2/sites-available/000-default.conf) == 0 ]
        then 
            sudo sed -ie 's|</VirtualHost>|\
                Alias /static /home/webslat-user/webslat/webslat/static \
                  <Directory /home/webslat-user/webslat/webslat/static>\
                    Require all granted\
                </Directory>\
        \
                <Directory /home/webslat-user/webslat/webslat/webslat>\
                  <Files wsgi.py>\
                      Require all granted\
                  </Files>\
                </Directory>\
        \
                WSGIDaemonProcess webslat python-home=/home/webslat-user/webslat-env python-path=/home/webslat-user/webslat/webslat:/home/webslat-user/SLAT/linux/lib\
                WSGIProcessGroup webslat\
                WSGIScriptAlias / /home/webslat-user/webslat/webslat/webslat/wsgi.py\
        </VirtualHost>|' /etc/apache2/sites-available/000-default.conf
        fi
    
    Test the configuration:
    
        sudo apache2ctl configtest 2>&1

7.  Install `libslat` where `apache2` can find it. Run:
    
        sudo ln -s /home/webslat-user/SLAT/linux/lib/libslat.so /usr/local/lib
        sudo ldconfig

8.  Restart the server:
    
        sudo systemctl restart apache2

9.  Connect from the browser:
    
        firefox http://localhost:3080

To update OpenSLAT and WebSLAT without creating a new image:

1.  Update OpenSLAT from git, and build:
    
        cd SLAT/linux
        git pull
        make

2.  Update WebSLAT:
    
        cd webslat
        git pull

3.  Run migrations:
    
        source .profile
        source webslat-env/bin/activate
        cd webslat/webslat
        yes yes | ./manage.py migrate

4.  Update the static files:
    
        source .profile
        source webslat-env/bin/activate
        cd webslat/webslat
        yes yes | ./manage.py collectstatic

5.  Restart the server:
    
        sudo systemctl restart apache2

