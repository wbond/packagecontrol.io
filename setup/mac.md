# Mac System Setup

These instructions assume you have homebrew installed on your machine and that
you have the XCode command line tools installed.

Nodejs is used for compiling handlebars and coffeescript files.

```bash
brew install nodejs
```

Make sure we have Python 3 and tools to create a virtual environment for it.

```bash
brew install pyenv
pyenv install 3.6.8
```

Install PostgreSQL for the database.

```bash
brew install postgresql
```

Install Redis for caching

```bash
brew install redis
```

Install Nginx for the web server

```bash
brew tap denji/nginx;
brew install nginx-full --with-lua-module --with-set-misc-module --with-http2 --with-sub
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
