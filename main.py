import app

if __name__ == "__main__":
    app = app.create_app()
    theresold = 0.5
    app.run(debug=True,threaded=True)