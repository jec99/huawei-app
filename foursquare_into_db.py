from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger, Float, String, \
	DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import scoped_session, sessionmaker
from geoalchemy2 import Geometry
import re
from datetime import datetime
from models import Base

engine = create_engine('postgresql://localhost/dc', convert_unicode=True)
db_session = scoped_session(sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=engine
))

class Checkin(Base):
	__tablename__ = 'checkins'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer)
	date = Column(DateTime)
	geom = Column(Geometry(geometry_type='POINT', srid=4326))

Base.metadata.create_all(bind=engine)

data_base = '/Users/julienclancy/Desktop/RIPS_2015/databases/foursquare/all/umn/'

# make it faster if it only chooses ones in dc
ll = [-77.6266, 38.5127]
ur = [-75.9595, 39.6512]

# parse venues into hash table of id: latlong

def parse_venue(ln):
	venues_re = re.compile('\s*(\d+)\s+[|]\s+(-?\d{1,2}[.]?\d*)\s+[|]\s+(-?\d{1,3}[.]?\d*).*')
	id, lat, lng = venues_re.match(ln).groups()
	return int(id), float(lat), float(lng)

def parse_checkin(ln):
	checkins_re = re.compile('\s*\d+\s+[|]\s+(\d+)\s+[|]\s+(\d+)\s+[|]\s+' +
		'(-?\d{1,2}[.]?\d*)?\s+[|]\s+' + '(-?\d{1,3}[.]?\d*)?\s+[|]\s+' +
		'([0-9-: ]*)')
	uid, vid, lat, lng, dt = checkins_re.match(ln).groups()
	# those and/or return value hacks
	return (int(uid), int(vid), lat and float(lat), lng and float(lng),
		datetime.strptime(dt, '%Y-%m-%d %H:%M:%S'))

venues = {}
with open(data_base + 'venues.dat') as f:
	for line in f:
		try:
			id, lat, lng = parse_venue(line)
		except:
			# most likely one of the filler lines
			print 'line: \'', line, '\''
			continue
		if ll[0] < lng < ur[0] and ll[1] < lat < ur[1]:
			# note [x, y] not [y, x]
			venues[id] = [lng, lat]

checkins = []
with open(data_base + 'checkins.dat') as f:
	for line in f:
		try:
			uid, vid, lat, lng, dt = parse_checkin(line)
		except:
			# likewise
			print line
			continue
		if vid in venues:
			lng_tmp = venues[vid][0]
			lat_tmp = venues[vid][1]
		elif lat and lng:
			if not (ll[0] < lng < ur[0] and ll[1] < lat < ur[1]):
				continue
			else:
				lng_tmp = lat
				lat_tmp = lng
		else:
			continue

		checkins.append({
			'user_id': uid,
			'lng': lng_tmp,
			'lat': lat_tmp,
			'date': dt
		})

for chk in checkins:
	c = Checkin()
	c.user_id = chk['user_id']
	c.date = chk['date']
	c.geom = 'SRID=4326;POINT ({:.8f} {:.8f})'.format(chk['lng'], chk['lat'])
	db_session.add(c)

db_session.commit()





