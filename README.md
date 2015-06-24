# README #

A Maya script to procedurally generate John Edmark's golden-ratio inspired zoetrope geometries.

### Configuring Your PYTHONPATH ###

In order for Maya to find this python script, you must add its location to your PYTHONPATH environment variable.  You can add this location in your ~/.bashrc, but I've found it easier to only modify Maya's PYTHONPATH.  Explaination [here](http://help.autodesk.com/view/MAYAUL/2015/ENU/?guid=Python_Python_in_Maya).  Finally, I recommend creating a custom shelf button to run the script.

##### INSTRUCTIONS #####

* If you don't already have a userSetup.py file, create one:
    * Windows: `C:\Documents and Settings\<username>\My Documents\maya\<Version>\scripts\userSetup.py`
    * Mac OS X: `~/Library/Preferences/Autodesk/maya/<version>/scripts/userSetup.py`

* Make sure userSetup.py contains the following:

```
    import sys
    sys.path.append("<location of cloned repository>")
```


* In Maya, you can now create a shelf button to run the script (or just run it in the script editor):

```
    import blooms.hemisphere
    reload(blooms.hemisphere)
    blooms.hemisphere.run()
```