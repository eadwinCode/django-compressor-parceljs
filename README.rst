Django Compressor with Parceljs
=====================================
Django-compressor_ with parceljs_ is base on Django-Compressor, which bundles and minifies your typescript, vue, react, scss etc in a Django template into cacheable static files using parceljs and django-compressor.

For more information visit Django-Compressor_


Quickstart
----------
Install django-compress::

    pip install git+https://github.com/eadwinCode/django-compressor.git@develop
 
Install parcel-bundler::

    npm install -g parcel-bundler

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'compressor',
        ...
    )
    
    STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        # other finders..
        'compressor.finders.CompressorFinder',
    )

Other Configurations
--------------------

To minify your code for production, you need to set COMPRESS_ENABLED and COMPRESS_OFFLINE to true in settings.py.

In django-compressor, the value of COMPRESS_ENABLED = !DEBUG is not set in the settings.

.. code-block:: python

    COMPRESS_ENABLED = True
    COMPRESS_OFFLINE = True

For more information on django-compressor-settings_

Usage
-----
In your template, load compress ``{% load compress %}``
then use ``{% compress parcel %} <script> {% endcompress %}`` to load a script. for example:

.. code-block:: html

    {% load static %} 
    {% load compress %}
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>Vue Django Testing</title>
      </head>
      <body>
        ....
       {% compress parcel file myts %}
        <script src="{% static 'js/index.ts' %}"></script>
       {% endcompress %}
      </body>
      ...
      
Vue example
-----------
Create a vue project in your django project root ::

    npm init --yes
    npm install -D vue-template-compiler, @vue/component-compiler-utils
    npm install vue
    
In your django project app create ::

    static/components/test.vue
    static/js/index.js
    
In static/components/test.vue,

.. code-block:: vue

    <template>
      <div>
        <h1>{{ message }}</h1>
      </div>
    </template>

    <script>
        export default {
          name: "app",
          components: {},
          data: {
            message: "Hello Vue",
          },
          computed: {}
        };
        </script>

    <style lang="scss">
    </style>
In static/js/index.js,

.. code-block:: javascript

    import Vue from "vue";
    import test  from "../components/test.vue";
    new Vue(test).$mount("#components-demo");

In your django template,

.. code-block:: html
    
    {% load static %} 
    {% load compress %}
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>Vue Django Testing</title>
      </head>
      <body>
        ....
       <div id="components-demo"></div>
       {% compress parcel file myjs %}
         <script src="{% static 'js/index.js' %}"></script>
       {% endcompress %}
      </body>
      ...

Run ``runserver`` ::

    python manage.py runserver

You have successfully bundled your vue app into your django template.  

Using Parceljs to bundle SASS, SCSS, LESS
-----------------------------------------
Integrating compilers into django-compressor is quiet very easy. All you need is to provide a COMPRESS_PRECOMPILERS option in django ``settings.py``. For more information visit django-compressor precompilers_

.. code-block:: python

    COMPRESS_PRECOMPILERS = (
        ('text/coffeescript', 'coffee --compile --stdio'),
        ('text/less', 'lessc {infile} {outfile}'),
        ('text/x-sass', 'sass {infile} {outfile}'),
        ('text/x-scss', 'sass --scss {infile} {outfile}'),
        ('text/stylus', 'stylus < {infile} > {outfile}'),
        ('text/foobar', 'path.to.MyPrecompilerFilter'),
    )
    
Use ``compressor.filters.parceljs.ParserFilterCSS`` on scss, sass or less in COMPRESS_PRECOMPILERS options as filter. For example: 

.. code-block:: python

    COMPRESS_PRECOMPILERS = (
        # ('text/coffeescript', 'coffee --compile --stdio'),
        ('text/less', 'compressor.filters.parceljs.ParserFilterCSS'),
        # ('text/x-sass', 'sass {infile} {outfile}'),
        ('text/x-scss', 'compressor.filters.parceljs.ParserFilterCSS'),
        # ('text/stylus', 'stylus < {infile} > {outfile}'),
        # ('text/foobar', 'path.to.MyPrecompilerFilter'),
    )

In your template, 

.. code-block:: html

    {% load static %} 
    {% load compress %}
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>Vue Django Testing</title>
        {% compress css file style %}
            <link rel="stylesheet" type="text/x-scss"  href="{% static 'css/style.scss'%}">
        {% endcompress %}
      </head>
      <body>
      .......

Add the ``type="text/x-scss"`` for django-compressor to use the precompiler options to compile the asset.

There is alittle drawback with parceljs css url resolver. There is no configuration for parceljs to ignore resolving css url since django will always resolve static urls automatically. Read more this issue_

A solution is to use ``///..`` in the url path followed by ``/static/(filepath)``

.. code-block:: scss

    body{
        background-color: lightblue;
        background-image: url(///../static/img/ssd/avatar1.png);

        button{
            font-size: .8rem;
        }
    }

Using typescript directly in django template
--------------------------------------------
Add lang attribute to the script tag ``<script lang="ts"></script>`` ::

    npm init --yes
    npm install -D @babel/core, @babel/preset-env, typescript

.. code-block:: ts

    {% load static %} 
    {% load compress %}
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <title>Vue Django Testing</title>
      </head>
      <body>
        ....
       {% compress parcel file myts %}
         <script lang="ts">
            interface IUser {
                name: string,
                age: number
            }

            class User implements IUser{
                constructor(user:IUser){
                    this.name = user.name
                    this.age = user.age
                }
                name: string    
                age: number

                get_name = () => {
                    return this.name
                };
            }

            const Peter = new User({name:'Peter', age:32})
            console.log(Peter)
         </script>
       {% endcompress %}
      </body>
      ...

.. _Django-Compressor: https://github.com/django-compressor/django-compressor
.. _parceljs: https://parceljs.org
.. _django-compressor-settings: https://django-compressor.readthedocs.io/en/latest/settings/
.. _precompilers: https://django-compressor.readthedocs.io/en/latest/settings/#django.conf.settings.COMPRESS_PRECOMPILERS
.. _issue: https://github.com/parcel-bundler/parcel/issues/1186/
