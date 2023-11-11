# Linux System Setup

## Install

Nodejs is used for compiling handlebars and coffeescript files.

```bash
sudo apt install nodejs
```

Make sure we have Python 3 and tools to create a virtual environment for it.

```bash
sudo apt install python3 python3-venv python3-pip
```

Install PostgreSQL for the database.

```bash
sudo apt install postgresql
```

Install Redis for caching

```bash
sudo apt install redis
```

Install Nginx for the web server

```bash
sudo apt nginx-full nginx-extras
```

Install git for downloading `package_control_channel` for crawler

```bash
sudo apt git
```

For development

```bash
sudo apt install libxml2-dev libxslt-dev
```

## Setup

Register postgresql binary path by adding the following line to ~/.profile

```bash
if [ -d "/usr/postgresql/13/bin" ] ; then
  PATH="/usr/postgresql/13/bin:$PATH"
fi
```

Create the `package_control` database and set up all of the tables.

```bash
createdb -U postgres -E 'UTF-8' package_control
psql -U postgres -d package_control -f sql/up.sql
```

Set up the virtual environment and install the packages.

```bash
python -m venv venv
pip install -r setup/requirements.txt
pip install -r setup/dev-requirements.txt
```

```bash
git clone --depth 1 https://github.com/wbond/package_control_channel channel
```
