from flask import Flask, render_template, request
import content
import display.lists
import display.quiz


app = Flask(__name__)


@app.route('/')
def main():
    return render_template('lists.html',
                           c=content,
                           d=display.lists,
                           q=request.args.get('q', default=''),
                           r='r' in request.args)
