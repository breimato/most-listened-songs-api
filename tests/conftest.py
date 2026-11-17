import os

# Force an isolated configuration before the application (and its settings)
# are imported by the test modules.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DB_HOST"] = ""
os.environ["LASTFM_API_KEY"] = ""
os.environ["LASTFM_USERNAME"] = ""
