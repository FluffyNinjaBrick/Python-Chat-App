from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/chat')
def chat():
    # get the username and chatroom number from the get request generated by the form
    username = request.args.get('username')
    room = request.args.get('room')

    # if they are correct, we enter the chatroom; the parameters can be accessed in the template via {{}}
    if username and room:
        return render_template('chat.html', username=username, room=room)
    # if not, we redirect to home( / )
    else:
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
