activate_this = '/home/iskalnik/projects/slovenia_info/venv/bin/activate.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

from test_app import app as application