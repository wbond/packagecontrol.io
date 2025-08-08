# Tasks

The Package Control website has a minimal python-based script runner that
may be invoked by calling:

```
python task.py [task_name]
```

The `[task_name]` if the filename of one of the files in
[app/tasks/](app/tasks/), without the `.py` extension. The following is the
current list of valid tasks:

 - `cleanup_renames` - updates various tables to move stats from an old name
   to a new one.

 - `compute_package_hashes` - compute the SHA-256 hash for the various packages
   that are made available for download via non-secure HTTP

 - `crawl` - uses the Package Control channel info from `config/crawler.yml` to
   crawl GitHub, BitBucket and other repositories for package data. Looks for
   packages that have not been seen in the past hour. Only crawls 200 sources
   per run.

- `deploy` - uses SSH to deploy the latest copy of code on GitHub to the server

 - `gather_system_stats` - pulls in updated info about the number of users,
   packages, labels and installs, bytes served, etc for the previous day.

 - `generate_channel_json` - builds the `channel.json` file that contains the
   `2.0` schema version channel info used by Package Control 2.x.

 - `generate_channel_v3_json` - builds the `channel_v3.json` file that contains
   the `3.0.0` schema version channel info used by Package Control 3.x.

 - `generate_channel_v4_json` - builds the `channel_v4.json` file that contains
   the `4.0.0` schema version channel info used by Package Control 4.x.

 - `generate_legacy_channel_json` - build the `repositories.json` file that
   contains the `1.2` schema version channel info used by Package Control 1.x.

 - `generate_signature` - generate an ECDSA signature of the
   `Package Control.sublime-package` file. It is written using ASCII armor of
   `BEGIN PACKAGE CONTROL SIGNATURE`.

 - `mark_removed` - looks for packages that haven't been seen in a long time
   and marks them as removed, so they don't should in search results

 - `parse_log_files` - reads through the nginx log files for the previous day
   to extract statistics about the number of requests and bytes served.

 - `rebuild_stats` - completely reparses the (giant) `usage` table and
   recreated all install statistics about packages. In production, the `usage`
   table has 40M entries (as of August 2013), so this can take quite a while.
   This is not normally used unless an error is detected in calulcating stats.

 - `refresh_package_stats` - recaclulates the installs and trending ranks for
   the packages.

 - `update_package_control_lib` - grabs the latest copy of the
   `package_control` lib from Package Control
