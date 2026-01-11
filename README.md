# CoTrack
## Overview
CoTrack is a Multimodal Learning Analytics tool which offers an easy-to-use interface for multimodal data collection from collaborative learning activities.

## Key Features

### Custom activity design

CoTrack allows teachers/researchers to cusomize the group activity and data recording. For example, CoTrack supports two different types of group activities: first, which only involves use of collaborative text editor; second without the text editor.

### Multimodal data collection

CoTrack captures following types of data and provides pre-processed features

* Voice activity detection (VAD): Data indicating whether someone speaks or not.
* Speech to text: Transcript from audio data using Google speech-to-text api in real time (only supported in chrome browser).
* Writing logs: Log data of participants' writing in collaborative text editor. Activity monitoring

### Analytics dashboard
CoTracks offers a real-time dashboard (updates every 30 seconds) presenting a social network (who is talking after whom network) and groups' writing activities in terms of number of revisions made.

### Prediction of collaboration quality and recommendations
CoTrack integrates machine learning models to predict collaboration quality of a group based on speaking activity distribution, features from speech data, and writing activities. Based on predicted collaboration quality, some recommendations are provided to assist teachers in improving the siution if detected LOW.

## Technology Stack

-   **Backend:** Django
-   **Database:** MySQL (recommended)
-   **Frontend:** HTML, Bootstrap5, Java Script

## Project Status

🚧 **Under active development**

* Customizing usage experience based on human-AI teaming levels such as situational and operational.
* Integrates prediction into analytics dashboard
* Storage of predicted values in database for later viewing

## Installation
The following steps offer guidelines on setting up & running SEEDS app on a local machine.

### Clone the CoTrack repository

```
git clone https://github.com/pankajchejara23/Taico-cotrack.git
```


### Install required packages

```
cd Taico-cotrack
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


## Maintainer

For questions, research collaboration, or support, please contact the
project maintainer: Pankaj Chejara (pankajch@tlu.ee).
