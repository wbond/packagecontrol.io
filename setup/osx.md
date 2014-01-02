# OS X System Setup

These instructions assume you have homebrew installed on your machine and that
you have the XCode command line tools installed.

Nodejs is used for compiling handlebars and coffeescript files.

```
brew install nodejs
```

Make sure we have Python 3 and tools to create a virtual environment for it.

```
brew install python3
easy_install-3.3 pip
pip-3.3 install virtualenv
```

Install PostgreSQL for the database.

```
brew install postgresql
ln -sfv /usr/local/opt/postgresql/*.plist ~/Library/LaunchAgents
launchctl load ~/Library/LaunchAgents/homebrew.mxcl.postgresql.plist
createuser -s postgres
```

Create the `package_control` database and set up all of the tables.

```
createdb -U postgres -E 'UTF-8' package_control
psql -U postgres -d package_control -f sql/up.sql
```

Set up the virtual environment and install the packages.

```
virtualenv-3.3 venv
```
