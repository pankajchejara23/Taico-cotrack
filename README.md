# CoTrack
CoTrack is a Multimodal Learning Analytics tool which offers an easy-to-use interface for multimodal data collection from collaborative learning activities.


# Installation
The following steps offer guidelines on setting up & running SEEDS app on a local machine.

### Clone the CoTrack repository

```
git https://github.com/pankajchejara23/Taico-cotrack.git
```


### Install required packages

```
cd Seeds_bootstrap
pip install -r ./requirement.txt
```

### Initialise database

```
python manage.py makemigrations
python manage.py migrate --run-syncdb
```

### Create a superuser account
The following command creates an admin user account.

```
python manage.py createsuperuser
```

### Run the server
Everything is set now to run the server.

```
python manage.py runserver
```