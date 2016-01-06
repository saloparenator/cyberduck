import sqlite3

import base

_init_sql = open('sqlite3/fsm.sql').read()

#example
#from https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Turnstile_state_machine_colored.svg/330px-Turnstile_state_machine_colored.svg.png
_test_sql = """
INSERT INTO context(id,name)                                      VALUES(1,'turnstileA');
INSERT INTO event(id,name)                                        VALUES(1,'push');
INSERT INTO event(id,name)                                        VALUES(2,'coin');
INSERT INTO fsm_state(id,name)                                    VALUES(1,'locked');
INSERT INTO fsm_state(id,name)                                    VALUES(2,'unlocked');
INSERT INTO fsm_machine(id,name,first_state_id)                   VALUES(1,'turnstile',1);
INSERT INTO fsm_transition                                        VALUES(1,1,1,1,1);
INSERT INTO fsm_transition                                        VALUES(2,1,2,1,2);
INSERT INTO fsm_transition                                        VALUES(3,1,1,2,1);
INSERT INTO fsm_transition                                        VALUES(4,1,2,2,2);
INSERT INTO action (id,last_action_id,event_id,context_id)        VALUES(1,0,1,1);
INSERT INTO fsm_instance (id,name,machine_id,state_id,last_action_id) VALUES(1,'turnstileA',1,1,0);
"""
_test_json = {
        'name' : "turnstile",
        'type' : "fsm",
        'begin' : "locked",
        'state' : [
                "locked",
                "unlocked"
        ],
        'transition' : [
                {
                        'event' : "push",
                        'from' : "locked",
                        'next' : "locked"
                },
                {
                        'event' : "coin",
                        'from' : "locked",
                        'next' : "unlocked"
                },
                {
                        'event' : "push",
                        'from' : "unlocked",
                        'next' : "locked"
                },
                {
                        'event' : "coin",
                        'from' : "unlocked",
                        'next' : "unlocked"
                }
        ]
}

def InitDatabase(conn):
    '''
    >>> conn = sqlite3.connect(':memory:')
    >>> conn = base.InitDatabase(conn)
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
    '''
    if not conn:
        conn = sqlite3.connect(':memory:')
    c = conn.executescript(_init_sql)
    conn.commit()
    return conn

def NewInstance(conn,MachineName,InstanceName=None):
    cur = conn.cursor()
    if not InstanceName:
        cur.execute("""
                INSERT INTO fsm_instance(name,machine_id,last_action_id,state_id)
                SELECT name,machine_id,last_action_id,state_id
                FROM fsm_init_view_instance
                WHERE machine_name = '%s'
        """ % MachineName)
    else:
        cur.execute("""
                INSERT INTO fsm_instance(name,machine_id,last_action_id,state_id)
                SELECT '%s',machine_id,last_action_id,state_id
                FROM fsm_init_view_instance
                WHERE machine_name = '%s'
        """ % (InstanceName,MachineName))

    conn.commit()
    return conn

def BuildMachine(conn,FSM):
    """
    >>> conn = sqlite3.connect(':memory:')
    >>> conn = base.InitDatabase(conn)
    >>> conn = InitDatabase(conn)
    >>> conn = BuildMachine(conn,_test_json)
    >>> conn.commit()
    >>> cur = conn.cursor()
    """
    cur = conn.cursor()
    for state in FSM['state']:
        cur.execute("INSERT INTO fsm_state(name) VALUES('%s')" % state)
    cur.execute("INSERT INTO fsm_machine(name,first_state_id) SELECT '%s',id FROM fsm_state WHERE name='%s'" %
                (FSM['name'],FSM['begin']))
    for transition in FSM['transition']:
        cur.execute(""" INSERT INTO fsm_transition (event_id,from_state_id,next_state_id,machine_id)
                        SELECT event.id, from_state.id, next_state.id, fsm_machine.id
                        FROM fsm_state AS from_state, fsm_state AS next_state, event, fsm_machine
                        WHERE from_state.name='%s'
                        AND next_state.name='%s'
                        AND event.name='%s'
                        AND fsm_machine.name='%s'""" %
                        (transition['from'],transition['next'],transition['event'],FSM['name']))
    return conn



if __name__ == '__main__':
    import doctest
    doctest.testmod()
