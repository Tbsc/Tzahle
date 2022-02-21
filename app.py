from flask import Flask, render_template, request
import content


app = Flask(__name__)


@app.route('/')
def main():
    return render_template('index.html',
                           c=content,
                           q=request.args.get('q', default=''),
                           r='r' in request.args)
