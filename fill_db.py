import requests
import sqlite3
import datetime

with open("key.txt","r") as f:
    key = f.read()

#connect to db
connection = sqlite3.connect("project.db")
cursor = connection.cursor()

#get api result
url = f'http://www.omdbapi.com/?apikey={key}'

for i in range (12037194, 12037394+1):
    id = "tt"+str(i)
    #check if is in db
    param = {"i": id}
    response = requests.get(url, params=param)
    print(response.url)
    response = response.json()
    if "Title" in response:
        in_database = cursor.execute("SELECT id FROM shows WHERE title = ?", (response["Title"],)).fetchone()
        print("OK")
        print(in_database)
        if in_database is None:


            for key, val in response.items():
                if val == "N/A":
                    response[key] = None

            if "totalSeasons" not in response:
                response["totalSeasons"] = None

            if response["Released"] is not None:
                response["Released"] = datetime.datetime.strptime(response["Released"], '%d %b %Y').strftime('%Y/%m/%d')





            cursor.execute("""INSERT INTO shows 
                    (title, year, rated, released, duration, plot, language, country, image, type, Seasons) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", 
                    (response["Title"],response["Year"],response["Rated"],response["Released"],response["Runtime"],response["Plot"],response["Language"],response["Country"],response["Poster"],response["Type"],response["totalSeasons"]))
            
            if response["Director"] is not None:
                for director in response["Director"].split(", "):
                    print(director)
                    check = cursor.execute("select id from people WHERE name = ?", (director,)).fetchone()
                    print(check)
                    if check is None:
                        print("please!!!!")
                        cursor.execute("INSERT INTO people (name) VALUES(?)",(director,))

                    cursor.execute("""INSERT INTO roles (show_id, person_id,role) VALUES(
                        (SELECT id from shows where title = ?),
                        (select id from people WHERE name = ?),?)""",(response["Title"],director,"director"))
                
            if response["Writer"] is not None:
                for writer in response["Writer"].split(", "):
                    check = cursor.execute("select id from people WHERE name = ?", (writer,)).fetchone()
                    if check is None:
                        cursor.execute("INSERT INTO people (name) VALUES(?)",(writer,))

                    cursor.execute("""INSERT INTO roles (show_id, person_id, role) VALUES(
                        (SELECT id from shows where title = ?),
                        (select id from people WHERE name = ?),?)""",(response["Title"],writer,"writer"))
            if response["Actors"] is not None:
                for actor in response["Actors"].split(", "):
                    check = cursor.execute("select id from people WHERE name = ?", (actor,)).fetchone()
                    if check is None:
                        cursor.execute("INSERT INTO people (name) VALUES(?)",(actor,))

                    cursor.execute("""INSERT INTO roles (show_id, person_id, role) VALUES(
                        (SELECT id from shows where title = ?),
                        (select id from people WHERE name = ?),?)""",(response["Title"],actor, "actor"))
                

            print("inserted")
            print(response["Title"])
        else:
            print("already in db")



    connection.commit()


