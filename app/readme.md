# App Layout

The Package Control website app is structured as:

 - `app/`
   - `controllers/` - one file per route, all controllers need to be included in `__init__.py`
   - `css/` - uses python Gears package to process SCSS and combine them, all files need to be added to `app.scss`
   - `html/` - raw HTML content "partials" that don't present dynamic content
   - `js/` - uses python Gears package to process Coffeescript and combine them, all files need to be added to `app.coffee`
     - `views/` - Backbone.js views to correspond to each controller
     - `router.coffee` - each route must be wired up here to load the appropriate view
   - `lib/` - various custom python code, including Package Control subset
   - `models/` - all database interaction happens through these python files
   - `tasks/` - scripts to be invoked via the command line, normally via cron
   - `templates/` - Handlebars/pybars templates that are used for both client and server-side templating
 - `config/` - yaml files for configuration of various components
 - `public/` - document root for web server, houses JS, CSS, robots.txt, etc
