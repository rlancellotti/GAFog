import sqlite3
import math

''' funione che conta quanti nodi sorgente sono collegati a ciascun nodo fog
    all'interno di un individuo'''
def get_sources_for_fog(individual, length):
    nSrc=[0]*length
    for i in individual:
        nSrc[(i)]+=1
    return nSrc

''' Queste funzioni si connettono al database e prelevano i dati utili per
    utilizzare l'algoritmo genetico'''

def start(dbname):
    conn = sqlite3.connect(dbname)
    conn.create_function("dst", 4, dst)
    print('''connection succeded''')
    return conn

def dst(x1, y1, x2, y2):
    x = x1 - x2
    y = y1 - y2
    dist = math.sqrt(x**2 + y**2)
    return round(dist*1000)

def get_set(conn, request, table):
    c = conn.cursor()
    c.execute("select "+ request + " from "+ table)
    _set = c.fetchall()
    c.close()
    return _set

def get_linkset(conn, request, table1, table2):
    c = conn.cursor()
    c.execute("select "+ request + " from "+ table1 +" cross join "+ table2)
    _set = c.fetchall()
    print(_set)
    c.close()
    return _set

def get_delays(conn, table1, table2):
    c = conn.cursor()
    c.execute("""select s.ID, f.ID, dst(s.Longitudine,s.Latitudine,f.Longitudine,f.Latitudine)
                from """+table1+""" s cross join """+table2+""" f""")
    ritardi_sf = c.fetchall()
    #print(ritardi_sf)
    c.close()
    rv=[]
    for r in ritardi_sf:
        rv.append(list(r))
    return rv

def stop(conn):
    conn.close()
