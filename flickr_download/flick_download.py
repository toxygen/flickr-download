#!/usr/bin/python
#
# Util to download a full Flickr set.
#

from __future__ import absolute_import
from __future__ import unicode_literals
import argparse
import errno
import logging
import os
import sys
import time

import flickr_api as Flickr
from dateutil import parser
import yaml

CONFIG_FILE = "~/.flickr_download"
TOKEN_FILE= "~/.flickr_token"
    
def _init(key, secret, oauth):
    """
    Initialize API.

    @see: http://www.flickr.com/services/api/

    @param key: str, API key
    @param secret: str, API secret
    """
    Flickr.set_keys(key, secret)
    
    if oauth:
    	if os.path.exists(os.path.expanduser(TOKEN_FILE)):
            Flickr.set_auth_handler(os.path.expanduser(TOKEN_FILE))
        else:
            a = Flickr.auth.AuthHandler() #creates the AuthHandler object
            perms = "read" # set the required permissions
            url = a.get_authorization_url(perms)
            print
            print "Enter following url to the browser to authorize application"
            print url
            print "Copy paste <oauth_verifier> value from xml and press return"
            Flickr.set_auth_handler(a)
            token = raw_input()
            a.set_verifier(token)
            a.save(os.path.expanduser(TOKEN_FILE))

def _load_defaults():
    """
    Load default parameters from config file

    @return: dict, default parameters
    """
    filename = os.path.expanduser(CONFIG_FILE)
    logging.debug('Loading configuration from {}'.format(filename))
    try:
        with open(filename, 'r') as cfile:
            vals = yaml.load(cfile.read())
            return vals
    except yaml.YAMLError as ex:
        logging.warning('Could not parse configuration file: {}'.format(ex))
    except IOError as ex:
        if ex.errno != errno.ENOENT:
            logging.warning('Could not open configuration file: {}'.format(ex))
        else:
            logging.debug('No config file')

    return {}

def download_list(list, directory, size_label=None):
    for photo in list:
        fname = '{0}.jpg'.format(photo.id)
        if os.path.exists(fname):
            # TODO: Ideally we should check for file size / md5 here
            # to handle failed downloads.
            print 'Skipping {0}, as it exists already'.format(fname)
            continue
		
        print 'Saving: {0}'.format(fname)
		# Must be in try block as sometimes flickr returns 404 not found
        try:
            photo.save(fname, size_label)
			 # Set file times to when the photo was taken
            info = photo.getInfo()
            taken = parser.parse(info['taken'])
            taken_unix = time.mktime(taken.timetuple())
            os.utime(fname, (taken_unix, taken_unix))
        except:
            print "Ooops photo couldn't be downloaded"

def download_set(set_id, size_label=None):
    """
    Download the set with 'set_id' to the current directory.

    @param set_id: str, id of the photo set
    @param size_label: str|None, size to download (or None for largest available)
    """
    pset = Flickr.Photoset(id=set_id)
    photos = Flickr.Walker(pset.getPhotos)
    download_list(photos, size_label)

def print_sets(username):
    """
    Print all sets for the given user

    @param username: str,
    """
    user = Flickr.Person.findByUserName(username)
    photosets = Flickr.Walker(user.getPhotosets)
    for set in photosets:
        print u"{0} - {1}".format(set.id, set.title)

def download_photos(username, size_label=None):
    """
		Download photos from user 'username' to the current directory.
		
		@param username: str, name of the user
		@param size_label: str|None, size to download (or None for largest available)
		"""

    user = Flickr.Person.findByUserName(username)
    photos = Flickr.Walker(user.getPhotos)
    download_list(photos, size_label)

def list_photos(username):
    """
		Print all photos of the given user
		
		@param username: str,
		"""
    user = Flickr.Person.findByUserName(username)
    photos = Flickr.Walker(user.getPhotos)
    for photo in photos:
        print u"{0} - {1}".format(photo.id, photo.title)

    print("Number of total photos: %s" % user.getPhotos().info.total)

def download_sets(username, size_label=None):
    user = Flickr.Person.findByUserName(username)
    photosets = Flickr.Walker(user.getPhotosets)

    for set in photosets:
        if not os.path.exists(set.id):
            os.mkdir(set.id)
        os.chdir(set.id)
        download_set(set.id)
        os.chdir(os.pardir)

def download_all(username, size_label=None):
    download_photos(username)
    download_sets(username)

def main():
    parser = argparse.ArgumentParser('Download a Flickr Set')
    parser.add_argument('-k', '--api_key', type=str,
                        help='Flickr API key')
    parser.add_argument('-s', '--api_secret', type=str,
                        help='Flickr API secret')
    parser.add_argument('-t', '--api_token', action='store_true',
                        help='Use OAuth token')
    parser.add_argument('-l', '--list', type=str,
                        help='List photosets for a user')
    parser.add_argument('-p', '--photos', type=str,
						help='List photo of a user')
    parser.add_argument('-d', '--download', type=str,
                        help='Download the given set')
    parser.add_argument('-u', '--photostream', type=str,
                        help='Download photostream of user')
    parser.add_argument('-o', '--photosets', type=str,
                        help='Download all photosets of user')
    parser.add_argument('-x', '--all', type=str,
                        help='Download all photosets and photos of user')



    parser.set_defaults(**_load_defaults())
    
    args = parser.parse_args()

    if not args.api_key or not args.api_secret:
        print >> sys.stderr, 'You need to pass in both "api_key" and "api_secret" arguments'
        return 1
 
    _init(args.api_key, args.api_secret, args.api_token)
    if args.list:
        print_sets(args.list)
    elif args.download:
        download_set(args.download)
    elif args.photos:
	    list_photos(args.photos)
    elif args.photosets:
        download_sets(args.photosets)
    elif args.photostream:
        download_photos(args.photostream)
    elif args.all:
        download_all(args.all)
    else:
        print >> sys.stderr, 'ERROR: Must pass either --list or --download\n'
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())
