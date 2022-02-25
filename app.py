import os

from flask import Flask, render_template, request, session
import flask
import content
import display.lists
import display.quiz


app = Flask(__name__)
app.secret_key = b'aTemporRsaySecretKeyBEcauseIcan"tMkaesomethginbNOw'


@app.route('/')
def main():
    return render_template('lists.html',
                           c=content,
                           d=display.lists,
                           q=request.args.get('q', default=''),
                           r='r' in request.args)


@app.route('/dir')
@app.route('/dir/<path:tag_path>')
def alt_main(tag_path=''):
    return render_template('lists.html',
                           c=content,
                           d=display.lists,
                           q=tag_path.replace('/', '-'),
                           r='r' in request.args)


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'GET':
        tag = display.quiz.random_tag()
        session['tag'] = content.get_folder_path(tag)
        return render_template('quiz.html',
                               c=content,
                               d=display.quiz,
                               tag=tag)
    else:
        tag = session.get('tag', default=None)
        if tag is None:
            return 'incorrect'
        tag = content.find_unit_tag(tag)
        guess = request.data.decode('utf-8').translate(content.no_punc_trans)
        if guess in tag.alt_names:
            score = session.get('score', 0)
            session['score'] = score + 1
            return tag.name
        else:
            return 'incorrect'


@app.route('/favicon.ico')
def favicon():
    return flask.send_from_directory(os.path.join(app.root_path, 'static/units/sections'), 'operations.png')


if __name__ == '__main__':
    app.run()
