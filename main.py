import app

if __name__ == "__main__":
    app = app.create_app()
    app.config["threshold"]=0.2
    app.run(debug=True,threaded=True)