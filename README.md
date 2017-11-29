# Planner-migrator
Python+flask webapp for migrating Microsoft Planner project from one tenant to another  

## Preparation

Before you can use the planner, you need to grant permissions for the app at https://apps.dev.microsoft.com/
You need to add the app for both the old and new user accounts, and admin permission are required.

### Exporter

* Add an app, for example, Planner exporter
* Generate a new password, and add the Application Id and password to config.json "source" section. See "config.json.example" for more info.
* Grant required permissions (see source code)
* Add a "web" platform, and add redirect url to "http://localhost:5000/login/authorized"

### Importer app

* Add an app, for example, Planner importer
* Generate a new password, and add the Application Id and password to config.json "destination" section. See "config.json.example" for more info.
* Grant required permissions (see source code)
* Add a "web" platform, and add redirect url to "http://localhost:5000/login/migrate"

## Usage
```
export FLASK_APP=planner_migrate.py && flask run
```

Navigate to http://localhost:5000/

