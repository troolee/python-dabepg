#===============================================================================
# Python DAB EPG API - Serialize/Deserialize To/From objects to XML/Binary as per
# ETSI specifications TS 102 818 (XML Specification for DAB EPG) and TS 102 
# 371 (Transportation and Binary Encoding Specification for EPG).
# 
# Copyright (C) 2010 Global Radio
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#===============================================================================


import datetime
import locale
import re
from dateutil.tz import tzlocal
import logging

logger = logging.getLogger('dabepg')

MAX_SHORTCRID = 16777215
TRIGGER_PATTERN = '[0-9a-fA-F]{8}'

class Bearer:  
    """DAB Bearer details

    :param id: ContentId
    :type id: ContentId
    :param trigger: Trigger found in the broadcast stream that indicates when
    a programme is being broadcast. This is the two SId and two PNum bytes
    from the DAB FG0/16 Programme Number - this should be a complete set of
    8 hexadecimal characters.
    :type trigger: str
    """
    def __init__(self, id, trigger=None):
        """Creates the Bearer"""

        if isinstance(id, str): id = ContentId.fromstring(id)
        self.id = id
        self.trigger = trigger
        if trigger is not None and re.match(TRIGGER_PATTERN, trigger) is None:
            raise ValueError('trigger does not match the following pattern ' + TRIGGER_PATTERN)
        
    def __eq__(self, other):
        if isinstance(other, Bearer):
            return self.id == other.id and self.trigger == other.trigger            
        
    def __str__(self):
        return '%s' % self.id
    
    def __repr__(self):
        return '<Bearer: %s>' % str(self)
        

CONTENTID_PATTERN = '([0-9a-fA-F]{2})\\.([0-9a-fA-F]{4})(\\.([0-9a-fA-F]{4,8})\\.([0-9a-fA-F]{1})){0,1}'

class ContentId:
    """DAB ensemble Content ID, of the form:
    
    ::
    
    <ECC>.<EId>.<SId>.<SCIdS>.<XPad> in hex
    
    Where ``ECC`` (Extended Country Code) and ``EId`` (Ensemble Identifier) are optional. The ``SId``
    (Service ID) is either a 16-bit service identifier (for audio services) or a 32-bit service identifier
    (for data services).
    
    The ``XPad`` (XPAD application type) is optional.
    
    For example:
    
    ::
        
        e1.ce15.c221.0.1
        c224.0
    
    For DRM, this is the content of the DRM channel. It shall be a string of the form:
    
    ::
        
        <SId> in hex
    
    The ``SId`` (Service ID) is the 24-bit service identifier.
    
    For example:
    
    :: 
    
        e1c238
    """
    
    def __init__(self, ecc, eid, sid=None, scids=None, xpad=None):
        """Values can be passed in as hex string or integers"""
        self.sid = sid
        self.scids = scids
        self.xpad = xpad
        
        # ECC    
        if isinstance(ecc, int): self.ecc = ecc
        else: self.ecc = int(ecc, 16)
        
        # EId
        if isinstance(eid, int): self.eid = eid
        else: self.eid = int(eid, 16)
            
        # SId
        if sid:
            if isinstance(sid, int): self.sid = sid
            else: self.sid = int(sid, 16)
                  
        # SCIdS
        if scids:
            if isinstance(scids, int): self.scids = scids
            else: self.scids = int(scids, 16)                      

        # XPAD
        if xpad:
            if isinstance(xpad, int): self.xpad = xpad
            else: self.xpad = int(xpad, 16)  
        
    @classmethod
    def fromstring(cls, string):
        """Parses a ContentId from its string representation"""        
        
        pattern = re.compile(CONTENTID_PATTERN)
        matcher = pattern.search(string)
        if not matcher: raise ValueError('ContentId %s does not match the pattern: %s' % (string, CONTENTID_PATTERN))
        ecc = matcher.group(1)
        eid = matcher.group(2)
        sid = None
        scids = None
        if len(matcher.groups()) > 2:
            sid = matcher.group(4)
            scids = matcher.group(5)
        return ContentId(ecc, eid, sid, scids)
    
    def __str__(self):
        id = '{ecc:02x}.{eid:04x}'.format(ecc=self.ecc, eid=self.eid)
        if self.sid is not None and self.scids is not None:
            id += '.{sid:04x}.{scids:x}'.format(sid=self.sid, scids=self.scids)
        return id
    
    def __repr__(self):
        return '<ContentId: %s>' % str(self)
    
    def __eq__(self, other):
        return str(self) == str(other)
            
        
CRID_PATTERN = 'crid://([^\\/]+)/([^\\/]+)'
        
class Crid:
    """A unique identifier for a programme, programme event or programme group in the format
    of a Content Reference ID as defined in the TV-Anytime specification. It is in the form
    of
    
    ::
    
        crid://<authority>/data
        
    :param authority: Registered Internet domain name that the CRID author has 
    permission to use
    :type id: str
    :param data: free format string that is meaningful to the given authority 
    and should uniquely identify the content within that authority
    :type id: str    
    """
    
    def __init__(self, authority, data):
        self.authority = authority
        self.data = data
        
    @classmethod
    def fromstring(cls, string):
        """Parses a Crid from its string representation"""    
        
        pattern = re.compile(CRID_PATTERN)
        matcher = pattern.search(string)
        authority = matcher.group(0)
        data = matcher.group(1)
        return Crid(authority, data)
        
    def __str__(self):
        return 'crid://%s/%s' % (self.authority, self.data)
    
    
class Ensemble:
    """Used to describe and locate a DAB ensemble or DRM channel.
    
    :param id: Ensemble ID
    :type id: ContentId
    """
    
    def __init__(self, id, version=1):
        self.id = id
        self.names = []
        self.media = []
        self.keywords = []
        self.links = []
        self.services = []
        self.frequencies = []
        self.ca = None
        self.version = version
        
    def __str__(self):
        return str(self.id)
    
    def __repr__(self):
        return '<Ensemble: %s>' % str(self)
    
    
class Epg:
    """The root of an EPG schedule"""
    
    DAB="DAB"
    DRM="DRM"
    
    def __init__(self, schedule, type=DAB):
        self.type = type
        self.schedule = schedule if schedule is not None else Schedule()
    
class Link:
    """This is used to link to additional information of content."""    
        
    def __init__(self, url, mimetype=None, description=None, expiry=None, locale=locale.getlocale()):
        self.url = url
        self.mimetype = mimetype
        self.description = description
        self.expiry = expiry
        self.locale = locale
        
    def __str__(self):
        return self.url
        
        
class Location:
    """Describes the time information and the location in the DAB or DRM channel of a programme.
    There may be:
    
    * One time element and one bearer element
    * One time element and multiple bearer elements
    * One bearer element and multiple time elements
    """
    
    def __init__(self, times=None, bearers=None):
        self.times = times if times is not None else []
        self.bearers = [] if bearers is None else map(lambda x: x if isinstance(x, ContentId) else ContentId.fromstring(str(x)), bearers)
        
    def __str__(self):
        return str(dict(times=self.times, bearers=self.bearers))
    
    def __repr__(self):
        return '<Location: %s>' % str(self)
        
        
class BaseTime:
    """Base for Absolute and Relative times"""
    
    def get_billed_time(self, base):
        raise ValueError('not implemented')
        
    def get_billed_duration(self):
        raise ValueError('not implemented')
        
    def get_actual_time(self, base):
        raise ValueError('not implemented')
        
    def get_actual_duration(self):
        raise ValueError('not implemented')
    
    
class RelativeTime(BaseTime):
    """Time for a :class:ProgrammeEvent relative to the start of the containing :class:Programme"""
    
    def __init__(self, billed_offset, billed_duration, actual_offset=None, actual_duration=None):
        self.actual_offset = actual_offset
        self.actual_duration = actual_duration
        self.billed_offset = billed_offset
        self.billed_duration = billed_duration
    
    def get_billed_time(self, base):
        if self.billed_offset is None: return None
        return base + self.billed_offset
        
    def get_billed_duration(self):
        return self.billed_duration
        
    def get_actual_time(self, base):
        if self.actual_offset is None: return None
        return base + self.actual_offset
        
    def get_actual_duration(self):
        return self.actual_duration
    
    def __str__(self):
        return 'offset=%s, duration=%s' % (str(self.billed_offset), str(self.billed_duration))
    
    def __repr__(self):
        return '<RelativeTime: %s>' % str(self)

        
class Time(BaseTime):
    """Absolute time for a :class:ProgrammeEvent or :class:Programme"""
    
    def __init__(self, billed_time, billed_duration, actual_time=None, actual_duration=None):
        self.actual_time = actual_time
        self.actual_duration = actual_duration
        self.billed_time = billed_time
        self.billed_duration = billed_duration
    
    def get_billed_time(self, base=None):
        return self.billed_time
        
    def get_billed_duration(self):
        return self.billed_duration
        
    def get_actual_time(self, base=None):
        return self.actual_time
        
    def get_actual_duration(self):
        return self.actual_duration

    def __str__(self):
        return 'time=%s, duration=%s' % (str(self.billed_time), str(self.billed_duration))
    
    def __repr__(self):
        return '<Time: %s>' % str(self)

class Text:
    """Abstract class for textual information"""
    
    def __init__(self, text, max_length, locale=locale.getdefaultlocale()):
        if not isinstance(text, basestring): raise ValueError('text must be of a basestring subtype, not %s: %s', type(text), text)
        if len(text) > max_length: 
            #raise ValueError('text length exceeds the maximum: %d>%d' % (len(text), max_length))
            logger.warning('text length exceeds the maximum: %d>%d : %s' % (len(text), max_length, text))
        self.max_length = max_length
        self.text = text
        
    def __str__(self):
        return self.text

    def __repr__(self):
        return '<Text[%d]: %s>' % (self.max_length, self.text)
    
class LongDescription(Text):
    """Long descriptive text, with maximum length of 1800 characters"""
    
    max_length = 1800
    
    def __init__(self, text, locale=locale.getdefaultlocale()):
        Text.__init__(self, text, 1800, locale)

class ShortDescription(Text):
    """Short descriptive text, with maximum length of 180 characters"""
    
    max_length = 180
    
    def __init__(self, text, locale=locale.getdefaultlocale()):
        Text.__init__(self, text, 180, locale)
        
class LongName(Text):
    """Long name text, with maximum length of 128 characters"""
    
    max_length = 128
    
    def __init__(self, text, locale=locale.getdefaultlocale()):
        Text.__init__(self, text, 128, locale)

class MediumName(Text):
    """Medium name text, with maximum length of 16 characters"""

    max_length = 16
    
    def __init__(self, text, locale=locale.getdefaultlocale()):
        Text.__init__(self, text, 16, locale)
        
class ShortName(Text):
    """Short name text, with maximum length of 8 characters"""
    
    max_length = 8
    
    def __init__(self, text, locale=locale.getdefaultlocale()):
        Text.__init__(self, text, 8, locale)    
        
def suggest_names(names):   
    """Returns a list of names best fitting to the lengths of the original
    strings passed in"""
      
    result = []
    for name in names:
        if len(name) > MediumName.max_length:
            result.append(MediumName(name[0:MediumName.max_length-1]))
            result.append(LongName(name))
        elif len(name) > ShortName.max_length:
            result.append(ShortName(name[0:ShortName.max_length-1]))
            result.append(MediumName(name))
            result.append(LongName(name))
        else:
            result.append(ShortName(name))
            result.append(MediumName(name))
            result.append(LongName(name))            
    return result
        
       
class Membership:
    """The member of a :class:Programme or :class:ProgrammeEvent to a group, references by a
    Short Crid
    
    :param shortcrid: Short Crid
    :type shortcrid: int
    :param crid: Full Crid
    :type crid: Crid
    :param index: Index within the group membership
    :type index: int    
    """
    
    def __init__(self, shortcrid, crid=None, index=None):
        self.shortcrid = shortcrid
        self.crid = crid
        self.index = index 
        
    def __str__(self):
        return str(self.shortcrid)
    
    def __repr__(self):
        return '<Membership: shortcrid=%d, crid=%s, index=%s>' % (self.shortcrid, self.crid, str(self.index))
    
class Multimedia:
    """Link to a multimedia element attached to a :class:Programme or :class:ProgrammeEvent
    
    :param url: URL to the multimedia resource
    :type url: str
    :param type: Type of Multimedia resource
    :type type: str
    :param mimetype: MIME type of the multimedia resource
    :type mimetype: str    
    :param height: height of the multimedia resource in pixels
    :type height: int      
    :param width: width of the multimedia resource in pixels
    :type width: int   
    """
    
    LOGO_UNRESTRICTED ="logo_unrestricted"    
    LOGO_MONO_SQUARE = "logo_mono_square"
    LOGO_COLOUR_SQUARE = "logo_colour_square"
    LOGO_MONO_RECTANGLE = "logo_mono_rectangle"
    LOGO_COLOUR_RECTANGLE = "logo_colour_rectangle"
    
    def __init__(self, url, type=LOGO_UNRESTRICTED, mimetype=None, height=None, width=None, locale=locale.getdefaultlocale()):
        self.url = url
        self.type = type
        self.mimetype = mimetype
        self.height = height
        self.width = width
        if type == Multimedia.LOGO_UNRESTRICTED and (not height or not width):
            raise ValueError('an unrestricted logo must have both height and width defined') 
        elif type != Multimedia.LOGO_UNRESTRICTED and (height or width):
            raise ValueError('should not specify width or height when type is restricted')    
        
class Programme:
    """Describes and locates a programme.
    
    :param shortcrid: Short Crid
    :type shortcrid: int    
    :param crid: Full Crid
    :type crid: str  
    :param bitrate: Where the programme differs from the default service bitrate, this indicates the highgest bitrate
    that the programme can broadcast at, in kHz.
    :type bitrate: int   
    :param onair: True to signal this programme as being broadcast on-air
    :type onair: bool   
    :param onair: True to flag as a recommended programme
    :type onair: bool  
    :param version: Programme metadata version
    :type version: int
    """   
    
    def __init__(self, shortcrid, crid=None, bitrate=None, onair=True, recommendation=True, version=1):
        self.shortcrid = shortcrid
        self.crid = crid
        self.version = version
        self.bitrate = bitrate
        self.onair = onair
        self.recommendation = recommendation
        self.names = []
        self.locations = []
        self.media = []
        self.genres = []
        self.keywords = []
        self.memberships = []
        self.links = []
        self.events = []
        
    def get_name(self, max_length=LongName.max_length):
        """returns the first name set with a length at or below the max_length field, which 
           defaults to the MAX_LENGTH of a LongName field"""
        for type in [LongName, MediumName, ShortName]:
            for name in [x for x in self.names if isinstance(x, type)]:
                if len(name.text) <= max_length: return name
                
    def get_description(self, max_length=LongDescription.max_length):
        """returns the first description set with a length at or below the max_length field, which 
           defaults to the MAX_LENGTH of a LongDescription field"""
        for type in [LongDescription, ShortDescription]:
            for description in [x for x in self.media if isinstance(x, type)]:
                if len(description.text) <= max_length: return description        
                
    def get_times(self):
        """returns a list of (datetime, timedelta) tuples collated from the billed times of the locations
           of this programme"""
        times = []
        for location in self.locations:
            times.extend([(x.get_billed_time(), x.get_billed_duration()) for x in location.times])
        return times
        
    def __str__(self):
        return str(self.get_name())
    
    def __repr__(self):
        return '<Programme: %s>' % str(self)    
    
    
class ProgrammeEvent:
    """Describes and locates a programme event
    
    :param shortcrid: Short Crid
    :type shortcrid: int    
    :param crid: Full Crid
    :type crid: str  
    :param bitrate: Where the programme event differs from the default service bitrate, this indicates the highgest bitrate
    that the programme can broadcast at, in kHz.
    :type bitrate: int   
    :param onair: True to signal this programme event as being broadcast on-air
    :type onair: bool   
    :param onair: True to flag as a recommended programme event
    :type onair: bool  
    :param version: Programme event metadata version
    :type version: int
    """       
    
    def __init__(self, shortcrid, originator=None, crid=None, version=None, bitrate=None, onair=True, recommendation=False):
        self.shortcrid = shortcrid
        self.originator = originator
        self.crid = crid
        self.version = version
        self.bitrate = bitrate
        self.onair = onair
        self.recommendation = recommendation
        self.names = []
        self.locations = []
        self.media = []
        self.genres = []
        self.keywords = []
        self.memberships = []
        self.links = []
        
    def __str__(self):
        return str(self.names)
    
    def __repr__(self):
        return '<ProgrammeEvent: %s>' % str(self)
    
    
class Schedule:
    """Contains programmes within a given time period."""
    
    def __init__(self, created=datetime.datetime.now(tzlocal()), version=1, originator=None):
        self.created = created
        self.version = version
        self.originator = originator
        self.programmes = []
        
    def get_scope(self):
        """Returns the suggested scope of the schedule, taken as an aggregate of the bearers
        and times in the locations of each programme"""
        
        start = None
        end = None
        services = []
        
        for programme in self.programmes:
            for location in programme.locations:
                for time in location.times:
                    if isinstance(time, RelativeTime): continue
                    if start is None or start > time.billed_time:
                        start = time.billed_time
                    if end is None or end < time.billed_time + time.billed_duration:
                        end = time.billed_time + time.billed_duration
                for bearer in location.bearers:
                    if isinstance(bearer, Bearer) and bearer.id not in services:
                        services.append(bearer.id) # we have a Bearer
                    elif isinstance(bearer, ContentId) and bearer not in services:
                        services.append(bearer) # we have a ContentId
                    
        if start is None or end is None: return None    
    
        return Scope(start, end, services)
        
        
class Scope:
    """Contains the times and periods covered by this schedule"""
    
    def __init__(self, start, end, services = []):
        self.start = start
        self.end = end
        self.services = services

    def __str__(self):
        return 'start=%s, end=%s, services=%s>' % (self.start, self.end, self.services)
    
    def __repr__(self):
        return '<Scope: %s>' % str(self)

                
class Service:
    """DAB Service details

    :param id: primary Service ID
    :type id: ContentId    
    :param bitrate: An indication of the highest bitrate of the service.
    :type bitrate: int   
    """
    
    PRIMARY = "primary"
    SECONDARY = "secondary"
    
    AUDIO = "audio"
    DLS = "DLS"
    SLIDESHOW = "MOTSlideshow"
    BWS = "MOTBWS"
    TPEG = "TPEG"
    DGPS = "DGPS"
    PROPRIETARY = "proprietary"
    
    def __init__(self, id, bitrate=None, type=PRIMARY, format=AUDIO, version=1, locale=locale.getdefaultlocale()):
        self.ids = [id]
        self.bitrate = bitrate
        self.type = type
        self.format = format
        self.version = version
        self.locale = locale
        self.names = []
        self.media = []
        self.genres = []
        self.links = []
        self.simulcasts = []
        self.keywords = []
        
    def get_name(self, max_length=LongName.max_length):
        """returns the first name set with a length at or below the max_length field, which 
           defaults to the MAX_LENGTH of a LongName field"""
        for type in [LongName, MediumName, ShortName]:
            for name in [x for x in self.names if isinstance(x, type)]:
                if len(name.text) <= max_length: return name        
        
        
class ServiceInfo:
    """Top-level Service Information document object"""
    
    DAB='DAB'
    DRM='DRM'
    
    def __init__(self, created=None, version=1, originator=None, provider=None, type=DAB):
        self.created = created
        self.version = version
        self.originator = originator
        self.provider = provider
        self.type = type
        self.ensembles = []
        
         
class Genre:
    """Indicates the genre of a programme, group or service. The genre scheme is based on that used by the 
    TV-Anytime specification.
    
    :param href: Genre URI
    :type href: str  
    """
    
    def __init__(self, href, name=None):
        self.href = href
        self.name = name     
        
    def __str__(self):
        return str(self.href)
    
    def __repr__(self):
        return '<Genre: %s>' % str(self)    
