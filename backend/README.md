# Backend

run using 
python manage.py runserver

You can view the schema using url .../schema-viewer/

There is a postgres dumpfile in data/ if you want to load it
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb', 
        'USER': 'myuser',
        'PASSWORD': 'mypassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}