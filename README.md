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
        ssh-keygen -f "/home/mike/.ssh/known_hosts" \
                   -R [127.0.0.1]:3022
        
        # Install the key in the VM:
        ssh-copy-id -o "StrictHostKeyChecking no" \
                    -i ~/.ssh/vm \
                    -p 3022 webslat-user@127.0.0.1

8.  Run these commands on the VM as root. (I can't figure out how to do this from
    a script on the host machine).
    
    This will install the packages needed to build and run `OpenSLAT`:
    
        apt-get update
        apt-get -y install  git \
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
        curl \
            http://www.antlr.org/download/antlr-4.7-complete.jar \
            -o /usr/local/lib/antlr-4.7-complete.jar
        
        ln -s /usr/bin/swig3.0 /usr/bin/swig
        
        pip3 install antlr4-python3-runtime numpy typing
9.  Build the libraries:
    
        echo \
             'if [[ -e SLAT ]]; then
                  cd SLAT/linux
                  git pull
              else
                  git clone \
                  http://github.com/mikelygee/SLAT
                  cd SLAT/linux
              fi;
              make' |
             ssh -i ~/.ssh/vm -p 3022 \
                 webslat-user@127.0.0.1 |
             tail -5

10. Add the search paths to `.bashrc`, if they aren't already there;
    
        echo \
            "if ! grep PYTHONPATH .profile; then
                 echo export LD_LIBRARY_PATH=~/SLAT/linux/lib >> .profile
                 echo export PYTHONPATH=~/SLAT/linux/lib >> .profile
             fi
        " | ssh -i ~/.ssh/vm -p 3022 webslat-user@127.0.0.1 | tail -5

11. Run the unit tests:
    
        echo "cd SLAT/linux/bin
               ./unit_tests
        " | ssh -i ~/.ssh/vm -p 3022 \
                webslat-user@127.0.0.1 2>&1 | tail -5

12. Run the C++ example2 binary:
    
        echo "cd SLAT/parser/example2
                 ../../linux/bin/example2
        " | ssh -i ~/.ssh/vm -p 3022 \
                webslat-user@127.0.0.1 2>&1 | tail -5

13. Run the example2 Python script:
    
        echo "cd SLAT/parser/example2
                 ./example2.py
        " | ssh -i ~/.ssh/vm -p 3022 \
                webslat-user@127.0.0.1 2>&1 | tail -5

14. Run the example2 SLAT script:
    
        echo "cd SLAT/parser/example2
                 ../../linux/scripts/SlatInterpreter.py \
                      example2.slat
        " | ssh -i ~/.ssh/vm -p 3022 \
                webslat-user@127.0.0.1 2>&1 | tail -10

15. Run these commands on the VM as root. (I can't figure out how to do this from
    a script on the host machine).
    
    This will install the packages needed for `WebSLAT`:
    
        apt-get -y install gfortran \
                gsl-bin \
                liblapack-dev \
                libfreetype6-dev \
                python3-tk \
                links2
        pip3 install virtualenv
16. Set up a virtual python environment
    
        echo "virtualenv webslat-env
                 source webslat-env/bin/activate
                 pip3 install numpy \
                     matplotlib \
                     scipy \
                     django \
                     django-jchart \
                     django-autocomplete-light \
                     django-extensions \
                     seaborn \
                     pyquery
                 pip3 install django-registration
                 pip3 install --upgrade django
                 deactivate
        " | ssh -i ~/.ssh/vm -p 3022 \
                webslat-user@127.0.0.1 2>&1 | tail -10

17. Copy the `webslat` files to the VM:
    
        echo "git clone \
                  http://github.com/mikelygee/webslat
        " | ssh -i ~/.ssh/vm -p 3022 \
                webslat-user@127.0.0.1 2>&1 | tail -10

18. Copy the `graphos` templates to the `slat` directory:
    
        echo "cd ~/webslat-env/lib/python3.5/site-packages/graphos/templates
              cp -r graphos/ ~/webslat/webslat/slat/templates
        " | ssh -i ~/.ssh/vm -p 3022 \
                webslat-user@127.0.0.1 2>&1 | tail -10
19. Initialise the databse:
    As `webslat-user` on the VM, run:
    
        source webslat-env/bin/activate
        cd webslat/webslat
        python3 manage.py migrate

20. Run the test scripts:
    As `webslat-user` on the VM, run:
    
        python3 manage.py test

21. Seed the databse:
    As `webslat-user` on the VM, run:
    
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
22. Test the `django` server:
    As `webslat-user` on the VM, run:
    
        python3 manage.py runserver 0:8000
    
    In a separate session, run:
    
        links2 127.0.0.1:8000/slat
    
    to confirm the server is working.
    
    Quit `links2` and kill the server.
23. User `apache2` to serve `webslat`. First, as `root` on the VM, run:
    
        apt-get -y install apache2 \
            libapache2-mod-wsgi-py3
24. Make sure the `apache2` process can read the database file.
    1.  Assign appropriate permissions:
        
            echo "chmod 664 webslat/webslat/db.sqlite3
                  chmod 775 webslat/webslat
                  chmod --recursive 744 webslat/webslat/slat/static
            " | ssh -i ~/.ssh/vm -p 3022 webslat-user@127.0.0.1 2>&1 | tail -10
    
    2.  Assign the files to the `www-data` group. As root on the VM, run:
        
            chown :www-data /home/webslat-user/webslat/webslat/db.sqlite3
            chown :www-data /home/webslat-user/webslat/webslat
            chown --recursive :www-data /home/webslat-user/webslat/webslat/slat/static
25. Edit `webslat/webslat/webslat/settings.py`
    1.  Set:
        
            ALLOWED_HOSTS = ['localhost', '127.0.0.1', '127.0.1.1']
    2.  Set:
        
            STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
26. Create the static files:
    
        echo "source webslat-env/bin/activate
              cd webslat/webslat
             ./manage.py collectstatic
        " | ssh -i ~/.ssh/vm -p 3022 webslat-user@127.0.0.1 2>&1 | tail -10

27. As `root` on the VM, edit `/etc/apache2/sites-available/000-default.conf`, by
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
28. Install `libslat` where `apache2` can find it. As `root`, on the VM, run:
    
        ln -s /home/webslat-user/SLAT/linux/lib/libslat.so /usr/local/lib
        ldconfig
29. Restart the server. As `root`, on the VM, run:
    
        systemctl restart apache2

To update OpenSLAT and WebSLAT without creating a new image:

1.  Update OpenSLAT from git, and build:
    
        echo \
            'cd SLAT/linux
             git pull
             make' |
             ssh -i ~/.ssh/vm -p 3022 \
                 webslat-user@127.0.0.1 |
             tail -5

1.  Update WebSLAT:
    
        echo \
            'cd webslat
             git pull
             ' |
             ssh -i ~/.ssh/vm -p 3022 \
                 webslat-user@127.0.0.1 |
             tail -5

1.  Run migrations:
    
        echo "source webslat-env/bin/activate
              cd webslat/webslat
             yes yes | ./manage.py migrate
        " | ssh -i ~/.ssh/vm -p 3022 webslat-user@127.0.0.1 2>&1 | tail -10

1.  Update the static files:
    
        echo "source webslat-env/bin/activate
              cd webslat/webslat
             yes yes | ./manage.py collectstatic
        " | ssh -i ~/.ssh/vm -p 3022 webslat-user@127.0.0.1 2>&1 | tail -10

1.  Restart the server. As `root`, on the VM, run:
    
        systemctl restart apache2

