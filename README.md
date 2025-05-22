# pygame-pictionary

Implémentation d'un jeu de type "Pictionary" en réseau.

Le jeu est constitué d'un serveur qui gère les connexions des joueurs et les parties en cours. Il se lance ainsi :

```
$ cd server
$ python server.py
```

La configuration du serveur est dans le fichier `config.ini`.

Le client est constitué d'une interface graphique lancée ainsi :

```
$ cd client
$ python run_pict.py
```

La configuration du client est dans le fichier `config.ini`.
