from app import app
from server import RiotApiHandler

@app.route('/')
@app.route('/index')
def index():
    rah = RiotApiHandler()
    rah.get_ranked_players()
    return "Hello, World!"
