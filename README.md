# django-tutu

This project is a django based performance monitor. It is much like munin, but is written as a django app, so it is easy to deploy alongside a Django project.

Every line of code written for this project has been recorded and uploaded to youtube. You can watch these videos [here.](https://www.youtube.com/playlist?list=PLhcom2KQ70q9KN0ZcbWMNCFLTZvGw_DAx)

This project works in both Python 2.7 and Python 3.0+. It works with Django 1.11 and 3.0

## Installation

1. Install module:
    
```console
pip install django-tutu
```

2. Add settings:

```python
from tutu.metrics import *
INSTALLED_TUTU_METRICS = [Uptime, SystemLoad, Memory]
```
3. Add urls to your project's urls.py:

In Django 1.11:

```python
url('tutu/', include("tutu.urls"))
```

or with Django 3.0:

```python
path('tutu/', include("tutu.urls"))
```
4. Run `manage.py migrate tutu` to generate the databse tables.

5. Add the `tutu_tick` management command to your system's crontab and have it run every 5 minutes (or however often you would like)

```console
crontab -e
* * * * */5 python /path/to/manage.py tutu_tick
````
6. Point your browser to `/tutu` to see pretty graphs.
