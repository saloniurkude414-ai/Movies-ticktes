from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, re
from pathlib import Path
from datetime import datetime
app=Flask(__name__); app.secret_key='cinebook-secret'
DB=Path(__file__).resolve().parent/'theatre.db'
MOVIES=[
{'id':1,'title':'Fighter','genre':'Action • Drama','duration':'2h 46m','price':180,'poster':'fighter.svg'},
{'id':2,'title':'Dunki','genre':'Comedy • Drama','duration':'2h 41m','price':160,'poster':'dunki.svg'},
{'id':3,'title':'Salaar','genre':'Action • Thriller','duration':'2h 55m','price':190,'poster':'salaar.svg'},
{'id':4,'title':'Animal','genre':'Action • Crime','duration':'3h 24m','price':170,'poster':'animal.svg'},
{'id':5,'title':'Interstellar','genre':'Sci-Fi • Drama','duration':'2h 49m','price':200,'poster':'interstellar.svg'},
{'id':6,'title':'3 Idiots','genre':'Comedy • Drama','duration':'2h 50m','price':140,'poster':'three_idiots.svg'}]
SHOWS=[
{'id':1,'movie_id':1,'date':'2026-09-15','time':'10:00 AM','screen':'Screen 1'},{'id':2,'movie_id':1,'date':'2026-09-15','time':'06:30 PM','screen':'Screen 1'},
{'id':3,'movie_id':2,'date':'2026-09-16','time':'01:00 PM','screen':'Screen 2'},{'id':4,'movie_id':2,'date':'2026-09-16','time':'08:00 PM','screen':'Screen 2'},
{'id':5,'movie_id':3,'date':'2026-09-17','time':'11:00 AM','screen':'Screen 3'},{'id':6,'movie_id':3,'date':'2026-09-17','time':'07:00 PM','screen':'Screen 3'},
{'id':7,'movie_id':4,'date':'2026-09-18','time':'04:00 PM','screen':'Screen 1'},{'id':8,'movie_id':4,'date':'2026-09-18','time':'09:00 PM','screen':'Screen 1'},
{'id':9,'movie_id':5,'date':'2026-09-19','time':'12:30 PM','screen':'Screen 2'},{'id':10,'movie_id':5,'date':'2026-09-19','time':'07:30 PM','screen':'Screen 2'},
{'id':11,'movie_id':6,'date':'2026-09-20','time':'03:00 PM','screen':'Screen 1'},{'id':12,'movie_id':6,'date':'2026-09-20','time':'08:30 PM','screen':'Screen 1'}]
SEATS=[f'{r}{n}' for r in 'ABCDEF' for n in range(1,11)]
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
 c=db(); c.execute('''CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY AUTOINCREMENT,booking_code TEXT UNIQUE,show_id INTEGER,customer_name TEXT,email TEXT,seats TEXT,total INTEGER,created_at TEXT)'''); c.commit(); c.close()
def movie(i): return next((m for m in MOVIES if m['id']==i),None)
def show(i): return next((s for s in SHOWS if s['id']==i),None)
def booked(i):
 c=db(); rows=c.execute('SELECT seats FROM bookings WHERE show_id=?',(i,)).fetchall(); c.close(); out=set()
 for r in rows: out.update(x.strip() for x in r['seats'].split(','))
 return out
@app.route('/')
def home():
 ms=[]
 for m in MOVIES:
  x=dict(m); x['shows']=[s for s in SHOWS if s['movie_id']==m['id']]; ms.append(x)
 return render_template('index.html',movies=ms)
@app.route('/book/<int:sid>',methods=['GET','POST'])
def book(sid):
 s=show(sid)
 if not s: flash('Show not found','error'); return redirect(url_for('home'))
 m=movie(s['movie_id']); taken=booked(sid)
 if request.method=='POST':
  name=request.form.get('name','').strip(); email=request.form.get('email','').strip(); chosen=[x.strip() for x in request.form.get('seats','').split(',') if x.strip()]
  if not name: flash('Please enter your full name.','error')
  elif not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',email): flash('Please enter a valid email address.','error')
  elif not chosen: flash('Please select at least one seat.','error')
  elif any(x not in SEATS for x in chosen): flash('Invalid seat selected.','error')
  elif len(chosen)!=len(set(chosen)): flash('Duplicate seat selected.','error')
  elif taken.intersection(chosen): flash('One or more selected seats are already booked.','error')
  else:
   code='CB'+datetime.now().strftime('%y%m%d%H%M%S%f')[-15:]; total=len(chosen)*m['price']; c=db()
   c.execute('INSERT INTO bookings(booking_code,show_id,customer_name,email,seats,total,created_at) VALUES(?,?,?,?,?,?,?)',(code,sid,name,email,', '.join(chosen),total,datetime.now().strftime('%Y-%m-%d %H:%M:%S'))); c.commit(); c.close()
   return redirect(url_for('ticket',code=code))
 return render_template('book.html',movie=m,show=s,booked=taken)
@app.route('/ticket/<code>')
def ticket(code):
 c=db(); b=c.execute('SELECT * FROM bookings WHERE booking_code=?',(code,)).fetchone(); c.close()
 if not b: flash('Ticket not found','error'); return redirect(url_for('home'))
 s=show(b['show_id']); return render_template('ticket.html',booking=b,show=s,movie=movie(s['movie_id']))
@app.route('/cancel',methods=['GET','POST'])
def cancel():
 if request.method=='POST':
  code=request.form.get('booking_code','').strip(); c=db(); b=c.execute('SELECT id FROM bookings WHERE booking_code=?',(code,)).fetchone()
  if not b: c.close(); flash('Booking ID not found.','error'); return redirect(url_for('cancel'))
  c.execute('DELETE FROM bookings WHERE booking_code=?',(code,)); c.commit(); c.close(); flash('Booking cancelled successfully. Seats are available again.','success'); return redirect(url_for('home'))
 return render_template('cancel.html')
init()
if __name__=='__main__':
 print('CINEBOOK: http://127.0.0.1:5000'); app.run(host='127.0.0.1',port=5000,debug=True)
