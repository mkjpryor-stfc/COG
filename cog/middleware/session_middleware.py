'''
Session-related middleware
'''

from datetime import datetime
from django.conf import settings
from cog.models import update_user_projects, update_user_tags, isUserRemote
from cog.views.utils import set_openid_cookie
from django.core.exceptions import ObjectDoesNotExist

class SessionMiddleware(object):
    
    def process_request(self, request):
        '''
        Method called before processing of the view.
        Used to periodically update the user's projects.
        '''
        
        # must not use shared anonymous session
        try:
            if request.user.is_authenticated() and request.user.profile.openid() is not None:
            
                s = request.session
                last_accessed_seconds = s.get('LAST_ACCESSED', 0) # defaults to Unix Epoch
                now_seconds = int(datetime.now().strftime("%s"))
                
                if now_seconds - last_accessed_seconds > settings.MY_PROJECTS_REFRESH_SECONDS:
                    
                    # update the user's projects across the federation                
                    update_user_projects(request.user)
                    
                    # update the user tags from their home site
                    if isUserRemote(request.user):
                        update_user_tags(request.user)
                    
                    # refresh session stamp
                    s['LAST_ACCESSED'] = now_seconds
                    s.save()
                    
        except ObjectDoesNotExist:
            pass # no profile
                
        # keep on processing this request
        return None


    def process_response(self, request, response):
        '''
        Method called before response is returned to the browser.
        '''
        
        try:
            if request.user.is_authenticated() and request.user.profile.openid() is not None:
                
                # check for 'LAST_ACCESSED' cookie - if found, store it in session
                # this mechanism allows to force a reloading of the user settings
                print 'looking at cookie=%s' % request.COOKIES.get('LAST_ACCESSED', None)
                #for key, value in request.COOKIES.items():
                #    print 'found cookie=%s value=%s' % (key, value)
                if request.COOKIES.get('LAST_ACCESSED', None):
                    print 'Found LAST_ACCESSED in request'
                    s = request.session
                    s['LAST_ACCESSED'] = int( request.COOKIES['LAST_ACCESSED'] )
                    
                    response.delete_cookie('LAST_ACCESSED')
                    
        except AttributeError:
            pass
                
        return response