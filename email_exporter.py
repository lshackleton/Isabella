from google.appengine.ext import db
from google.appengine.tools import bulkloader

"""
Author: Bill Ferrell
Instructions:

Copy this file to the directory below (outside) miracleone (the app engine / git hub directory.)
-- For Bill this means copy this file (email_exporter.py) to the Desktop as the project directory is on the Desktop.

Then open the command line and run the following command:

appcfg.py download_data --config_file=email_exporter.py --filename=email_data_archive.csv --kind=Email miraclewine --auth_domain=[INSERT DOMAIN]

Note you will be asked for a valid username and password.

The output Bill received:

Application: [App Name]; version: 8.
Downloading data records.
[INFO    ] Logging to bulkloader-log-20091222.095917
[INFO    ] Throttling transfers:
[INFO    ] Bandwidth: 250000 bytes/second
[INFO    ] HTTP connections: 8/second
[INFO    ] Entities inserted/fetched/modified: 20/second
[INFO    ] Opening database: bulkloader-progress-20091222.095917.sql3
[INFO    ] Opening database: bulkloader-results-20091222.095917.sql3
[INFO    ] Connecting to miraclewine.appspot.com/remote_api
.[INFO    ] Email: No descending index on __key__, performing serial download
..............
[INFO    ] Have 147 entities, 0 previously transferred
[INFO    ] 147 entities (34570 bytes) transferred in 7.5 seconds
dhcp-172-19-78-177:~/Desktop wferrell$


"""

class Email(db.Model):
  """This is the AppEngine data model for the Email Data."""
  email = db.EmailProperty()
  name = db.StringProperty()
  verified = db.BooleanProperty()
  timestamp = db.DateTimeProperty(auto_now_add=True)


class EmailExporter(bulkloader.Exporter):
    def __init__(self):
        bulkloader.Exporter.__init__(self, 'Email',
                                     [('email', str, None),
                                      ('name', str, None),
                                      ('verified', str, None),
                                      ('timestamp', str, None)
                                     ])

exporters = [EmailExporter]
