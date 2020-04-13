# Géocodage de la base DICOTOPO

Ce projet vise à affiner le géocodage de la base DicoTopo:

* https://dicotopo.cths.fr/
* https://github.com/chartes/dico-topo

# Méthodologie

Le géocodage est inspiré du projet de Christian Quest sur le géocodage de la base SIRENE:

* https://github.com/cquest/geocodage-spd

Il utilise pour cela les bases d'adresses BAN et BANO qui seront desservies par le moteur de géocodage [addok](https://github.com/addok/addok)

## Installation de l'environnement virtuel Python

Afin de faire tourner ce programme il est conseillé d'utiliser un environnement virtuel Python basé sur la distribution Anaconda.


```bash
conda create --name dicotopo_geocodage -c conda-forge python=3.7  # addok ne fonctionne pas avec Python 3.8
```

Pour ne pas oublier d'utiliser source *conda-forge* sur la ligne de commande il est conseillé de l'ajouter comme source par défaut

```bash
conda activate dicotopo_geocodage
conda config --env --add channels conda-forge
```

[addok](https://addok.readthedocs.io/en/latest/) est un logiciel Python fournissant des services de géocodage d'adresses.
Il sera utilisé pour géolocaliser les adresses du dictionnaire.
Installation de la librairie addok, une fois l'environnement anaconda activé.

Commencez par les outils de développement:

```
sudo apt install build-essential  # Debian based
sudo yum/dnf groupinstall "Development Tools"  # RedHat based
```

Puis la librairie addok:
```
conda install python-geohash
conda install cython
pip install --no-binary :all: falcon
pip install --no-binary :all: addok
```

## Installation de la base BANO


### Installation d'addok pour le géoréférencement
Nous allons suivre ce tutoriel: https://addok.readthedocs.io/en/latest/tutorial/

Dans l'environnement virtuel activé, installer les plugins addok:

```
pip install addok-fr addok-france addok-csv
```

Créer un fichier de configuration addok.conf

```python
QUERY_PROCESSORS_PYPATHS = [
    "addok.helpers.text.check_query_length",
	"addok_france.extract_address",
	"addok_france.clean_query",
	"addok_france.remove_leading_zeros",
]
SEARCH_RESULT_PROCESSORS_PYPATHS = [
    "addok.helpers.results.match_housenumber",
    "addok_france.make_labels",
    "addok.helpers.results.score_by_importance",
    "addok.helpers.results.score_by_autocomplete_distance",
    "addok.helpers.results.score_by_ngram_distance",
    "addok.helpers.results.score_by_geo_distance",
]
PROCESSORS_PYPATHS = [
    "addok.helpers.text.tokenize",
    "addok.helpers.text.normalize",
    "addok_france.glue_ordinal",
    "addok_france.fold_ordinal",
    "addok_france.flag_housenumber",
    "addok.helpers.text.synonymize",
    "addok_fr.phonemicize",
]
```


### Installation de Redis

Le serveur *addok* s'appuie sur la base de données [redis](https://redis.io) qui elle travaille en RAM.  
Il convient donc de l'installer.  
Pour cet exercice, nous allons compiler et installer la base dans notre dossier utilisateur, ce qui permettra de la gérer sans avoir les droits root.

Toutefois elle est généralement fournie avec votre distribution. Si vous optez pour cette option, référez-vous à la documentation de votre distribution Linux.

Téléchargement:

```
wget http://download.redis.io/releases/redis-5.0.8.tar.gz
tar xzf redis-5.0.8.tar.gz
cd redis-5.0.8
```

Compilation et installation:

```
mkdir -p $HOME/tools/redis
make PREFIX=$HOME/tools/redis
make test
make PREFIX=/home/pegliasco/tools/redis install
```

Copie des fichiers de configuration:

```
cp redis.conf sentinel.conf $HOME/tools/redis/

```

Editez ensuite le fichier de configuration et personnalisez les variables suivantes:

* *dbfilename* : nom du fichier de la base de données
* *dir* : emplacement du fichier de la base de données
* *logfile* : emplacement du fichier de logs


Lancement de Redis:

```
$HOME/tools/redis/bin/redis-server $HOME/tools/redis/redis.conf

```


### Chargement de la base bano
Nous allons maintenant charger la base BANO dans ADDOK/REDIS.  
La base peut être téléchargée depuis le site [bano.openstreetmap.fr](http://bano.openstreetmap.fr)


Téléchargement et décompression:
```
wget http://bano.openstreetmap.fr/data/full.sjson.gz
gunzip full.sjson.gz
```

Chargement de la base dans addok, une fois redis démarré et l'environnement virtuel activé:

```
addok --config /path/to/addok.conf batch /path/to/full.sjson
```

Vous pouvez ensuite tester le bon fonctionnement de la base:

```
addok --config /path/to/addok.conf shell
```

```
Addok 1.0.2
Loaded local config from /home/pegliasco/tools/addok/addok.conf
Loaded plugins:
addok.shell==1.0.2, addok.http.base==1.0.2, addok.batch==1.0.2, addok.pairs==1.0.2, addok.fuzzy==1.0.2, addok.autocomplete==1.0.2, france==1.1.0, fr==1.0.1, csv==1.0.1

Welcome to the Addok shell o/
Type HELP or ? to list commands.
Type QUIT or ctrl-C or ctrl-D to quit.

> l'abbatiale crans
L'Abbatiale 01320 Crans (QXK5 | 0.9094545454545453)
L'Abbatiale 01320 Crans (W6lrMg | 0.9094545454545453)
Route de l'Abbatiale 01320 Crans (yAWV | 0.6365363636363636)
Route de l'Abbatiale 01320 Crans (qxrEm0 | 0.6365363636363636)
20.0 ms — 1 run(s) — 4 results
--------------------------------------------------------------------------------
```

Afin d'interroger le serveur addok via son api nous allons le lancer en mode serveur:

```
addok --config /path/to/addok.conf serve
```


# Execution du géocodage

2 scripts Python ont été développés pour géocoder les fichiers du dicotopo:

	* `geocoding_dicotopo.py` : géocode un fichier XML issu de dicotopo et génère le résultat dans un fichier ayant l'extension `.geocoded.xml` et un second avec l'extension `.errors.csv` pour les éventuelles erreurs rencontrées.
* `geocoding_dicotopo_folder.py` : recherche tous les fichiers `DT*.XML` des sous dossiers `DT*` et génère le géocodage


Dans cette première version les scripts ne sont pas parallélisés et travaille sur un seul serveur addok de géocodage

Ils nécessitent la librairie lxml pour parser les fichiers dicotopo:

```
conda install lxml requests
```

Exemple d'utilisation:

```
 python geocoding_dicotopo.py -h
```																																					 



```
python geocoding_dicotopo.py -f /path/to/dicotopo/xml/file/DT01.xml --addok-api http://localhost:7878
```


```
python geocoding_dicotopo_folder.py --dicotopo-folder=/home/<user>/data/dicotopo/dico-topo/data --addok-api=http://localhost:7878
```



