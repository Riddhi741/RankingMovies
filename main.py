from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

Bootstrap5(app)

MOVIE_DB_api_key = os.getenv("API_KEY")
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_IMG_URL = "https://image.tmdb.org/t/p/w1280/"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"

# CREATE DB
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE TABLE
class Movies(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

# new_movie = Movies(
#     title="The Mummy",
#     year=1999,
#     description="At an archaeological dig in the ancient city of Hamunaptra, an American serving in the French Foreign Legion accidentally awakens a mummy who begins to wreak havoc as he searches for the reincarnation of his long-lost love.",
#     rating=7.1,
#     ranking=10,
#     review="Brendan Fraser was cute.",
#     img_url="https://a.ltrbxd.com/resized/sm/upload/5i/du/2g/s8/6CweTLmngcPrsEH4G6RKvdwmQdC-0-2000-0-3000-crop.jpg?v=397ac4a555"
# )
# second_movie = Movies(
#     title="Pirates of the Caribbean: Dead Man's Chest",
#     year=2006,
#     description="Captain Jack Sparrow races to recover the heart of Davy Jones to avoid enslaving his soul to Jones’ service, as other friends and foes seek the heart for their own agenda as well.",
#     rating=7.3,
#     ranking=9,
#     review="Absolute childhood favourite",
#     img_url="By http://www.impawards.com/2006/pirates_of_the_caribbean_dead_mans_chest_ver2_xlg.html, Fair use, https://en.wikipedia.org/w/index.php?curid=24062458"
# )
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.add(second_movie)
#     db.session.commit()

class RateMovieForm(FlaskForm):
    rating = FloatField('Your Rating Out of 10', validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    update_done = SubmitField("Done")

class FindMovies(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

@app.route("/")
def home():
    result = db.session.execute(db.select(Movies).order_by(Movies.rating))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) -i
    db.session.commit()

    #print(all_movies)
    return render_template("index.html", movies=all_movies)

# @app.route("/add", methods=["GET", "POST"])
# def add_movies():
#     form = FindMovies()
#     if form.validate_on_submit():
#         print("Submitted")
#     return render_template("add.html", form=form)

@app.route("/edit", methods=["GET", "POST"])
def edit_reviews():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movies, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie)

@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movies, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add", methods=["GET", "POST"])
def add_movies():
    form = FindMovies()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={
            "api_key": MOVIE_DB_api_key,
            "query": movie_title
        })
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)

@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_api_key, "language": "en-US"})
        data = response.json()
        #poster_path = data.get("poster_path")
        new_movie = Movies(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"https://image.tmdb.org/t/p/original/{data['poster_path']}",
            description=data["overview"],
            rating = 0.0,
            ranking=0,
            review="No review yet."
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit_reviews", id=new_movie.id))






if __name__ == '__main__':
    app.run(debug=True)
