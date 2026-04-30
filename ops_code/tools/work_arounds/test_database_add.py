#manual add to database for testing
#author- Isaac Reister

import sqlite3
from datetime import datetime

db_path = r"/home/funkb/Documents/GliderPP/databases/PPglider_chain_database.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("""
INSERT INTO PPglider_processing_stages
(glider_type, glider_prefix, glider_number, glider_name, downloaded, date_added, file_downloaded, staged)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", ("seaglider", "ego", "454", "cabot", 1, datetime.now().strftime("%Y%m%d"), r"/home/funkb/Documents/GliderPP/data/cabot_454_test.nc", 0))

conn.commit()
conn.close()
