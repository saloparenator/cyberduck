import sqlite3

_init_sql = open('sqlite3/base.sql').read()

_emit_action_sql = """
    INSERT INTO action (last_action_id, context_id, event_id)
    SELECT last_action_id, context_id, event_id
    FROM view_build_action AS new_action
    WHERE event_name = '%s'
    AND context_name = '%s'
"""

_test_sql = """
INSERT INTO context VALUES(1,'test');
INSERT INTO event VALUES(1,'hello');
INSERT INTO event VALUES(2,'bye');
INSERT INTO event VALUES(3,'foo');
INSERT INTO event VALUES(4,'bar');
INSERT INTO action VALUES(1,0,1,1,'01_first_action');
INSERT INTO action VALUES(2,1,2,1,'02_last_action');
"""

def InitDatabase(conn=None):
    '''
    >>> conn = sqlite3.connect(':memory:')
    >>> conn = InitDatabase(conn)
    >>> cur = conn.executescript(_test_sql)
    >>> conn.commit()
    >>> cur = conn.cursor()

    >>> query = "SELECT * FROM view_action"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    >>> print(result)
    [(1, 0, 1, u'hello', 1, u'test', u'01_first_action'), (2, 1, 2, u'bye', 1, u'test', u'02_last_action')]
    
    >>> query = "SELECT * FROM view_last_action"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    >>> print(result)
    [(2, 1, 2, u'bye', 1, u'test', u'02_last_action')]

    >>> query = "SELECT * FROM view_build_action"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    >>> print(result)
    [(2, 1, 0, u'test', u'begin'), (2, 1, 1, u'test', u'hello'), (2, 1, 2, u'test', u'bye'), (2, 1, 3, u'test', u'foo'), (2, 1, 4, u'test', u'bar')]
    '''
    if not conn:
        conn = sqlite3.connect(':memory:')
    c = conn.executescript(_init_sql)
    conn.commit()
    return conn


def EmitAction(conn, event_name, context_name):
    '''
    >>> conn = sqlite3.connect(':memory:')
    >>> c = conn.executescript(_init_sql)
    >>> c = conn.executescript(_test_sql)
    >>> conn.commit()
    
    >>> conn = EmitAction(conn,'foo','test')
    >>> cur = conn.cursor()

    >>> query = "SELECT last_action_id, event_id, event_name, context_id, context_name FROM view_last_action"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    >>> print(result)
    [(2, 3, u'foo', 1, u'test')]

    >>> query = "SELECT * FROM view_build_action WHERE context_name = 'test'"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    >>> print(result)
    [(3, 1, 0, u'test', u'begin'), (3, 1, 1, u'test', u'hello'), (3, 1, 2, u'test', u'bye'), (3, 1, 3, u'test', u'foo'), (3, 1, 4, u'test', u'bar')]

    '''
    cur = conn.cursor()
    cur.execute(_emit_action_sql % (event_name,context_name))
    conn.commit()
    return conn

if __name__ == '__main__':
    import doctest
    doctest.testmod()
