import app

if __name__ == "__main__":
    app = app.create_app()
    app.run(debug=True,threaded=True)