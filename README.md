# Python SharePoint

This is a Python-based SharePoint interface, geared toward NTLM/AD/LDAP authentication.

## Why

I created this because, despite 25 projects appearing on PyPI for the search term 'sharepoint', some were authentication only, some were extremely application-specific, some had nothing to do with SharePoint. There were a couple of others that either only supported Python 2, only supported SharePoint 2010 (somehow that one didn't work with my test server, though most of the API endpoints should be the same), provided little-to-no documentation, or hadn't been updated in months or years _and_ didn't work.

Also, I wanted to learn how the SharePoint REST API worked. [easy_sharepoint](https://github.com/krzysztofgrowinski/EasySharePoint) _might_ work for most of this, but it was missing a couple of methods I wanted. Because of my secondary goal, I wrote this from scratch.

## Basic Example:

```python
from sharepoint import SharePointSite

site=SharePointSite('https://example.com/path/to/sharepoint/site',
                    'username',
		    'password',
		    return_format='json',
		    search_tree=False)
site.get_file_property('/file/relative/path','property name')
                                     #returns the property, e.g.
				     #'UIVersion'
site.get_file('/file/relative/path') #downloads the file, saves to
                                     #current working directory, and
				     #returns path of file
site.get_file('/file/relative/path',version) #downloads a particular
                                     #version of a file. UIVersion,
				     #not displayed version
				     #(a.k.a. UIVersionLabel)
```

## Explicit Dependencies

**_These modules contain their own dependencies_**

* requests
* requests_ntlm

## Current Methods

* `__init__(url,username,password,return_format='json',search_tree=False)`
    * `url` is the URL of the SharePoint site, or possibly any valid URL within that site (see `search_tree` parameter)
    * `username`: hopefully self-explanatory.
    * `password`: hopefully self-explanatory. Yes, it's plaintext. Yes, I'm working on fixing that, but somewhere, someone's going to have to code how to handle getting it.
    * `return_format` alters the HTTP `Accept` header. Default is JSON, but XML is the other value that SharePoint will return. I only have handlers for JSON, however, so any parsing done without this will require external processing.
    * `search_tree`, if true, will scan the path of the given URL to find the top-level valid SharePoint site URL.
* `get_all_lists()`
* `get_list(list_name)`
* `get_base_folders()`
* `get_folder_list(folder_name,expand=0,prepend_base_path=True)`
    * `folder_name`: hopefully this is self-explanatory.
    * `expand` is an integer to expand folders below given level. Depending on structure, sometimes the server will :poop: if this value is too high.
    * `prepend_base_path` prepends `folder_name` with `base_path` (see below) to ensure you're looking in the right place. This is usually required.
* `get_folder_property(folder_name,property_name,prepend_base_path=True)`
* `get_file_list(folder_name,prepend_base_path=True)`
* `get_file_info(file_name,prepend_base_path=True)`
    * `file_name`: hopefully this is self-explanatory.
* `get_file_property(file_name,property_name,prepend_base_path=True)`
* `get_file(file_name,version=None,prepend_base_path=True)`
    * `version` is SharePoint's version number, not yours or the version SharePoint displays. Unfortunately. In theory there's a way to get the file by one of those other version numbers, but I haven't been able to make it work yet, so right now we're stuck with this.
* `get_relative_path_from_link(link)`
    * `link` is meant to be the link from a file sharing link popup, and returns the relative path of the file to be used with the rest of this module to get file info, properties, the actual file, etc.
* `simple_query(querytext,**kwargs)`
    * `querytext` is whatever you might type into the search box of the actual SharePoint site.
* `query` (currently just an alias for `simple_query`)

## Class Values

* `auth` is the requests_ntlm.HttpNtlmAuth object for authentication.
* `site_url` is the site url: https://example.com/path/to/sharepoint/site above.
* `server_url` is the server url, or the domain: https://example.com above
* `base_path` is the base path, usually required when browsing folders and files: /path/to/sharepoint/site above.
* `api_url` is the URL for the REST API, which is `site_url` appended with '/_api/web/'. Unfortunately this is not correct for *every* API call, but it hits most of them.
* `return_format` currently has two acceptable values: 'json' and anything else. This determines the HTTP `Accept` header.

## Under The Hood

**Explaining my choices**

I created this class for a [Django](https://djangoproject.com)-based website I worked on. One issue I had was getting the correct path for the SharePoint site given any valid SharePoint URL. Lines 13 through 32 of `sharepoint.py` are all dedicated to locating the correct path of the base SharePoint site. I'm not 100% sure this is correct, and am aware that a `P3P` header is far from a guarantee that the visited site is a SharePoint one, but it served as a shortcut for me. It probably won't work for some users at all, and the W3C P3P specification has been obsoleted as of 30 August 2018. Basically, downloading a file did not return this header, but `Content-Type: text/html` didn't work for me either because of the structure of the server I was developing this for (partly because that server hosted/hosts several SharePoint sites). I couldn't see any *other* header that looked unique for the set of URLs being tested. I will attempt to improve this checking in the future. Possibly some analysis of the content of the returned page will give me a more accurate test, but I haven't done that yet.

Another wrinkle in the way I wrote this module is the fact that I embedded authentication in the constructor. This should probably be separated, in the event that a SharePoint site is public or uses some other form of authentication. As I only had access to a single server, and all sites on this server utilized the same authentication, I could only test the one, and made the shortcut assumption that this would be true regardless. It worked for me, but I know will not be universal.

## Future Plans:

* Improve SharePoint URL checking
* Separate authentication from constructor
* Make `requests_ntlm` optional
* Auto-detect necessity of `prepend_base_path` parameter
* Add more intuitive method of getting file by version.
* Add methods for POST query
    * The `query(json_query)` method exists but is commented out. It works, but is incomplete, and I don't know see what it buys in addition to the simple_query method.
* Add methods to iterate through Collection objects
* Add methods for modifying files/folders on the site:
    * `update_file`
    * `check_out_file`
    * `check_in_file`
    * `undo_check_out`
    * `recycle`
    * `delete`
    * `publish`
    * `unpublish`
    * `approve`
    * `copy_file_to`
    * `move_file_to`
    * `add_file`
* Add a tree walker to get more information from `_deferred` fields
* Add type hints (PEP 484)
* Edit to meet PEP8 code styling guidelines (except for the "follow Strunk and White" bit, see [here](https://www.chronicle.com/blogs/linguafranca/2018/06/20/strunk-at-100-a-centennial-not-to-celebrate/), [here](http://www.lel.ed.ac.uk/~gpullum/LandOfTheFree.html), and [here](https://www.quickanddirtytips.com/education/grammar/strunk-and-white))
* Add comments and docstrings!
* Add readthedocs/Sphinx/MkDocs documentation
* Add testing if possible
* Add `'xml'` as valid `return_format`, with `lxml`
* Automate versioning for wheel builds
* Submit to PyPI
