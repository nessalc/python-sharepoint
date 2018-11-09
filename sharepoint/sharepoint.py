from requests_ntlm import HttpNtlmAuth
import json
import requests
import urllib.parse
from pathlib import PurePosixPath as P
from pathlib import Path
import dateutil.parser

HOMEPAGE='SitePages/Home.aspx'

class SharePointSite:
    def __init__(self,url,username,password,return_format='json',search_tree=True):
        self.auth=HttpNtlmAuth(username,password)
        if url[-1]!='/':
            url+='/'
        parsed=urllib.parse.urlsplit(url)
        if search_tree:
            for test_uri in [parsed[2]]+list(P(parsed[2]).parents)[::-1]:
                url=urllib.parse.urljoin(urllib.parse.urlunsplit([parsed[0],parsed[1],str(test_uri)+'/','','']),HOMEPAGE)
                r=requests.get(url,auth=self.auth)
                if r.status_code==200 and 'P3P' not in r.headers.keys():
                    site_url=urllib.parse.urlunsplit([parsed[0],parsed[1],str(test_uri),'',''])
                    if site_url[-1]!='/':
                        site_url+='/'
                    break
            else:
                raise Exception('No SharePoint site found with given URL.')
        else:
            r=requests.get(url,auth=self.auth)
            if r.status_code==200 and 'P3P' not in r.headers.keys():
                site_url=url
            else:
                raise Exception('No SharePoint site found with given URL.')
        self.site_url=site_url
        parsed=urllib.parse.urlsplit(site_url)
        self.server_url=urllib.parse.urlunsplit([parsed[0],parsed[1],'','',''])
        self.base_path=parsed[2]
        self.api_url=urllib.parse.urljoin(site_url,'_api/web/')
        self.return_format=return_format
        if return_format=='json':
            self.headers={'Accept':'application/json;odata=verbose'}
        else:
            self.headers={}
    def __fetch(self,url,return_format):
        if return_format!=self.return_format and return_format=='json':
            headers={'Accept':'application/json;odata=verbose'}
        else:
            headers=self.headers
        r=requests.get(url,auth=self.auth,headers=headers)
        if self.return_format=='json' and r.status_code==200:
            try:
                return r.json()['d']['results']
            except json.decoder.JSONDecodeError:
                return r
            except KeyError:
                try:
                    return r.json()['d']
                except KeyError:
                    return r
        elif r.status_code!=200:
            r.raise_for_status()
        else:
            return r.text
    def get_all_lists(self):
        url=urllib.parse.urljoin(self.api_url,
                                 'lists')
        return self.__fetch(url,self.return_format)
    def get_list(self,list_name):
        url=urllib.parse.urljoin(self.api_url,
                                 "lists/GetByTitle('{}')/items".format(list_name))
        return self.__fetch(url,self.return_format)
    def get_base_folders(self):
        url=urllib.parse.urljoin(self.api_url,'folders')
        return self.__fetch(url,self.return_format)
    def get_folder_list(self,folder_name,expand=0,prepend_base_path=True):
        return self.get_folder_property(folder_name,'Folders',prepend_base_path)
    def get_folder_property(self,folder_name,property_name,prepend_base_path=True):
        if prepend_base_path:
            folder_name=urllib.parse.urljoin(self.base_path,folder_name)
        url=urllib.parse.urljoin(self.api_url,
                                 "GetFolderByServerRelativeUrl('{}')/{}".format(folder_name,property_name))
        return self.__fetch(url,self.return_format)[property_name]
    def get_file_list(self,folder_name,prepend_base_path=True):
        return self.get_folder_property(folder_name,'Files',prepend_base_path)
    def get_file_info(self,file_name,prepend_base_path=True):
        if prepend_base_path:
            file_name=urllib.parse.urljoin(self.base_path,file_name)
        url=urllib.parse.urljoin(self.api_url,
                                 "GetFileByServerRelativeUrl('{}')".format(file_name))
        return self.__fetch(url,self.return_format)
    def get_file_id(self,file_path,prepend_base_path=True):
        fdict=self.get_file_property(file_path,'ListItemAllFields',prepend_base_path)
        return fdict['Id']
    def get_file_property(self,file_name,property_name,prepend_base_path=True):
        if prepend_base_path:
            file_name=urllib.parse.urljoin(self.base_path,file_name)
        url=urllib.parse.urljoin(self.api_url,
                                 "GetFileByServerRelativeUrl('{}')/{}".format(file_name,property_name))
        try:
            return self.__fetch(url,self.return_format)[property_name]
        except (TypeError,KeyError):
            return self.__fetch(url,self.return_format)
    def get_file(self,file_name,version=None,prepend_base_path=True):
        if version:
            url=urllib.parse.urljoin(self.site_url,self.get_file_property(file_name,'versions({})/Url'.format(version))['Url'])
            data=self.__fetch(url,self.return_format).content
        else:
            data=self.get_file_property(file_name,'openbinarystream',prepend_base_path).content
        fname=Path(file_name)
        suffix=''.join(fname.suffixes)
        if version:
            fname=fname.name[:-len(suffix)]+'.{}'.format(version)+suffix
        else:
            fname=fname.name
        file=open(fname,'wb')
        file.write(data)
        file.close()
        return Path.cwd().joinpath(fname)
    def __dictify(self,resultlist):
        result={}
        for i in resultlist:
            if i['ValueType']=='Edm.Double':
                v=float(i['Value'])
            elif i['ValueType'] in ['Edm.String','Edm.Guid']:
                v=i['Value']
            elif i['ValueType'] in ['Edm.Int64','Edm.Int32']:
                v=int(i['Value'])
            elif i['ValueType']=='Null':
                v=None
            elif i['ValueType']=='Edm.DateTime':
                v=dateutil.parser.parse(i['Value'])
            elif i['ValueType']=='Edm.Boolean':
                v=(i['Value']=='true')
            result[i['Key']]=v
        return result
    def __get_deferred_properties(self,resultdict):
        if self.return_format=='json':
            for k,v in resultdict.items():
                if isinstance(v,dict) and '__deferred' in v.keys():
                    try:
                        resultdict[k]=self.__fetch(v['__deferred']['uri'],self.return_format)
                    except requests.exceptions.HTTPError:
                        pass
        return None
    def get_relative_path_from_link(self,link):
        if link.find(self.site_url)==0:
            parsed=urllib.parse.urlsplit(link)
            return urllib.parse.unquote(parsed[2][len(self.base_path):])
        return None
##    def query(self,json_query):
##        if 'X-RequestDigest' not in self.headers.keys():
##            r=requests.post(self.query_url,
##                            auth=self.auth)
##            self.headers['X-RequestDigest']=r.headers['X-RequestDigest']
##        result=requests.post(self.query_url,
##                             data=json_query,
##                             auth=self.auth,
##                             headers={'X-RequestDigest':r.headers['X-RequestDigest'],
##                                      'Content-Type':'application/json;odata=verbose',
##                                      'Accept':'application/json;odata=verbose'})
##        return result.json()['d']['postquery']
    def simple_query(self,querytext,**kwargs):
        for k,v in kwargs.items():
            kwargs[k]="'{}'".format(v)
        kwargs.update({'querytext':"'{}'".format(querytext)})
        r=requests.get(urllib.parse.urljoin(self.site_url,'_api/search/query'),
                       kwargs,
                       auth=self.auth,
                       headers={'Accept':'application/json;odata=verbose'})
        try:
            r=r.json()['d']['query']['PrimaryQueryResult']['RelevantResults']
            t=r['Table']['Rows']['results']
            return [self.__dictify(t[k]['Cells']['results']) for k in range(len(t))]
        except KeyError:
            return r
    def find_file_version(self,filename,file_id,file_version=None):
        r=self.query('listitemid:{} and filename:"{}"'.format(file_id,filename))
        if len(r)==1:
            k=self.get_file_info(r[0]['Path'].replace(self.server_url,''),False)
            if file_version is None:
                return {'Version':k['UIVersion'],
                        'UIVersionLabel':k['UIVersionLabel'],
                        'URL':urllib.parse.urljoin(self.server_url,k['ServerRelativeUrl'])}
            elif k['UIVersionLabel']==str(file_version):
                return {'Version':k['UIVersion'],
                        'URL':urllib.parse.urljoin(self.server_url,k['ServerRelativeUrl'])}
            self.__get_deferred_properties(k)
            for v in k['Versions']:
                if v['VersionLabel']==str(file_version):
                    return {'Version':v['ID'],
                            'URL':urllib.parse.urljoin(self.site_url,v['Url'])}
            return None
        elif len(r)==0:
            raise Exception('No results found!')
        else:
            raise Exception('Too many results found!')
    query=simple_query
