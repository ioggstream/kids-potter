# A cli game with rest api

This simple `spell` game aims at teaching kids a bit of python and APIs.

The players engage a spell fight with some of the spells from the Potter's world,
like `expelliarmus` and `avada kedavra`.

# Playing

Run the server with

```
pip install tox
tox -e server
```

Each player should run the client and connect to the server:

```
tox -e client
```
