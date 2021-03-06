#!/usr/bin/python

import logging
import os
import shelve
import sys

import flickr
import configuration

existingSets = None
user = None
# set to true if Sets should be called only by the name of the last subfolder
onlySubs = configuration.configdict.get('only_sub_sets')

def  creatSet(photoSet, setName):
    msg = "Generating set %s with %d pictures" % (setName, len(photoSet))
    logging.debug(msg)
    print msg
    setName = setName.replace('\\',' ')
    setName = setName.replace('/',' ')
    setName = setName.strip()
    photos = [] #real photo objects
    for p in photoSet:
        photos.append(flickr.Photo(id = p))

    fset = None
    #check if set with the name exists already
    for s in existingSets:
        if(s.title == setName):
            fset= s
            logging.debug('tags2set: Found existing set %s' % setName)
           # return
            break
    try:
        if(fset == None):
            logging.debug("tags2set: create set %s with photo %s\n\n" % (setName, photos[0]))
            fset = flickr.Photoset.create(photos[0], setName, 'auto generated by folders2flickr')
            logging.debug('tags2set: created new set %s' % setName)
    except Exception, ex:
        logging.error('tags2set: Cannot create set "%s"' % setName)
        logging.error(str(ex))
        logging.error(sys.exc_info()[0])

    try:
        fset.editPhotos(photos)
    except:
        logging.error('tags2set: Cannot edit set %s' % setName)
        logging.error(sys.exc_info()[0])


    logging.debug('tags2set: ...added %d photos' % len(photos)  )
    return fset

def image2set(image):
    if(onlySubs.startswith('true')):
        _, setName = os.path.split(os.path.dirname(image))
    else:
        setName = os.path.dirname(image) #set name is realy a directory
    return setName

def createSets(uploaded_now, historyFile):
    global existingSets
    global user

    logging.debug('tags2set: Started tags2set')
    try:
        user = flickr.test_login()
        logging.debug(user.id)
        existingSets=user.getPhotosets()
    except:
        logging.error(sys.exc_info()[0])
        return None

    uploaded = shelve.open( historyFile )
    keys = uploaded.keys()
    keys.sort()
    uploaded_sets = set()
    for uploadedid in uploaded_now:
        try:
            image = uploaded[str(uploadedid)]
        except KeyError:
            continue
        uploaded_sets.add(image2set(image))

    lastSetName =''
    photoSet =[]
    setName = ''
    for image in keys:
        if image.find(os.path.sep) > -1: #filter out photoid keys
            setName = image2set(image)
            # only update sets that have been modified this round
            if setName not in uploaded_sets:
                continue

            if(not lastSetName == setName and not lastSetName == ''):
                #new set is starting so save last
                creatSet(photoSet, lastSetName)
                photoSet = []
            logging.debug("tags2set: Adding image %s" % image)
            photoSet.append(uploaded.get(image))
            lastSetName = setName

    #dont forget to create last set
    if len(photoSet) > 0:
        creatSet(photoSet, setName)
