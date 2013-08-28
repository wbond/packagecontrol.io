# Package Control Website

The Package Control website serves as both the main aggregator of package
information for Package Control and as a web interface for users to discover
packages.

## Overview

The Package Control website runs on an architecture of:

 - Python 3.3
 - PostgreSQL 9.2
 - nginx
 - redis (production only)

The website uses the following server-side libraries:

 - bottle
 - psycopg2
 - pybars
 - coffeescript
 - SCSS

The client-side libraries are:

 - backbone.js
 - Handlebars
 - D3

The various libraries are woven together to create a site with the following
properties:

 - Shared HTML templating on the server and client with pybars and Handlebars
 - Initial page loads deliver fully-rendered HTML. Subsequent requests (for
   all supported browsers but IE 9) use HTML 5 pushState and pull in JSON that
   is rendered with Handlebars.
 - URLs without an extension return fully rendered HTML page. URLs ending in
   .json return raw JSON data. URLs ending in .html return an HTML partial that
   excludes the header and footer.
 - When HTML 5 pushState is used, the header and footer do not need to be
   re-rendered. This allows for nice CSS transitions between pages. This also
   requires a progress bar to communicate the AJAX request state.
 - No raster graphics are used - icons are from Font Awesome, logos are SVG and
   the install graphics use SVG through D3. This means the site is
   retina-friendly.

Supported browsers:

 - Firefox, Chrome, Safari, Opera, IE 9+

IE 8 and older are not supported because they do not support SVG, which is used
for all of the graphics and charting on the site.

## Further Reading

 - [Development environment setup](development.md)
 - [Production environment setup](production.md)
 - [App layout](app/readme.md)
 - [Tasks](tasks.md)
 - [Cron](crontab)
 - [License](license.md)
