from imdb import Cinemagoer
ia = Cinemagoer()

print(ia.get_movie_infoset())

movie = ia.get_movie('2911666')
airdate=movie["airing"]
print(airdate)
print(movie)
print(movie.infoset2keys)