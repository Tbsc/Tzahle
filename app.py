import os

from flask import Flask, render_template, request, session
import flask
import content
import display.lists
import display.quiz


app = Flask(__name__)
# Secret key used for development, set it if one hasn't been set already
if app.secret_key is None:
    app.secret_key = os.environ.get('SECRET_KEY',
                                    '64b29b9e8f970f9fc7fbc10bc20585841162bd3fe1088b1a47b227e19620471c8b2e1a422bc3d7730864db8c3952b8ae')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dir/')
@app.route('/dir')
@app.route('/dir/<path:tag_path>')
def units_dir(tag_path=''):
    if tag_path == '' and 'q' in request.args:
        tag_path = request.args['q'].replace('-', '/')
    return render_template('lists.html',
                           c=content,
                           d=display.lists,
                           q=tag_path,
                           r='r' in request.args)


@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    """A GET request returns the HTML page of the quiz.
    A POST request has the user's guess inside, or a "give up" message.
    Giving up is defined as sending the following string: giveup
    If the guess inside a request was right, the user's score (inside their session cookies) is incremented,
    and a JSON containing the tag's full name (key: name), path (key: path), relative URL to see the
    tag (key: rel_path), and new score (key: score) is returned for it to be shown to the player. The same JSON is
    returned when giving up, the only difference is that the score counter isn't incremented. If the guess is
    incorrect, the string "incorrect" is returned."""
    if request.method == 'GET':
        tag = display.quiz.random_tag()
        session['tag'] = content.get_folder_path(tag)
        return render_template('quiz.html',
                               c=content,
                               d=display.quiz,
                               tag=tag)
    else:
        tag_path = session.get('tag', default=None)
        if tag_path is None:
            return 'error'
        tag = content.find_unit_tag(tag_path)
        answer_dict = {'name': tag.name, 'path': tag_path, 'rel_path': flask.url_for('units_dir', tag_path=tag_path),
                       'score': score()}

        guess = request.data.decode('utf-8').translate(content.no_punc_trans).strip()

        if guess == 'giveup':
            return answer_dict

        if guess in tag.alt_names:
            answer_dict['score'] += 1
            score(answer_dict['score'])
            return answer_dict
        else:
            return 'incorrect'


def score(new=None):
    if new is None:
        return session.get('score', 0)
    else:
        session['score'] = new


if __name__ == '__main__':
    app.run()
