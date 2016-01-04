import sqlite3

_init_sql = open('base.sql').read()

def InitDatabase(conn):
    '''
    >>> conn = sqlite3.connect(':memory:')
    >>> c = conn.executescript(_init_sql)
    >>> c = conn.executescript(_test_sql)
    >>> conn.commit()
    >>> cur = conn.cursor()

    >>> query = "SELECT * FROM fsm_init_view_instance WHERE machine_name='turnstile'"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    >>> for _id,_name,_machine_id,_last_action_id,_state_id,_ in result:
    ...     if not _id == None:          print('id should be 1 but was %s'                % _id)
    ...     if not 'began:' in _name:    print('_name should contain "began:" but was %s' % _name)
    ...     if not _machine_id == 1:     print('_machine_id should be 1 but was %s'       % _machine_id)
    ...     if not _last_action_id == 0: print('_last_action_id should be 0 but was %s'   % _last_action_id)
    ...     if not _state_id == 1:       print('_state_id should be 1 but was %s'         % _state_id)

    >>> query = "SELECT * FROM fsm_turn_view_instance"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    >>> print(result)
    [(1, u'turnstileA', 1, 1, 1)]

    >>> query = "SELECT * FROM fsm_view_instance"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    '''
    if not conn:
        conn = sqlite3.connect(':memory:')
    c = conn.executescript(_init_sql)
    conn.commit()
    return conn