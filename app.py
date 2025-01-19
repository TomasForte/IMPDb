from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import json
from helper import apology, login_required
from datetime import date

# Configure application
app = Flask(__name__)
app.run(debug=True)

app.config['TEMPLATES_AUTO_RELOAD'] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
DOMAIN = "http://127.0.0.1:5000"

#this probably should be in the db
status_list=["Watching", "Planning to watch", "Completed", "Dropped"]

#connect  to db
connection = sqlite3.connect("project.db",check_same_thread=False)
cursor = connection.cursor()

@app.route("/")
def index():

    new_releases_shows = cursor.execute("SELECT * FROM shows  WHERE type = 'series' ORDER BY released DESC LIMIT 5").fetchall()
    new_releases_movies = cursor.execute("SELECT * FROM shows WHERE type = 'movie' ORDER BY released DESC LIMIT 5").fetchall()
    trending_movies = cursor.execute("""SELECT shows.id, shows.title, shows.image from shows 
                                    INNER JOIN(SELECT show_id, count(show_id), RANK() OVER  (ORDER BY COUNT(show_id) DESC) ranking FROM users_list WHERE show_id in (
                                    SELECT id from shows WHERE type = "movie") AND edit_date > date('now','-6 month') Group By show_id LIMIT 5) as a
                                    ON shows.id= a.show_id
                                    """).fetchall()
    
    trending_shows = cursor.execute("""SELECT shows.id, shows.title, shows.image from shows 
                                INNER JOIN(SELECT show_id, count(show_id), RANK() OVER  (ORDER BY COUNT(show_id) DESC) ranking FROM users_list WHERE show_id in (
                                SELECT id from shows WHERE type = "series") AND edit_date > date('now','-6 month') Group By show_id LIMIT 5) as a
                                ON shows.id= a.show_id
                                """).fetchall()



    return render_template("/index.html",new_releases_shows = new_releases_shows, 
                        trending_shows=trending_shows,
                        new_releases_movies = new_releases_movies,
                        trending_movies = trending_movies)

@app.route("/show")
def show():
     id = request.args.get("id", None)
     if id is not None:
        show = cursor.execute("""SELECT json_object('title', title,'year',year,'rated',rated,'released',released,'duration',duration
            ,'plot',plot,'language',language,'country',country,'image',image,'type',type,'seasons',Seasons, 'id', id
            ) FROM shows  WHERE id = ?""",(id,)).fetchone()
        if show is not  None:
            show = json.loads(show[0])

            actors =  cursor.execute("""SELECT roles.role, people.name FROM shows 
                                    INNER JOIN roles
                                    ON shows.id = roles.show_id
                                    INNER JOIN people
                                    ON roles.person_id = people.id
                                    Where shows.id = ?""", (id,)).fetchall()

            #get shows stats
            stats={}        
            mean = cursor.execute("SELECT ROUND(AVG(score),2) as mean FROM users_list WHERE show_id = ? AND score IS NOT NULL GROUP BY show_id",(id,)).fetchone()
            ranking = cursor.execute("""SELECT * FROM 
                                        (SELECT show_id, ROUND(AVG(score),2) as mean, RANK() OVER  (ORDER BY AVG(score) DESC) ranking
                                        FROM users_list WHERE score IS NOT NULL GROUP BY show_id) AS a
                                        WHERE show_id = ?""",(id,)).fetchone()
            
            popularity = cursor.execute("""SELECT * FROM 
                                        (SELECT show_id, COUNT(show_id) as members, RANK() OVER  (ORDER BY COUNT(show_id) DESC) ranking
                                        FROM users_list GROUP BY show_id) AS a
                                        WHERE show_id = ?""",(id,)).fetchone()
            
            stats = {"mean": mean[0] if mean is not None else "N/A",
                    "ranking": ranking[2] if mean is not None else "N/A",
                    "popularity":popularity[1] if mean is not None else "N/A"}


            # get user list info on the show
            if "user_id" in session:
                status = cursor.execute("""SELECT status, score FROM users_list WHERE user_id = ? AND show_id = ?""", (session["user_id"], id)).fetchone()
            else:
                status = None

            
            
            return render_template("/show.html", show=show, actors=actors, status=status, status_list=status_list, stats = stats)
        else:
            return apology("ERROR show not found")
     else:
          return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = cursor.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        ).fetchall()

        if len(rows) > 0:
            return apology("username already used", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        cursor.execute("INSERT INTO users (username, password) VALUES(?, ?)",
                   (request.form.get("username"),  generate_password_hash(request.form.get("password"))))

        rows = cursor.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        ).fetchall()

        connection.commit()


        # Remember which user has logged in
        session["user_id"] = rows[0][0]
        session["username"] = rows[0][1]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")
    
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        

        # Query database for username
        rows = cursor.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        ).fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]
        session["username"] = rows[0][1]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
    
@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/addlist", methods=["POST"])
@login_required
def addlist():
    status = request.form.get("status", None)
    score = request.form.get("score")
    show_id = request.form.get("show_id")
    
    # verify the user inputput is correct
    try:
        score = int(score)
    except:
        score = None

    try:
        show_id = int(show_id)
    except:
        show_id = None

    
    if show_id is not None:
        if status in status_list and (score in range(1, 11) or score == None):
            check = cursor.execute("SELECT id FROM shows WHERE id = ?", (show_id,)).fetchone()
            if len(check) != 1:
                return apology("ERROR show not found")
            else:
                #check if not in list add or update if in list
                check1= cursor.execute("SELECT show_id FROM users_list WHERE show_id = ? AND user_id = ?",(show_id,session["user_id"])).fetchone()
                if check1 is None:

                    cursor.execute("INSERT INTO users_list (user_id, show_id, status, score, edit_date) VALUES (?,?,?,?,?)",
                                (session["user_id"],show_id,status,score,date.today()))
                    connection.commit()
                    return redirect(f"show?id={show_id}")
                else:
                    cursor.execute("UPDATE users_list SET status = ?, score = ?, edit_date = ? WHERE show_id = ? AND user_id = ?",
                                   (status, score, date.today(), show_id, session["user_id"]))
                    connection.commit()
                    return redirect(f"show?id={show_id}")
        else:   
            return apology("status not select")
    else:
        return apology("invalid show")
    


@app.route("/topmovies", methods=["GET"])
def topmovies():
    offset = request.args.get("offset", 0)
    try:
        offset = int(offset)
    except:
        offset = 0
    max = cursor.execute("""SELECT count(show_id) FROM (SELECT show_id 
                        FROM users_list WHERE score IS NOT NULL AND show_id in (SELECT id FROM shows WHERE type = 'movie')
                         GROUP BY show_id)""").fetchone()
    listmovies = cursor.execute("""SELECT a.ranking, shows.id,shows.title, shows.image, a.mean FROM shows
                                INNER JOIN (SELECT show_id, ROUND(AVG(score),2) as mean, RANK() OVER  (ORDER BY AVG(score) DESC) ranking
                            FROM users_list WHERE score IS NOT NULL AND show_id in (SELECT id FROM shows WHERE type = 'movie')GROUP BY show_id LIMIT 5 OFFSET ?) as a
                                ON a.show_id = shows.id""", (offset,)).fetchall()


    #offset for the button (next or previous)
    if offset - 5 >= 0 :
        previous = offset - 5
    elif offset > 0:
        previous = 0
    else:
        previous = None

    if offset + 5 >= max[0]:
        next = None
    else:
        next = offset + 5
    
    return render_template("topmovies.html", listmovies=listmovies, offset=offset, next = next, previous=previous)


@app.route("/topshows", methods=["GET"])
def topshows():
    offset = request.args.get("offset", 0)
    try:
        offset = int(offset)
    except:
        offset = 0

    max = cursor.execute("""SELECT count(show_id) FROM (SELECT show_id 
                        FROM users_list WHERE score IS NOT NULL AND show_id in (SELECT id FROM shows WHERE type = 'series')
                         GROUP BY show_id)""").fetchone()
    listmovies = cursor.execute("""SELECT a.ranking, shows.id,shows.title, shows.image, a.mean FROM shows
                                INNER JOIN (SELECT show_id, ROUND(AVG(score),2) as mean, RANK() OVER  (ORDER BY AVG(score) DESC) ranking
                            FROM users_list WHERE score IS NOT NULL AND show_id in (SELECT id FROM shows WHERE type = 'series')GROUP BY show_id LIMIT 5 OFFSET ?) as a
                                ON a.show_id = shows.id""", (offset,)).fetchall()
    
    #offset for the button
    if offset - 5 >= 0 :
        previous = offset - 5
    elif offset > 0:
        previous = 0
    else:
        previous = None

    if offset + 5 >= max[0]:
        next = None
    else:
        next = offset + 5
    
    return render_template("topshows.html", listmovies=listmovies, offset=offset, next = next, previous=previous)


@app.route("/search", methods=["GET"])
def search():

    #check correct input
    title = request.args.get("title", None)
    if title == "":
        title = None
    year = request.args.get("year", None)
    if year == "":
        year = None
    try:
        year = int(year)
    except:
        year = None
    type = request.args.get("type", None)
    if type == "":
        type = None
    if type != "series" and type != "movie":
        type = None
    #for shows the api used to fill the database uses a format like 2000-2004 so I had to get start and end date column 
    # and if the search that is between those column it will display a show
    query = """SELECT id, image, title, 
                    list.score, type,
                    CASE
                        WHEN length(year)=4 THEN
                            CAST(year AS INTEGER)
                        WHEN length(year)=5 THEN
                            CAST(SUBSTR(year, 1, INSTR(year, '–') - 1) AS INTEGER)
                        WHEN length(year)=9 THEN
                            CAST(SUBSTR(year, 1, INSTR(year, '–') - 1) AS INTEGER)
                    END year_started,
                    CASE
                        WHEN length(year)=4 THEN
                            CAST(year AS INTEGER)
                        WHEN length(year)=9 THEN
                            CAST(SUBSTR(year, INSTR(year, '–') + 1) AS INTEGER)
                    END year_finished,
                list.menbers
                FROM shows
                LEFT JOIN (SELECT show_id, ROUND(AVG(score),2) AS score, COUNT(show_id) as menbers FROM users_list GROUP BY show_id) as list
                ON list.show_id = shows.id"""
    values = []
    matches = None
    nfilter = 0
    #check how many filter there are and edit query
    if type == None and year == None and title == None:
        if ("title" in request.args or "year" in request.args or "type" in request.args):
            msg = "please select some filtering option"

            return render_template("search.html", message=msg, matches=matches)
        else:
            return render_template("search.html", matches=matches)
    
    # add filter to the query string
    else:
        query = query + " WHERE "
        if title != None:
            nfilter +=1
            title = '%' + title + '%'
            query = query + "title LIKE ?"
            values.append(title)
        if year != None:
            if nfilter != 0:
                nfilter +=1
                query = query + " AND ((year_started <= ? AND year_finished IS NULL) OR (year_started <= ? AND year_finished >= ?))"
            else:
                nfilter +=1
                query = query + " ((year_started <= ? AND year_finished IS NULL) OR (year_started <= ? AND year_finished >= ?))"
            values.extend([year,year,year])
        if type != None:
            if nfilter != 0:
                nfilter +=1
                query = query + " AND type = ?"
            else:
                nfilter +=1
                query = query + " type = ?"
            values.append(type)
        query = query + " ORDER BY list.menbers DESC"
        matches = cursor.execute(query,values).fetchall()
        if len(matches) == 0:
            msg = "zero matches found"
        else:
            msg = str(len(matches)) + " matches found"


    return render_template("search.html", matches=matches, message=msg)


@app.route("/profile", methods=["GET", "POST"])
def profile():

    id = request.args.get("id", None)
    try:
        id = int(id)
    except:

        id = None
    if id != None:
        username =  cursor.execute("SELECT username FROM users WHERE id = ?",(id,)).fetchone()
        status = cursor.execute("""SELECT status, COUNT(show_id) from users_list 
                    WHERE user_id = ? GROUP BY status""",(id,)).fetchall()
        types = cursor.execute("""SELECT shows.type, COUNT(shows.id) from users_list 
                    INNER JOIN shows ON shows.id = users_list.show_id 
                    WHERE user_id = ?
                    GROUP BY shows.type """,(id,)).fetchall()
        if status!=None and types != None:
            query = """SELECT title, shows.type, score, status FROM users_list 
                            INNER JOIN users
                            ON users.id = users_list.user_id
                            INNER JOIN shows
                            ON shows.id = users_list.show_id
                            WHERE users.id = ?"""
            filter_type = request.form.get("type", None)

            #check which filter are selected
            if filter_type != "" and filter_type is not None:
                
                query = query + " AND shows.type = ?"
            else:
                filter_type = None

            filter_status  = request.form.get("status", None)
            if filter_status != "" and filter_status is not None:
                
                query = query + " AND users_list.status = ?"
            else:
                filter_status = None

            query = query + " ORDER BY title ASC"

            #execute query based in the selected filters
            if filter_type is None and filter_status is None:
                user_list = cursor.execute(query, (session["user_id"],))
            elif filter_type is not None and filter_status is not None:
                user_list = cursor.execute(query, (session["user_id"], filter_type, filter_status))
            elif filter_type is not None:
                user_list = cursor.execute(query, (session["user_id"], filter_type))
            else:
                user_list = cursor.execute(query, (session["user_id"], filter_status))

            
            return render_template("profile.html", status = status, types = types, username=username[0], user_list = user_list)


    return render_template("index.html")




